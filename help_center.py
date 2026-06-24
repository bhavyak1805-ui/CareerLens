import datetime
import streamlit as st
from db  import get_conn
from nav import back_to_dashboard

FAQS = [
    ("How do I complete my profile?",
     "Go to the Dashboard and click your avatar (top-right) to open your profile panel, "
     "then hit ✏️ Edit. This reopens onboarding so you can update any section — personal "
     "info, education, experience, projects, certifications, or achievements."),

    ("How does Face ID login work?",
     "During registration, choose 'face_id' or 'both' as your login method and capture a "
     "clear, front-facing photo. To log in afterward, select the Face ID tab and take a new "
     "photo — it's compared against your stored face data using a similarity score, and you "
     "need at least 70% similarity to be matched."),

    ("Why does Face ID say 'no face detected'?",
     "This usually means the camera couldn't clearly find a face in the frame. Make sure "
     "you're in good lighting, facing the camera directly, and not too far away or partially "
     "out of frame, then try capturing the photo again."),

    ("Where do job recommendations come from?",
     "The Job Recommendations module pulls live listings from Adzuna and ranks them against "
     "the skills and tools you enter using TF-IDF text matching, so listings that mention your "
     "exact skills rank higher. It also shows a skill-gap breakdown so you know what to learn "
     "next."),

    ("Who is Aria, the chatbot?",
     "Aria is an AI career assistant built into the Chatbot module. Ask it about jobs, "
     "internships, or general career questions, and it can recommend specific opportunities "
     "inline. Your chat history is saved per-account so you can pick up old conversations."),

    ("What is the CSVTU Portal module?",
     "It's a placement-portal simulation for CSVTU students — log in with your university ID "
     "to see companies visiting for your branch, apply to listings, and run a skill-gap check "
     "against each company's requirements."),

    ("Is my data secure?",
     "Passwords are hashed before storage and face data is stored as numeric embeddings, not "
     "raw images, for login matching. As with any platform, avoid reusing sensitive passwords "
     "and only use this on trusted networks."),

    ("I found a bug or something isn't working — what do I do?",
     "Use the support form below to describe what happened, including which page/module you "
     "were on and what you expected to happen instead. Your message is saved so it can be "
     "reviewed."),
]


def _ensure_table(conn):
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS support_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            subject VARCHAR(150) NOT NULL,
            message TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            created_at DATETIME NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    conn.commit()


def _save_support_message(user_id, subject, message):
    conn = get_conn()
    _ensure_table(conn)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO support_messages (user_id, subject, message, created_at) VALUES (%s,%s,%s,%s)",
        (user_id, subject, message, datetime.datetime.now()),
    )
    conn.commit()
    conn.close()


def _fetch_my_messages(user_id):
    conn = get_conn()
    _ensure_table(conn)
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT subject, message, status, created_at FROM support_messages "
        "WHERE user_id=%s ORDER BY created_at DESC", (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def render_help_center():
    back_to_dashboard()
    user = st.session_state.current_user

    st.markdown("""
    <div class="module-hero">
      <div class="module-hero-tag">Student Help Desk · Support</div>
      <div class="module-hero-title">Help Center 🛟</div>
      <div class="module-hero-sub">Answers to common questions, plus a direct line if you're still stuck.</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-header">Frequently Asked Questions</div></div>',
                unsafe_allow_html=True)
    for question, answer in FAQS:
        with st.expander(question):
            st.write(answer)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-header">Still need help? Send us a message</div>',
                unsafe_allow_html=True)
    subject = st.text_input("Subject", placeholder="e.g. Face ID won't recognise me", key="hc_subject")
    message = st.text_area("Describe the issue", placeholder="What happened, and what did you expect instead?",
                            height=130, key="hc_message")
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
    if st.button("📨  Submit Message", key="hc_submit"):
        if not subject.strip() or not message.strip():
            st.error("❌ Please fill in both the subject and message.")
        else:
            try:
                _save_support_message(user["user_id"], subject.strip(), message.strip())
                st.success("✅ Message sent! We'll review it soon.")
            except Exception as ex:
                st.error(f"❌ Couldn't save your message: {ex}")
    st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    try:
        my_msgs = _fetch_my_messages(user["user_id"])
    except Exception:
        my_msgs = []

    if my_msgs:
        st.markdown('<div class="card"><div class="card-header">Your Past Messages</div>', unsafe_allow_html=True)
        for m in my_msgs:
            status_cls = "badge green" if m["status"] == "resolved" else "badge orange"
            st.markdown(f"""
            <div class="detail-card" style="margin-bottom:0.6rem;">
              <div class="detail-top">
                <div>
                  <div class="detail-title">{m['subject']}</div>
                  <div class="detail-sub">{m['message'][:140]}{'…' if len(m['message'])>140 else ''}</div>
                </div>
                <span class="{status_cls}">{m['status'].title()}</span>
              </div>
              <div class="detail-meta">{str(m['created_at'])[:16]}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)