#from dotenv import load_dotenv
#load_dotenv()
import streamlit as st
import mysql.connector
import json
import time

from styles      import GLOBAL_CSS
from db          import get_conn, test_conn, load_full_profile
from auth        import (hash_pw, check_pw, log_login,
                         camera_to_array, save_face_image,
                         extract_embedding, cosine_sim, faces_match)
from onboarding  import render_onboarding
from dashboard   import render_dashboard
from chatbot     import render_chatbot
from job_rec     import render_job_recommendations
from csvtu       import render_csvtu
from applications import render_applications
from help_center import render_help_center

for k, v in [("db_config", {"host":"localhost","port":"3306","user":"root",
                              "password":"bk123@","database":"faceauth"}),
             ("logged_in", False), ("current_user", None),
             ("profile", {"loaded":False}), ("active_module", None),
             ("onboarding_step", 1), ("reg_embedding", None)]:
    if k not in st.session_state: st.session_state[k] = v

# Sidebar auto-expanded only on the Dashboard (active_module is None); collapsed in every module
_sidebar_state = "expanded" if st.session_state.active_module is None else "collapsed"
st.set_page_config(page_title="Student Help Desk", page_icon="🎓",
                   layout="wide", initial_sidebar_state=_sidebar_state)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if st.session_state.logged_in:
    user = st.session_state.current_user
    if not st.session_state.profile.get("loaded"):
        load_full_profile(user["user_id"])
    if not bool(user.get("profile_completed")):
        render_onboarding(); st.stop()
    module = st.session_state.active_module
    if   module == "applications": render_applications()
    elif module == "chatbot":  render_chatbot()
    elif module == "job_rec":  render_job_recommendations()
    elif module == "csvtu":    render_csvtu()
    elif module == "help":     render_help_center()
    else:                      render_dashboard()
    st.stop()

# ── AUTH PAGES ────────────────────────────────────────────────────────────────
_AUTH_ILLUSTRATION = """<svg width="100%" viewBox="0 0 520 480" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="blob" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#dbeafe"/>
      <stop offset="100%" stop-color="#c7d2fe"/>
    </linearGradient>
  </defs>
  <ellipse cx="260" cy="250" rx="225" ry="205" fill="url(#blob)" opacity="0.55"/>
  <circle cx="110" cy="78" r="30" fill="#93c5fd" opacity="0.55"/>
  <circle cx="438" cy="100" r="15" fill="#6366f1" opacity="0.5"/>
  <circle cx="72" cy="370" r="9" fill="#3b82f6" opacity="0.4"/>
  <circle cx="452" cy="330" r="12" fill="#93c5fd" opacity="0.45"/>
  <rect x="148" y="108" width="244" height="186" rx="14" fill="#ffffff" stroke="#bfdbfe" stroke-width="2"/>
  <rect x="148" y="108" width="244" height="28" rx="14" fill="#3b82f6"/>
  <rect x="148" y="122" width="244" height="14" fill="#3b82f6"/>
  <circle cx="166" cy="122" r="4.5" fill="#ffffff" opacity="0.85"/>
  <circle cx="181" cy="122" r="4.5" fill="#ffffff" opacity="0.6"/>
  <circle cx="196" cy="122" r="4.5" fill="#ffffff" opacity="0.4"/>
  <rect x="164" y="152" width="84" height="7" rx="3.5" fill="#dbeafe"/>
  <rect x="164" y="167" width="64" height="7" rx="3.5" fill="#dbeafe"/>
  <rect x="164" y="182" width="74" height="7" rx="3.5" fill="#dbeafe"/>
  <rect x="164" y="197" width="50" height="7" rx="3.5" fill="#dbeafe"/>
  <circle cx="322" cy="200" r="40" fill="none" stroke="#dbeafe" stroke-width="13"/>
  <path d="M322 160 A40 40 0 0 1 358 218" fill="none" stroke="#3b82f6" stroke-width="13" stroke-linecap="round"/>
  <path d="M358 218 A40 40 0 0 1 322 240" fill="none" stroke="#6366f1" stroke-width="13" stroke-linecap="round"/>
  <rect x="164" y="252" width="46" height="26" rx="6" fill="#eff6ff"/>
  <rect x="217" y="252" width="46" height="26" rx="6" fill="#eff6ff"/>
  <rect x="270" y="252" width="46" height="26" rx="6" fill="#eff6ff"/>
  <rect x="173" y="262" width="10" height="10" rx="2" fill="#93c5fd"/>
  <rect x="226" y="258" width="10" height="14" rx="2" fill="#3b82f6"/>
  <rect x="279" y="265" width="10" height="7" rx="2" fill="#6366f1"/>
  <g>
    <ellipse cx="190" cy="438" rx="42" ry="7" fill="#bfdbfe" opacity="0.4"/>
    <rect x="160" y="394" width="14" height="28" rx="7" fill="#1d4ed8" transform="rotate(-6 167 408)"/>
    <rect x="206" y="394" width="14" height="28" rx="7" fill="#1d4ed8" transform="rotate(10 213 408)"/>
    <path d="M168 438 C168 392 212 392 212 438 Z" fill="#3b82f6"/>
    <rect x="178" y="378" width="24" height="46" rx="10" fill="#1d4ed8"/>
    <circle cx="190" cy="356" r="20" fill="#1e3a8a"/>
    <path d="M170 354 A20 20 0 0 1 210 354 L210 348 A20 16 0 0 0 170 348 Z" fill="#0f1f4d"/>
  </g>
  <g>
    <ellipse cx="340" cy="430" rx="40" ry="7" fill="#c7d2fe" opacity="0.4"/>
    <rect x="312" y="388" width="14" height="26" rx="7" fill="#4338ca" transform="rotate(-10 319 401)"/>
    <rect x="354" y="388" width="14" height="26" rx="7" fill="#4338ca" transform="rotate(8 361 401)"/>
    <path d="M320 430 C320 386 360 386 360 430 Z" fill="#6366f1"/>
    <rect x="328" y="372" width="24" height="44" rx="10" fill="#4338ca"/>
    <circle cx="340" cy="350" r="19" fill="#312e81"/>
    <path d="M321 348 A19 19 0 0 1 359 348 L359 342 A19 15 0 0 0 321 342 Z" fill="#1e1b4b"/>
  </g>
  <rect x="98" y="318" width="50" height="58" rx="8" fill="#ffffff" stroke="#bfdbfe" stroke-width="2"/>
  <rect x="108" y="346" width="7" height="22" rx="2" fill="#93c5fd"/>
  <rect x="119" y="336" width="7" height="32" rx="2" fill="#3b82f6"/>
  <rect x="130" y="354" width="7" height="14" rx="2" fill="#93c5fd"/>
  <line x1="48" y1="436" x2="472" y2="436" stroke="#bfdbfe" stroke-width="2"/>
</svg>"""

