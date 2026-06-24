import streamlit as st
from db  import get_conn
from nav import back_to_dashboard


def render_applications():
    user    = st.session_state.current_user
    profile = st.session_state.profile
    name    = user.get("full_name", "Student")
    initials = "".join(p[0].upper() for p in name.split()[:2])

    # ── CSS (mirrors dashboard.py so the module feels native, not bolted-on) ──
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg: #f0f4ff; --surface: #ffffff; --s2: #f7f9ff; --border: #e4e8f5;
    --accent: #3b82f6; --a-light: #dbeafe; --a2: #10b981; --a3: #f59e0b; --a4: #ef4444;
    --text: #111827; --t2: #6b7280; --muted: #9ca3af; --sidebar-w: 230px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; background: var(--bg) !important; color: var(--text) !important; }
.stApp { background: var(--bg) !important; }
.main .block-container { padding: 0 1.5rem 2rem !important; max-width: 100% !important; }

.stButton > button {
    background: transparent !important; color: var(--t2) !important; border: none !important;
    border-radius: 10px !important; font-weight: 500 !important; font-size: 0.85rem !important;
    padding: 0.55rem 0.85rem !important; transition: all 0.15s !important; white-space: nowrap !important;
    width: auto !important; text-align: left !important; justify-content: flex-start !important; box-shadow: none !important;
}
.stButton > button:hover { background: var(--a-light) !important; color: var(--accent) !important; }
.btn-ghost > button { background: transparent !important; color: var(--accent) !important; border: 1px solid var(--border) !important; font-size: 0.78rem !important; padding: 0.38rem 0.8rem !important; border-radius: 8px !important; width: auto !important; }
.btn-ghost > button:hover { background: var(--a-light) !important; }

.panel { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 1.1rem 1.25rem; margin-bottom: 1rem; }
.panel-title { font-size: 0.92rem; font-weight: 700; color: var(--text); margin-bottom: 0.9rem; display:flex; align-items:center; justify-content:space-between; }

.metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.1rem; display: flex; align-items: center; gap: 0.75rem; }
.metric-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0; }
.metric-val { font-size: 1.45rem; font-weight: 800; color: var(--text); line-height: 1; }
.metric-lbl { font-size: 0.68rem; color: var(--muted); font-weight: 500; margin-top: 2px; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.9rem 1.5rem; }
.info-item .info-lbl { font-size: 0.65rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
.info-item .info-val { font-size: 0.85rem; color: var(--text); font-weight: 500; }

.detail-card { border: 1px solid var(--border); border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 0.7rem; background: var(--s2); }
.detail-card:last-child { margin-bottom: 0; }
.detail-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.6rem; }
.detail-title { font-size: 0.85rem; font-weight: 700; color: var(--text); }
.detail-sub { font-size: 0.74rem; color: var(--t2); margin-top: 1px; }
.detail-meta { font-size: 0.68rem; color: var(--muted); margin-top: 4px; }
.detail-desc { font-size: 0.75rem; color: var(--t2); margin-top: 6px; line-height: 1.5; }
.tag { display: inline-block; font-size: 0.64rem; font-weight: 600; background: var(--a-light); color: var(--accent); border-radius: 20px; padding: 2px 9px; margin-top: 6px; margin-right: 5px; }
.badge-pill { font-size: 0.62rem; font-weight: 700; border-radius: 20px; padding: 3px 10px; white-space: nowrap; }
.empty-row { font-size: 0.78rem; color: var(--muted); padding: 0.6rem 0; font-style: italic; }
.link-row a { font-size: 0.72rem; color: var(--accent); text-decoration: none; margin-right: 12px; }

