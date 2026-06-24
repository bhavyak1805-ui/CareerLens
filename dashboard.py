import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import datetime
import requests
from db import get_conn

# ── Adzuna credentials (kept server-side only, never rendered in UI) ──────────
_ADZUNA_APP_ID  = "de9d9ffd"
_ADZUNA_APP_KEY = "fe0dfad323224ae4fd989408bc94e51c"

# ── Cached dataset ─────────────────────────────────────────────────────────────
@st.cache_data
def load_dataset():
    try:
        df = pd.read_csv("india_jobs_only.csv")
    except FileNotFoundError:
        df = pd.DataFrame({
            "job_title":        ["AI Engineer","ML Engineer","Data Scientist",
                                 "Software Engineer","DevOps Engineer",
                                 "Backend Developer","Frontend Developer",
                                 "Cloud Engineer","Cybersecurity Analyst","Product Manager"]*3,
            "experience_years": list(range(0,21))*2,
            "education_level":  (["PhD","Master","Bachelor","Diploma","High School"]*12)[:42],
            "company_size":     (["Enterprise","Startup","Medium","Large","Small"]*12)[:42],
            "remote_work":      (["Yes","No","Hybrid"]*14)[:42],
            "industry":         (["Technology","Finance","Healthcare","Retail","Consulting"]*9)[:42],
            "skills_count":     list(range(1,20))*3,
            "certifications":   ([0,1,2,3,4,5]*7)[:42],
            "salary":           [117040,109255,97834,94707,101571,
                                 93449,89149,101699,99861,105598]*3,
        })
    return df

CHART_CFG = {"displayModeBar": False}

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_adzuna_jobs(query, location, max_results=8):
    """Fetch live job listings from Adzuna. Returns [] on any failure."""
    try:
        url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
        params = {
            "app_id":        _ADZUNA_APP_ID,
            "app_key":       _ADZUNA_APP_KEY,
            "results_per_page": max_results,
            "what":          query or "software",
            "where":         location or "India",
            "content-type":  "application/json",
        }
        resp = requests.get(url, params=params, timeout=6)
        if resp.status_code != 200:
            return []
        data = resp.json()
        jobs = []
        for r in data.get("results", []):
            jobs.append({
                "title":    r.get("title", "—"),
                "company":  (r.get("company") or {}).get("display_name", "Confidential"),
                "location": (r.get("location") or {}).get("display_name", location or "India"),
                "salary":   r.get("salary_min"),
                "url":      r.get("redirect_url", "#"),
                "created":  (r.get("created") or "")[:10],
            })
        return jobs
    except Exception:
        return []

def cl(**kw):
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color="#374151"),
        margin=dict(l=8, r=8, t=10, b=8),
    )
    base.update(kw)
    return base

# ──────────────────────────────────────────────────────────────────────────────
def render_dashboard():
    user    = st.session_state.current_user
    profile = st.session_state.profile
    name    = user.get("full_name", "Student")
    df      = load_dataset()

    if "show_profile_panel" not in st.session_state:
        st.session_state.show_profile_panel = False

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg:        #f0f4ff;
    --surface:   #ffffff;
    --s2:        #f7f9ff;
    --border:    #e4e8f5;
    --accent:    #3b82f6;
    --a-light:   #dbeafe;
    --a2:        #10b981;
    --a3:        #f59e0b;
    --a4:        #ef4444;
    --text:      #111827;
    --t2:        #6b7280;
    --muted:     #9ca3af;
    --sidebar-w: 200px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

.stApp { background: var(--bg) !important; }

.main .block-container {
    padding: 0 1.5rem 2rem !important;
    max-width: 100% !important;
}

/* ── SIDEBAR ─────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    width: var(--sidebar-w) !important;
    min-width: var(--sidebar-w) !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 0.75rem !important;
}

/* ── NAV BUTTONS — reference style ──────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    color: var(--t2) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    padding: 0.55rem 0.85rem !important;
    transition: all 0.15s !important;
    white-space: nowrap !important;
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    background: var(--a-light) !important;
    color: var(--accent) !important;
}

/* Active nav — filled blue pill like reference */
.nav-active > button {
    background: var(--accent) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
}
.nav-active > button:hover {
    background: #2563eb !important;
    color: #ffffff !important;
}