st.markdown("""
<style>
div[data-testid="stHorizontalBlock"]:has(.auth-shell-anchor) {
    max-width:1080px; margin:2rem auto 0; background:#ffffff;
    border:2px solid #bfdbfe; border-radius:24px; overflow:hidden;
    box-shadow:0 20px 60px rgba(59,130,246,0.12);
}
div[data-testid="stHorizontalBlock"]:has(.auth-shell-anchor) > div:first-child {
    padding:2.5rem 2.5rem 2rem;
}
div[data-testid="stHorizontalBlock"]:has(.auth-shell-anchor) > div:last-child {
    background:linear-gradient(160deg,#eef2ff,#f0f4ff);
    border-left:1px solid #e4e8f5;
    display:flex; align-items:center; justify-content:center; padding:2rem;
}
.auth-brand { font-size:0.78rem; font-weight:800; letter-spacing:2px;
    color:#3b82f6; text-transform:uppercase; margin-bottom:1.4rem; }
.auth-hero h1 { font-size:2rem; font-weight:800; letter-spacing:-1px;
    margin:0 0 0.35rem; color:#111827; }
.auth-hero p { color:#6b7280; font-size:0.85rem; margin:0 0 0.4rem; }
.stTabs [data-baseweb="tab-panel"] { padding-top:1.25rem !important; }
@media (max-width:900px) {
    div[data-testid="stHorizontalBlock"]:has(.auth-shell-anchor) > div:last-child { display:none; }
}
</style>
""", unsafe_allow_html=True)

auth_left, auth_right = st.columns([1.15, 1], gap="large")

with auth_right:
    st.markdown('<span class="auth-shell-anchor"></span>', unsafe_allow_html=True)
    st.markdown(_AUTH_ILLUSTRATION, unsafe_allow_html=True)