#MainMenu, footer, header { visibility: hidden !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-thumb { background: #c7d2fe; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # BACK BUTTON (replaces full sidebar on module pages)
    # ════════════════════════════════════════════════════════════════════════
    back_to_dashboard()

    # ════════════════════════════════════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════════════════════════════════════
    h1, h2 = st.columns([0.7, 0.3])
    with h1:
        st.markdown(f"""
        <div style="padding:0.7rem 0 0.5rem 0;">
          <div style="font-size:1.3rem;font-weight:800;color:#111827;">📋 My Application Profile</div>
          <div style="font-size:0.72rem;color:#9ca3af;margin-top:2px;">
            Everything you submitted during onboarding, in one place
          </div>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown('<div style="padding-top:1.1rem;text-align:right;">', unsafe_allow_html=True)
        st.markdown('<div class="btn-ghost" style="display:inline-block;">', unsafe_allow_html=True)
        if st.button("✏️ Edit Profile", key="apps_edit_profile"):
            try:
                conn = get_conn(); cur = conn.cursor()
                cur.execute("UPDATE users SET profile_completed=FALSE WHERE user_id=%s", (user["user_id"],))
                conn.commit(); conn.close()
            except Exception:
                pass
            st.session_state.current_user["profile_completed"] = False
            st.session_state.onboarding_step = 1
            st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)

    if not profile.get("loaded"):
        st.info("Profile data isn't loaded yet — please refresh.")
        return

    u     = profile.get("user") or {}
    edu   = profile.get("education") or []
    exp   = profile.get("experience") or []
    proj  = profile.get("projects") or []
    certs = profile.get("certifications") or []
    ach   = profile.get("achievements") or []

    # ════════════════════════════════════════════════════════════════════════
    # QUICK STATS
    # ════════════════════════════════════════════════════════════════════════
    m1, m2, m3, m4 = st.columns(4, gap="small")
    stats = [
        ("🎓", "#dbeafe", "#1d4ed8", len(edu),   "Education Entries"),
        ("💼", "#fef3c7", "#92400e", len(exp),   "Experience Entries"),
        ("🛠️", "#d1fae5", "#065f46", len(proj),  "Projects"),
        ("📜", "#ede9fe", "#5b21b6", len(certs), "Certifications"),
    ]
    for col, (ic, bg, fg, val, lbl) in zip([m1, m2, m3, m4], stats):
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-icon" style="background:{bg};color:{fg};">{ic}</div>
              <div><div class="metric-val">{val}</div><div class="metric-lbl">{lbl}</div></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # PERSONAL INFORMATION
    # ════════════════════════════════════════════════════════════════════════
    def v(key, fallback="—"):
        val = u.get(key)
        return val if val not in (None, "", "None") else fallback

    st.markdown(f"""
    <div class="panel">
      <div class="panel-title">👤 Personal Information</div>
      <div class="info-grid">
        <div class="info-item"><div class="info-lbl">Full Name</div><div class="info-val">{v('full_name', name)}</div></div>
        <div class="info-item"><div class="info-lbl">Email</div><div class="info-val">{v('email')}</div></div>
        <div class="info-item"><div class="info-lbl">Phone</div><div class="info-val">{v('phone')}</div></div>
        <div class="info-item"><div class="info-lbl">Date of Birth</div><div class="info-val">{v('dob')}</div></div>
        <div class="info-item"><div class="info-lbl">Gender</div><div class="info-val">{v('gender')}</div></div>
        <div class="info-item"><div class="info-lbl">Location</div><div class="info-val">{v('city')}{', ' + u.get('state') if u.get('state') else ''}</div></div>
        <div class="info-item"><div class="info-lbl">Target Role</div><div class="info-val">{v('target_role')}</div></div>
        <div class="info-item"><div class="info-lbl">Experience Level</div><div class="info-val">{v('experience_level')}</div></div>
        <div class="info-item"><div class="info-lbl">LinkedIn</div><div class="info-val">{v('linkedin_url')}</div></div>
        <div class="info-item"><div class="info-lbl">GitHub</div><div class="info-val">{v('github_url')}</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # EDUCATION + EXPERIENCE (two columns)
    # ════════════════════════════════════════════════════════════════════════
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        cards = ""
        for e in edu:
            cards += (
                '<div class="detail-card">'
                '<div class="detail-top">'
                '<div>'
                f'<div class="detail-title">{e.get("degree","—")}</div>'
                f'<div class="detail-sub">{e.get("institution","—")}</div>'
                '</div>'
                '<span class="badge-pill" style="background:#dbeafe;color:#1d4ed8;">'
                f'{e.get("year_from","—")}–{e.get("year_to","—")}'
                '</span>'
                '</div>'
                f'<div class="detail-meta">{e.get("score","—")} {e.get("score_type","")}</div>'
                '</div>'
            )
        if not cards:
            cards = '<div class="empty-row">No education entries added yet.</div>'
        st.markdown(f'<div class="panel"><div class="panel-title">🎓 Education</div>{cards}</div>', unsafe_allow_html=True)

    with col_b:
        cards = ""
        for e in exp:
            cards += (
                '<div class="detail-card">'
                '<div class="detail-top">'
                '<div>'
                f'<div class="detail-title">{e.get("role","—")}</div>'
                f'<div class="detail-sub">{e.get("company","—")}</div>'
                '</div>'
                f'<span class="badge-pill" style="background:#fef3c7;color:#92400e;">{e.get("exp_type","—")}</span>'
                '</div>'
                f'<div class="detail-meta">{e.get("duration","—")}</div>'
                '</div>'
            )
        if not cards:
            cards = '<div class="empty-row">No work experience added — that\'s fine for freshers.</div>'
        st.markdown(f'<div class="panel"><div class="panel-title">💼 Experience</div>{cards}</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # PROJECTS
    # ════════════════════════════════════════════════════════════════════════
    cards = ""
    for p in proj:
        links = ""
        if p.get("github_url"):
            links += f'<a href="{p["github_url"]}" target="_blank">🔗 GitHub</a>'
        if p.get("live_url"):
            links += f'<a href="{p["live_url"]}" target="_blank">🌐 Live</a>'
        tech_tags = "".join(
            f'<span class="tag">{t.strip()}</span>'
            for t in (p.get("tech_stack") or "").split(",") if t.strip()
        )
        links_html = f'<div class="link-row" style="margin-top:8px;">{links}</div>' if links else ""
        cards += (
            '<div class="detail-card">'
            f'<div class="detail-title">{p.get("title","—")}</div>'
            f'<div class="detail-desc">{p.get("description","") or "No description provided."}</div>'
            f'{tech_tags}'
            f'{links_html}'
            '</div>'
        )
    if not cards:
        cards = '<div class="empty-row">No projects added yet.</div>'
    st.markdown(f'<div class="panel"><div class="panel-title">🛠️ Projects</div>{cards}</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # CERTIFICATIONS + ACHIEVEMENTS (two columns)
    # ════════════════════════════════════════════════════════════════════════
    col_c, col_d = st.columns(2, gap="medium")

    with col_c:
        cards = ""
        for c in certs:
            extra = ""
            if c.get("credential_id"):
                extra += f'<div class="detail-meta">ID: {c["credential_id"]}</div>'
            if c.get("verify_url"):
                extra += f'<div class="link-row" style="margin-top:4px;"><a href="{c["verify_url"]}" target="_blank">✅ Verify</a></div>'
            cards += (
                '<div class="detail-card">'
                '<div class="detail-top">'
                '<div>'
                f'<div class="detail-title">{c.get("name","—")}</div>'
                f'<div class="detail-sub">{c.get("issuer","—")}</div>'
                '</div>'
                f'<span class="badge-pill" style="background:#ede9fe;color:#5b21b6;">{c.get("issue_year") or c.get("year","—")}</span>'
                '</div>'
                f'{extra}'
                '</div>'
            )
        if not cards:
            cards = '<div class="empty-row">No certifications added yet.</div>'
        st.markdown(f'<div class="panel"><div class="panel-title">📜 Certifications</div>{cards}</div>', unsafe_allow_html=True)

    with col_d:
        cards = ""
        for a in ach:
            desc_html = f'<div class="detail-desc">{a["description"]}</div>' if a.get("description") else ""
            cards += (
                '<div class="detail-card">'
                '<div class="detail-top">'
                f'<div class="detail-title">{a.get("title","—")}</div>'
                f'<span class="badge-pill" style="background:#dcfce7;color:#166534;">{a.get("year","—")}</span>'
                '</div>'
                f'{desc_html}'
                '</div>'
            )
        if not cards:
            cards = '<div class="empty-row">No achievements added yet.</div>'
        st.markdown(f'<div class="panel"><div class="panel-title">🏆 Achievements</div>{cards}</div>', unsafe_allow_html=True)