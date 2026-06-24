import os
import datetime
import re

import streamlit as st
from groq import Groq
from mysql.connector import Error as MySQLError

from db  import get_conn
from nav import back_to_dashboard

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are "Aria", a friendly campus career-services assistant inside the
Futureconx student platform. Your job: recommend jobs, internships, projects, and career
next-steps to students, and answer their study/career questions clearly and concisely.

Formatting rule: whenever you recommend a specific job, internship, or project opportunity,
wrap EACH recommendation in its own block exactly like this, with nothing else on those lines:
[[JOB]]
TITLE: <role title>
TAG: <one or two word category, e.g. Internship, Remote, Part-time, Research>
WHY: <one sentence on why it fits the student>
[[/JOB]]
You can include 1-4 of these blocks per answer when relevant, plus normal prose before/after.
If the student asks something general (not a job request), just answer normally in plain text,
no job blocks. Keep answers warm, practical, and not overly long."""

SUGGESTIONS = [
    "Suggest internships for a 2nd-year CS student",
    "What jobs fit someone who likes design + writing?",
    "Help me find part-time remote work",
    "How do I write a resume bullet for a class project?",
]

def _ensure_table(conn):
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS chatbot_questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL, chat_id VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL, content TEXT NOT NULL,
            asked_at DATETIME NOT NULL,
            INDEX idx_user_chat (user_id, chat_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    conn.commit()

def get_chat_db_connection():
    try:
        conn = get_conn(); _ensure_table(conn); return conn
    except Exception as e:
        st.session_state["_chat_db_error"] = str(e); return None

def log_message(conn, user_id, chat_id, role, content):
    if conn is None: return
    cur = conn.cursor()
    cur.execute("INSERT INTO chatbot_questions (user_id,chat_id,role,content,asked_at) VALUES (%s,%s,%s,%s,%s)",
                (user_id, chat_id, role, content, datetime.datetime.now()))
    conn.commit(); cur.close()

def fetch_user_chats(conn, user_id):
    if conn is None: return []
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT chat_id,role,content,asked_at FROM chatbot_questions WHERE user_id=%s ORDER BY id ASC", (user_id,))
    rows = cur.fetchall(); cur.close()
    chats_by_id = {}; order = []
    for r in rows:
        cid = r["chat_id"]
        if cid not in chats_by_id:
            chats_by_id[cid] = {"id":cid,"title":None,"messages":[]}; order.append(cid)
        chats_by_id[cid]["messages"].append({"role":r["role"],"content":r["content"]})
        if chats_by_id[cid]["title"] is None and r["role"] == "user":
            t = r["content"]
            chats_by_id[cid]["title"] = t[:40]+("…" if len(t)>40 else "")
    return [chats_by_id[cid] for cid in reversed(order)]

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key: return None
    return Groq(api_key=api_key)

def ask_groq(client, messages):
    full_messages = [{"role":"system","content":SYSTEM_PROMPT}] + messages
    response = client.chat.completions.create(model=GROQ_MODEL, messages=full_messages,
                                               temperature=0.6, max_tokens=700)
    return response.choices[0].message.content

def parse_reply(raw):
    parts = []; pattern = re.compile(r"\[\[JOB\]\](.*?)\[\[/JOB\]\]", re.DOTALL); last_end = 0
    for match in pattern.finditer(raw):
        if match.start() > last_end:
            text = raw[last_end:match.start()].strip()
            if text: parts.append({"type":"text","text":text})
        block = match.group(1)
        def ef(f): m=re.search(rf"{f}:\s*(.+)",block); return m.group(1).strip() if m else None
        parts.append({"type":"job","title":ef("TITLE") or "Recommended role",
                      "tag":ef("TAG") or "Opportunity","why":ef("WHY") or ""})
        last_end = match.end()
    if last_end < len(raw):
        text = raw[last_end:].strip()
        if text: parts.append({"type":"text","text":text})
    if not parts: parts.append({"type":"text","text":raw})
    return parts

def render_bot_reply(content):
    for part in parse_reply(content):
        if part["type"] == "job":
            st.markdown(f"""
            <div class="job-card">
                <span class="job-card-tag">{part['tag']}</span>
                <div class="job-card-title">{part['title']}</div>
                <p class="job-card-why">{part['why']}</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.write(part["text"])