with auth_left:
    st.markdown("""
    <div class="auth-brand">🎓 Student Help Desk</div>
    <div class="auth-hero">
      <h1>Welcome back</h1>
      <p>Log in or create an account to continue to your dashboard.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_reg = st.tabs(["🔑  Login", "📝  Register"])

    with tab_reg:
        st.markdown('<div class="card"><div class="card-header">Create Account</div>', unsafe_allow_html=True)
        r_name  = st.text_input("Full Name",        placeholder="Ada Lovelace",    key="r_name")
        r_email = st.text_input("Email",            placeholder="ada@example.com", key="r_email")
        r_pass  = st.text_input("Password",         type="password",               key="r_pass")
        r_pass2 = st.text_input("Confirm Password", type="password",               key="r_pass2")
        r_auth  = st.selectbox("Login Method",      ["manual","face_id","both"],   key="r_auth")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="divider">Face Registration — Live Camera</div>', unsafe_allow_html=True)
        st.markdown('<div class="cam-hint"><span style="font-size:1.8rem;display:block;margin-bottom:0.4rem;">📸</span>Position your face clearly in the frame, then click <b>Take Photo</b></div>', unsafe_allow_html=True)
        reg_cam  = st.camera_input("", key="reg_cam")
        emb_slot = st.empty()
        if reg_cam:
            with st.spinner("Detecting face..."):
                emb, bk = extract_embedding(camera_to_array(reg_cam))
            if emb:
                st.session_state.reg_embedding = emb
                emb_slot.success(f"✅ Face detected via {bk} — {len(emb)} dims")
            else:
                st.session_state.reg_embedding = None
                emb_slot.error(f"❌ No face detected ({bk})")

        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Create Account 🚀", key="btn_register"):
            errors = []
            if not r_name:  errors.append("Full name required")
            if not r_email: errors.append("Email required")
            if not r_pass:  errors.append("Password required")
            if r_pass != r_pass2: errors.append("Passwords do not match")
            if r_auth in ("face_id","both") and not st.session_state.get("reg_embedding"):
                errors.append("Capture a face photo for Face ID")
            if errors:
                for e in errors: st.error(f"❌ {e}")
            else:
                try:
                    conn = get_conn(); cur = conn.cursor()
                    emb      = st.session_state.reg_embedding
                    emb_json = json.dumps(emb) if emb else None
                    img_path = save_face_image(reg_cam, r_email) if reg_cam else None
                    cur.execute("INSERT INTO users (full_name,email,password_hash,face_embedding,face_image_path,auth_method) VALUES (%s,%s,%s,%s,%s,%s)",
                        (r_name, r_email, hash_pw(r_pass), emb_json, img_path, r_auth))
                    uid = cur.lastrowid
                    if emb:
                        cur.execute("INSERT INTO face_samples (user_id,embedding,image_path) VALUES (%s,%s,%s)", (uid, emb_json, img_path))
                    conn.commit(); conn.close()
                    st.session_state.reg_embedding = None
                    st.success("🎉 Account created! Go to Login."); st.balloons()
                except mysql.connector.IntegrityError:
                    st.error("❌ Email already registered.")
                except Exception as ex:
                    st.error(f"❌ {ex}")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_login:
        mode = st.radio("Method", ["🔑  Password", "🤳  Face ID"], horizontal=True, key="login_mode")
        if mode == "🔑  Password":
            st.markdown('<div class="card"><div class="card-header">Password Login</div>', unsafe_allow_html=True)
            l_email = st.text_input("Email",    placeholder="ada@example.com", key="l_email")
            l_pass  = st.text_input("Password", type="password",               key="l_pass")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Login →", key="btn_login"):
                if not l_email or not l_pass:
                    st.error("❌ Fill all fields.")
                else:
                    try:
                        conn = get_conn(); cur = conn.cursor(dictionary=True)
                        cur.execute("SELECT * FROM users WHERE email=%s", (l_email,))
                        user = cur.fetchone(); conn.close()
                        if not user: st.error("❌ Email not found.")
                        elif not check_pw(l_pass, user["password_hash"]):
                            log_login(user["user_id"],"manual","failed"); st.error("❌ Wrong password.")
                        else:
                            log_login(user["user_id"],"manual","success")
                            st.session_state.logged_in = True
                            st.session_state.current_user = user
                            st.success("✅ Login successful!")
                            time.sleep(0.4); st.rerun()
                    except Exception as ex: st.error(f"❌ {ex}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><div class="card-header">Face ID Login</div>', unsafe_allow_html=True)
            fi_email = st.text_input("Registered Email", placeholder="ada@example.com", key="fi_email")
            st.markdown('<div class="cam-hint" style="margin-top:0.8rem;"><span style="font-size:1.5rem;display:block;">🤳</span>Look straight at the camera and click Take Photo</div>', unsafe_allow_html=True)
            fi_cam = st.camera_input("", key="fi_cam")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Verify Face →", key="btn_face"):
                if not fi_email or not fi_cam:
                    st.error("❌ Email and photo required.")
                else:
                    try:
                        conn = get_conn(); cur = conn.cursor(dictionary=True)
                        cur.execute("SELECT * FROM users WHERE email=%s", (fi_email,))
                        user = cur.fetchone()
                        if not user: st.error("❌ Email not found."); conn.close()
                        elif not user.get("face_embedding"): st.error("❌ No Face ID registered."); conn.close()
                        else:
                            cur.execute("SELECT embedding FROM face_samples WHERE user_id=%s", (user["user_id"],))
                            samples = cur.fetchall(); conn.close()
                            with st.spinner("Verifying face..."):
                                live_emb, bk = extract_embedding(camera_to_array(fi_cam))
                            if not live_emb:
                                log_login(user["user_id"],"face_id","failed"); st.error(f"❌ No face detected ({bk})")
                            else:
                                stored = json.loads(user["face_embedding"])
                                matched = faces_match(live_emb, stored)
                                if not matched:
                                    for s in samples:
                                        if faces_match(live_emb, json.loads(s["embedding"])): matched = True; break
                                sim = cosine_sim(live_emb, stored)
                                if matched:
                                    log_login(user["user_id"],"face_id","success")
                                    st.session_state.logged_in = True
                                    st.session_state.current_user = user
                                    st.success(f"✅ Face verified! Similarity: {sim:.2%}")
                                    time.sleep(0.4); st.rerun()
                                else:
                                    log_login(user["user_id"],"face_id","failed")
                                    st.error(f"❌ Face not recognised. Score: {sim:.2%} (need ≥70%)")
                    except Exception as ex: st.error(f"❌ {ex}")
            st.markdown('</div>', unsafe_allow_html=True)