/* Ghost (edit profile) */
.btn-ghost > button {
    background: transparent !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
    font-size: 0.78rem !important;
    padding: 0.38rem 0.8rem !important;
    border-radius: 8px !important;
    width: auto !important;
}
.btn-ghost > button:hover {
    background: var(--a-light) !important;
}

/* Avatar button */
.avatar-btn > button {
    border-radius: 50% !important;
    width: 42px !important;
    height: 42px !important;
    padding: 0 !important;
    background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    box-shadow: none !important;
    border: 2px solid white !important;
    float: right !important;
}

/* ── WHITE PANEL CARD ─────────────────────────────────────────────────── */
.panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.1rem 1.25rem;
    height: 100%;
}
.panel-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.9rem;
}

/* ── TOP HEADER BAR ──────────────────────────────────────────────────── */
.top-bar {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0.7rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 -1.5rem 1.25rem -1.5rem;
}

/* ── JOB LIST ────────────────────────────────────────────────────────── */
.job-scroll {
    max-height: 295px;
    overflow-y: auto;
    padding-right: 4px;
}
.job-scroll::-webkit-scrollbar { width: 4px; }
.job-scroll::-webkit-scrollbar-thumb {
    background: #c7d2fe;
    border-radius: 4px;
}

/* ── SIDEBAR LOGO ──────────────────────────────────────────────────────*/
.brand-row {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 1.8rem;
    padding: 0 0.25rem;
}
.brand-icon {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 1rem;
    flex-shrink: 0;
}
.brand-name {
    font-weight: 800;
    font-size: 0.95rem;
    color: var(--text);
    letter-spacing: -0.3px;
}
.brand-name span { color: #3b82f6; }

/* ── NAV SECTION LABEL ─────────────────────────────────────────────────*/
.nav-lbl {
    font-size: 0.58rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--muted);
    font-weight: 600;
    margin: 1rem 0 0.35rem 0.5rem;
}

/* ── SIDEBAR NAV ITEM wrapper ──────────────────────────────────────────*/
.nav-item {
    margin-bottom: 2px;
}

/* ── PROFILE PROGRESS ──────────────────────────────────────────────────*/
.progress-wrap {
    margin-top: 1.8rem;
    padding: 0.85rem;
    background: var(--s2);
    border: 1px solid var(--border);
    border-radius: 12px;
}