def handle_new_message(prompt, conn, client, user_id):
    if st.session_state.chatbot_active_chat_id is None:
        chat_id = f"chat_{user_id}_{datetime.datetime.now().timestamp()}"
        title   = prompt[:40]+("…" if len(prompt)>40 else "")
        st.session_state.chatbot_chats.insert(0, {"id":chat_id,"title":title,"messages":[]})
        st.session_state.chatbot_active_chat_id = chat_id
    active_chat = next(c for c in st.session_state.chatbot_chats
                       if c["id"] == st.session_state.chatbot_active_chat_id)
    active_chat["messages"].append({"role":"user","content":prompt})
    log_message(conn, user_id, active_chat["id"], "user", prompt)
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        if client is None:
            reply = "I can't reach Aria right now — GROQ_API_KEY isn't set."; st.write(reply)
        else:
            with st.spinner("Aria is thinking…"):
                try:
                    history = [{"role":m["role"],"content":m["content"]} for m in active_chat["messages"]]
                    reply   = ask_groq(client, history)
                except Exception as e:
                    reply = f"Something went wrong: {e}"
            render_bot_reply(reply)
    active_chat["messages"].append({"role":"assistant","content":reply})
    log_message(conn, user_id, active_chat["id"], "assistant", reply)
    st.rerun()

def render_chatbot():
    back_to_dashboard()

    user    = st.session_state.current_user
    user_id = user["user_id"]
    conn    = get_chat_db_connection()
    client  = get_groq_client()

    if "chatbot_chats" not in st.session_state:
        st.session_state.chatbot_chats = fetch_user_chats(conn, user_id) if conn else []
    if "chatbot_active_chat_id" not in st.session_state:
        st.session_state.chatbot_active_chat_id = None

    # Chat history + status, now in an expander instead of the sidebar
    with st.expander("🗂️  Chat History", expanded=False):
        if st.button("＋ New chat", key="chat_new"):
            st.session_state.chatbot_active_chat_id = None; st.rerun()

        if not st.session_state.chatbot_chats:
            st.caption("No chats yet.")
        else:
            for chat in st.session_state.chatbot_chats:
                if st.button(chat["title"] or "Untitled chat", key=f"chathist_{chat['id']}"):
                    st.session_state.chatbot_active_chat_id = chat["id"]; st.rerun()

        pill_cls = "badge green" if client else "badge red"
        pill_txt = "✓ Aria is online" if client else "⚠ GROQ_API_KEY not set"
        st.markdown(f'<span class="{pill_cls}">{pill_txt}</span>', unsafe_allow_html=True)

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="module-hero">
      <div class="module-hero-tag">Student Help Desk · AI Assistant</div>
      <div class="module-hero-title">Ask Aria Anything 🤖</div>
      <div class="module-hero-sub">Jobs, internships, career questions — Aria recommends roles tailored to you.</div>
    </div>""", unsafe_allow_html=True)

    active_chat = next(
        (c for c in st.session_state.chatbot_chats
         if c["id"] == st.session_state.chatbot_active_chat_id), None)

    if active_chat is None:
        first_name = (user.get("full_name") or "there").split()[0]
        st.markdown(f"""
        <div style="text-align:center;padding:1rem 0 1.5rem;">
          <div style="font-size:1.3rem;font-weight:700;color:var(--text);margin-bottom:0.3rem;">
            Hey {first_name}, what are you looking for today?
          </div>
          <div style="font-size:0.85rem;color:var(--t2);">Pick a suggestion or type below</div>
        </div>""", unsafe_allow_html=True)
        cols = st.columns(2)
        clicked = None
        for i, s in enumerate(SUGGESTIONS):
            if cols[i%2].button(s, key=f"chat_sugg_{i}"): clicked = s
        prompt = st.chat_input("Ask about jobs, internships, or your career…")
        if clicked: prompt = clicked
    else:
        for msg in active_chat["messages"]:
            with st.chat_message("user" if msg["role"]=="user" else "assistant"):
                if msg["role"] == "user": st.write(msg["content"])
                else: render_bot_reply(msg["content"])
        prompt = st.chat_input("Ask about jobs, internships, or your career…")

    if prompt:
        handle_new_message(prompt, conn, client, user_id)