/* ── PLACEHOLDER ───────────────────────────────────────────────────────*/
.placeholder-box {
    border: 2px dashed var(--border);
    border-radius: 14px;
    min-height: 230px;
    display: flex; align-items: center; justify-content: center;
    background: var(--s2);
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-thumb { background: #c7d2fe; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

    initials = "".join(p[0].upper() for p in name.split()[:2])
    fields_done = ["dob","gender","city","state","target_role","about_me"]
    pct = int(sum(1 for f in fields_done if user.get(f)) / len(fields_done) * 100)

    # ════════════════════════════════════════════════════════════════════════
    # SIDEBAR  — reference style: solid blue pill for active, icons + labels
    # ════════════════════════════════════════════════════════════════════════
    with st.sidebar:
        # ── Brand ──
        st.markdown("""
        <div class="brand-row">
          <div class="brand-icon">🚀</div>
          <div class="brand-name">Career<span>Lens</span></div>
        </div>
        """, unsafe_allow_html=True)

        active = st.session_state.get("active_module")

        # ── Main ──
        st.markdown('<div class="nav-lbl">Main</div>', unsafe_allow_html=True)

        cls = "nav-active nav-item" if active is None else "nav-item"
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.button("🏠  Dashboard", key="nav_dash"):
            st.session_state.active_module = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Modules ──
        st.markdown('<div class="nav-lbl">Modules</div>', unsafe_allow_html=True)

        nav_modules = [
            ("📋", "Applications",       "applications"),
            ("💡", "Job Recommendations", "job_rec"),
            ("🤖", "AI Chatbot — Aria",   "chatbot"),
            ("🏛️", "CSVTU Login",         "csvtu"),
        ]

        for icon, label, key in nav_modules:
            cls = "nav-active nav-item" if key == active else "nav-item"
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nav_{key}"):
                st.session_state.active_module = key
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── System ──
        st.markdown('<div class="nav-lbl">System</div>', unsafe_allow_html=True)

        cls = "nav-active nav-item" if active == "help" else "nav-item"
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.button("🛟  Help Center", key="nav_help"):
            st.session_state.active_module = "help"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="nav-item">', unsafe_allow_html=True)
        if st.button("🚪  Logout", key="logout_btn"):
            st.session_state.logged_in     = False
            st.session_state.current_user  = None
            st.session_state.profile       = {"loaded": False}
            st.session_state.active_module = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Profile progress ──
        st.markdown(f"""
        <div class="progress-wrap">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <span style="font-size:0.68rem;color:#64748b;font-weight:500;">Profile</span>
            <span style="font-size:0.68rem;font-weight:700;color:#3b82f6;">{pct}%</span>
          </div>
          <div style="background:#e0e7ff;border-radius:20px;height:5px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;
                        background:linear-gradient(90deg,#3b82f6,#6366f1);
                        border-radius:20px;"></div>
          </div>
          <div style="font-size:0.63rem;color:#94a3b8;margin-top:6px;">
            Complete your profile to unlock features
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # TOP HEADER BAR
    # ════════════════════════════════════════════════════════════════════════
    now      = datetime.datetime.now()
    hour     = now.hour
    greet    = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 17 else "Good Evening")
    date_str = now.strftime("%A, %B ") + str(now.day)

    hdr_left, hdr_search, hdr_right = st.columns([0.35, 0.40, 0.25])
    with hdr_left:
        st.markdown(f"""
        <div style="padding:0.7rem 0 0.5rem 0;">
          <div style="font-size:1.25rem;font-weight:800;color:#111827;">
            {greet}, {name.split()[0]} Here!
          </div>
          <div style="font-size:0.72rem;color:#9ca3af;margin-top:2px;">{date_str}</div>
        </div>
        """, unsafe_allow_html=True)

    with hdr_search:
        st.markdown("""
        <div style="padding-top:0.85rem;">
          <div style="display:flex;align-items:center;gap:8px;
                      background:#f7f9ff;border:1px solid #e4e8f5;
                      border-radius:24px;padding:0.45rem 1rem;">
            <span style="color:#9ca3af;font-size:0.9rem;">🔍</span>
            <span style="font-size:0.78rem;color:#9ca3af;">Search your favourite job here…</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with hdr_right:
        st.markdown('<div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;padding-top:0.55rem;">', unsafe_allow_html=True)
        avatar_col, info_col = st.columns([0.35, 0.65])
        with info_col:
            st.markdown(f"""
            <div style="text-align:right;">
              <div style="font-size:0.8rem;font-weight:700;color:#111827;">{name}</div>
              <div style="font-size:0.65rem;color:#9ca3af;">
                {user.get('target_role') or 'Looking for a job'}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with avatar_col:
            st.markdown('<div class="avatar-btn">', unsafe_allow_html=True)
            if st.button(initials, key="avatar_toggle", help="View profile"):
                st.session_state.show_profile_panel = not st.session_state.show_profile_panel
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Profile panel ────────────────────────────────────────────────────────
    if st.session_state.show_profile_panel:
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #e4e8f5;border-radius:16px;
                    padding:1.2rem 1.4rem;margin-bottom:1rem;
                    box-shadow:0 4px 20px rgba(0,0,0,0.07);">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.8rem;">
            <div style="width:42px;height:42px;border-radius:50%;
                        background:linear-gradient(135deg,#3b82f6,#6366f1);
                        display:flex;align-items:center;justify-content:center;
                        font-weight:800;font-size:0.95rem;color:white;">{initials}</div>
            <div>
              <div style="font-weight:700;font-size:0.95rem;color:#111827;">{name}</div>
              <div style="font-size:0.72rem;color:#6b7280;">
                {user.get('target_role') or 'Set your target role'}
              </div>
            </div>
          </div>
          <div style="font-size:0.75rem;color:#6b7280;line-height:2;
                      display:grid;grid-template-columns:1fr 1fr;gap:2px;">
            <span>📧 {user.get('email','')}</span>
            <span>📱 {user.get('phone') or '—'}</span>
            <span>📍 {user.get('city','')}{', '+user.get('state','') if user.get('state') else ''}</span>
            <span>📅 Since {str(user.get('created_at',''))[:10]}</span>
          </div>
        </div>""", unsafe_allow_html=True)
        ep_col, _ = st.columns([0.2, 0.8])
        with ep_col:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("✏️ Edit", key="edit_profile_btn"):
                try:
                    conn = get_conn(); cur = conn.cursor()
                    cur.execute("UPDATE users SET profile_completed=FALSE WHERE user_id=%s",
                                (user["user_id"],))
                    conn.commit(); conn.close()
                except: pass
                st.session_state.current_user["profile_completed"] = False
                st.session_state.onboarding_step = 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # ROW 1 — Jobs Stats + Salary by Role
    # (Metric cards row REMOVED as per request)
    # ════════════════════════════════════════════════════════════════════════
    r1_left, r1_right = st.columns([0.60, 0.40], gap="medium")

    with r1_left:
        import random; random.seed(42)
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        sent   = [random.randint(15,70) for _ in months]
        accept = [random.randint(10,45) for _ in months]

        fig_jobs = go.Figure()
        fig_jobs.add_trace(go.Scatter(
            x=months, y=sent, name="Application Sent",
            mode="lines+markers",
            line=dict(color="#10b981", width=2.5, shape="spline"),
            marker=dict(color="#10b981", size=5),
            fill="tozeroy", fillcolor="rgba(16,185,129,0.07)",
            hovertemplate="%{x}: %{y}<extra>Sent</extra>",
        ))
        fig_jobs.add_trace(go.Scatter(
            x=months, y=accept, name="Application Accepted",
            mode="lines+markers",
            line=dict(color="#3b82f6", width=2.5, shape="spline"),
            marker=dict(color="#3b82f6", size=5),
            fill="tozeroy", fillcolor="rgba(59,130,246,0.07)",
            hovertemplate="%{x}: %{y}<extra>Accepted</extra>",
        ))
        fig_jobs.update_layout(**cl(
            xaxis=dict(showgrid=False, tickfont=dict(size=10), title=""),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9",
                       tickfont=dict(size=10), title=""),
            height=260,
            legend=dict(
                bgcolor="rgba(0,0,0,0)", font=dict(size=10),
                orientation="h", yanchor="top", y=1.15, xanchor="left", x=0,
            ),
        ))
        st.markdown("""
        <div class="panel">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;">
            <div class="panel-title" style="margin-bottom:0;">📊 Jobs Stats</div>
            <div style="font-size:0.7rem;color:#6b7280;border:1px solid #e4e8f5;
                        border-radius:7px;padding:3px 10px;cursor:pointer;">This Month ▾</div>
          </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig_jobs, use_container_width=True, config=CHART_CFG)
        st.markdown('</div>', unsafe_allow_html=True)

    with r1_right:
        role_sal = df.groupby("job_title")["salary"].mean().sort_values().tail(6).round(0)
        fig_bar = go.Figure(go.Bar(
            x=role_sal.values, y=role_sal.index, orientation="h",
            marker=dict(
                color=["#bfdbfe","#93c5fd","#60a5fa","#3b82f6","#2563eb","#1d4ed8"][:len(role_sal)],
                line=dict(width=0)
            ),
            text=[f"₹{v/1000:.0f}k" for v in role_sal.values],
            textposition="outside", textfont=dict(size=9, color="#374151"),
        ))
        fig_bar.update_layout(**cl(
            xaxis=dict(showgrid=False, showticklabels=False, title=""),
            yaxis=dict(showgrid=False, tickfont=dict(size=9.5)),
            height=260,
        ))
        st.markdown("""
        <div class="panel">
          <div class="panel-title">💼 Avg Salary by Role</div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig_bar, use_container_width=True, config=CHART_CFG)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # ROW 2 — Donut + Recent Jobs
    # ════════════════════════════════════════════════════════════════════════
    r2_left, r2_right = st.columns([0.38, 0.62], gap="medium")

    with r2_left:
        wm = df["remote_work"].value_counts()
        lm = {"Yes": "Remote", "No": "On-site", "Hybrid": "Hybrid"}
        fig_donut = go.Figure(go.Pie(
            labels=[lm.get(k, k) for k in wm.index],
            values=wm.values,
            hole=0.64,
            marker=dict(
                colors=["#3b82f6", "#10b981", "#f59e0b"],
                line=dict(color="#fff", width=3),
            ),
            textinfo="label+percent",
            textfont=dict(size=10.5),
            hovertemplate="%{label}: %{value:,}<extra></extra>",
        ))
        fig_donut.add_annotation(
            text=f"<b>66%</b><br><span style='font-size:10px'>Management</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color="#111827"), align="center",
        )
        fig_donut.update_layout(**cl(
            height=270, showlegend=False,
        ))
        st.markdown("""
        <div class="panel">
          <div class="panel-title">🌐 Relevant Jobs Posted</div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig_donut, use_container_width=True, config=CHART_CFG)
        st.markdown("""
          <div style="text-align:center;font-size:0.72rem;color:#6b7280;margin-top:-0.4rem;">
            Management jobs<br>
            <span style="font-size:0.62rem;color:#9ca3af;">621 new jobs posted today</span>
          </div>
        </div>""", unsafe_allow_html=True)

    with r2_right:
        search_role = user.get("target_role") or "software developer"
        search_city = user.get("city") or "India"
        jobs = fetch_adzuna_jobs(search_role, search_city, max_results=6)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.9rem;">
          <div class="panel-title" style="margin-bottom:0;">📋 Most Recent</div>
          <div style="font-size:1rem;color:#9ca3af;cursor:pointer;">⋯</div>
        </div>
        """, unsafe_allow_html=True)

        if jobs:
            st.markdown("""
            <div style="display:grid;grid-template-columns:30px 1fr 1fr 90px 40px;
                        gap:8px;padding:0 0 6px 0;
                        border-bottom:1px solid #e4e8f5;margin-bottom:4px;">
              <div style="font-size:0.65rem;color:#9ca3af;font-weight:600;"></div>
              <div style="font-size:0.65rem;color:#9ca3af;font-weight:600;">ID / Company</div>
              <div style="font-size:0.65rem;color:#9ca3af;font-weight:600;">Role</div>
              <div style="font-size:0.65rem;color:#9ca3af;font-weight:600;">Type</div>
              <div style="font-size:0.65rem;color:#9ca3af;font-weight:600;">Apply</div>
            </div>""", unsafe_allow_html=True)

            colors_cycle = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4"]
            rows_html = '<div class="job-scroll">'
            for i, j in enumerate(jobs):
                initials_co = (j["company"][:2]).upper()
                ic_bg  = colors_cycle[i % len(colors_cycle)]
                app_id = f"#APL-{1000+i:04d}"
                sal    = f"₹{int(j['salary']):,}+" if j.get("salary") else "FULLTIME"
                rows_html += f"""
                <div style="display:grid;grid-template-columns:30px 1fr 1fr 90px 40px;
                             gap:8px;align-items:center;
                             padding:7px 0;border-bottom:1px solid #f3f4f6;">
                  <input type="checkbox" style="width:14px;height:14px;accent-color:#3b82f6;">
                  <div>
                    <div style="font-size:0.72rem;font-weight:600;color:#9ca3af;">{app_id}</div>
                    <div style="display:flex;align-items:center;gap:5px;margin-top:2px;">
                      <div style="width:20px;height:20px;border-radius:5px;
                                  background:{ic_bg};display:inline-flex;align-items:center;
                                  justify-content:center;font-size:0.55rem;
                                  font-weight:700;color:white;">{initials_co}</div>
                      <span style="font-size:0.72rem;color:#374151;">{j['company'][:20]}</span>
                    </div>
                  </div>
                  <div>
                    <div style="font-size:0.75rem;font-weight:600;color:#111827;">{j['title'][:22]}</div>
                    <div style="font-size:0.65rem;color:#9ca3af;">Creative Design Agency</div>
                  </div>
                  <div style="font-size:0.65rem;font-weight:600;
                               background:#dbeafe;color:#1d4ed8;
                               border-radius:20px;padding:2px 8px;
                               text-align:center;">{sal[:8]}</div>
                  <a href="{j['url']}" target="_blank"
                     style="font-size:0.7rem;color:#3b82f6;text-decoration:none;">✉️</a>
                </div>"""
            rows_html += '</div>'
            st.markdown(rows_html, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="placeholder-box">
              <div style="text-align:center;color:#c7d2fe;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">🔍</div>
                <div style="font-size:0.78rem;font-weight:600;color:#6b7280;">
                  No live jobs found right now
                </div>
                <div style="font-size:0.68rem;color:#9ca3af;margin-top:4px;">
                  Try updating your target role in profile
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)