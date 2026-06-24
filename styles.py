GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg:        #f0f4ff;
    --surface:   #ffffff;
    --surface2:  #f7f9ff;
    --surface3:  #eef2ff;
    --border:    #e4e8f5;
    --border2:   #d1d9f0;
    --accent:    #3b82f6;
    --accent2:   #6366f1;
    --a-light:   #dbeafe;
    --a-light2:  #e0e7ff;
    --a2:        #10b981;
    --a2-light:  #d1fae5;
    --a3:        #f59e0b;
    --a3-light:  #fef3c7;
    --a4:        #ef4444;
    --a4-light:  #fee2e2;
    --cyan:      #06b6d4;
    --text:      #111827;
    --text2:     #374151;
    --t2:        #6b7280;
    --muted:     #9ca3af;
    --sidebar-w: 230px;
    --success:   #10b981;
    --error:     #ef4444;
    --warn:      #f59e0b;
    --gold:      #f59e0b;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }
.main .block-container {
    padding: 0 1.5rem 2rem !important;
    max-width: 100% !important;
}

/* ── SCROLLBAR ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--surface2); }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 4px; opacity: 0.5; }

/* ── SIDEBAR ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    width: var(--sidebar-w) !important;
    min-width: var(--sidebar-w) !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* ── TABS ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface2) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    padding: 4px !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    color: var(--t2) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    padding: 8px 20px !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: white !important;
    box-shadow: 0 3px 12px rgba(59,130,246,0.3) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem !important; }

/* ── INPUTS ──────────────────────────────────────────────────────────────── */
.stTextInput input,
.stTextArea textarea,
.stSelectbox > div > div,
.stNumberInput input {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    transition: all 0.2s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    background: var(--surface) !important;
}
label { color: var(--t2) !important; font-size: 0.8rem !important; font-weight: 500 !important; }

/* ── BUTTONS ─────────────────────────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    color: var(--t2) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
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

/* Primary action button */
.btn-primary > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    text-align: center !important;
    justify-content: center !important;
    box-shadow: 0 2px 12px rgba(59,130,246,0.25) !important;
}
.btn-primary > button:hover {
    background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(59,130,246,0.35) !important;
    color: white !important;
}

/* Active nav */
.nav-active > button {
    background: var(--a-light) !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
}

/* Ghost */
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

/* Avatar */
.avatar-btn > button {
    border-radius: 50% !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    box-shadow: none !important;
    border: 2px solid white !important;
    float: right !important;
}

/* ── CARDS ───────────────────────────────────────────────────────────────── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.9rem;
}
.card-sm {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
}
.card-header {
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--accent);
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 6px;
}
.card-header::before {
    content: '';
    display: inline-block;
    width: 3px; height: 12px;
    background: var(--accent);
    border-radius: 2px;
}

/* ── BADGES ──────────────────────────────────────────────────────────────── */
.badge {
    display: inline-flex; align-items: center;
    background: var(--a-light); color: var(--accent);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 20px; padding: 3px 11px;
    font-size: 0.7rem; font-weight: 600; gap: 4px;
}
.badge.green  { background: var(--a2-light); color: #065f46; border-color: rgba(16,185,129,0.2); }
.badge.red    { background: var(--a4-light); color: #991b1b; border-color: rgba(239,68,68,0.2); }
.badge.orange { background: var(--a3-light); color: #92400e; border-color: rgba(245,158,11,0.2); }
.badge.cyan   { background: #cffafe; color: #155e75; border-color: rgba(6,182,212,0.2); }
.badge.purple { background: var(--a-light2); color: #3730a3; border-color: rgba(99,102,241,0.2); }

/* ── SKILL CHIPS ─────────────────────────────────────────────────────────── */
.skill-chip {
    display: inline-flex; align-items: center;
    background: var(--a-light);
    color: var(--accent);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 8px; padding: 4px 12px;
    font-size: 0.72rem; font-weight: 500;
    margin: 3px; transition: all 0.15s;
}
.skill-chip:hover { background: var(--accent); color: white; }
.skill-chip.green { background: var(--a2-light); color: #065f46; border-color: rgba(16,185,129,0.2); }
.skill-chip.red   { background: var(--a4-light); color: #991b1b; border-color: rgba(239,68,68,0.2); }

/* ── DIVIDER ─────────────────────────────────────────────────────────────── */
.divider {
    display: flex; align-items: center; gap: 1rem; margin: 1.2rem 0;
    color: var(--muted); font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;
}
.divider::before, .divider::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
}

/* ── PROGRESS ────────────────────────────────────────────────────────────── */
.progress-wrap {
    background: var(--surface3); border-radius: 20px; height: 6px; overflow: hidden;
}
.progress-fill {
    height: 100%; border-radius: 20px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    transition: width 0.8s ease;
    position: relative; overflow: hidden;
}
.progress-fill::after {
    content: ''; position: absolute; top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg,transparent,rgba(255,255,255,0.4),transparent);
    animation: shimmer 2s infinite;
}
@keyframes shimmer { 0%{left:-100%} 100%{left:100%} }

/* ── STAT CARDS ──────────────────────────────────────────────────────────── */
.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px; padding: 1.1rem;
    text-align: center; transition: all 0.2s;
}
.stat-card:hover {
    border-color: var(--accent);
    box-shadow: 0 4px 20px rgba(59,130,246,0.12);
    transform: translateY(-2px);
}
.stat-number {
    font-size: 2rem; font-weight: 800;
    color: var(--accent); line-height: 1.1;
}
.stat-label { font-size: 0.72rem; color: var(--muted); margin-top: 4px; }

/* ── TIMELINE ────────────────────────────────────────────────────────────── */
.timeline-item {
    border-left: 2px solid var(--border);
    padding-left: 1.2rem; margin-bottom: 1.2rem; position: relative;
}
.timeline-item::before {
    content: ''; position: absolute; left: -5px; top: 6px;
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 0 3px var(--a-light);
}

/* ── METRIC CARD ─────────────────────────────────────────────────────────── */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px; padding: 1rem 1.1rem;
    display: flex; align-items: center; gap: 0.75rem;
}
.metric-icon {
    width: 36px; height: 36px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0;
}
.metric-val { font-size: 1.45rem; font-weight: 800; color: var(--text); line-height: 1; }
.metric-lbl { font-size: 0.68rem; color: var(--muted); font-weight: 500; margin-top: 2px; }
.metric-delta-up   { font-size: 0.68rem; color: var(--a2); font-weight: 600; }
.metric-delta-down { font-size: 0.68rem; color: var(--a4); font-weight: 600; }

/* ── PANEL ───────────────────────────────────────────────────────────────── */
.panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px; padding: 1.1rem 1.25rem; height: 100%;
}
.panel-title {
    font-size: 0.88rem; font-weight: 700;
    color: var(--text); margin-bottom: 0.9rem;
}

/* ── MODULE HERO ─────────────────────────────────────────────────────────── */
.module-hero {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    position: relative; overflow: hidden;
}
.module-hero::before {
    content: '';
    position: absolute; top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}
.module-hero-tag {
    font-size: 0.62rem; font-family: 'JetBrains Mono', monospace;
    color: rgba(255,255,255,0.75); letter-spacing: 3px;
    text-transform: uppercase; margin-bottom: 0.5rem;
}
.module-hero-title {
    font-size: 1.9rem; font-weight: 800; color: white;
    letter-spacing: -0.5px; line-height: 1.15; margin-bottom: 0.4rem;
}
.module-hero-sub { font-size: 0.85rem; color: rgba(255,255,255,0.8); }

/* ── LOGIN/AUTH SPECIFIC ─────────────────────────────────────────────────── */
.auth-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2rem 2.2rem;
    box-shadow: 0 8px 32px rgba(59,130,246,0.08);
}

/* ── CAM HINT ────────────────────────────────────────────────────────────── */
.cam-hint {
    background: var(--surface2);
    border: 2px dashed var(--border2);
    border-radius: 14px; padding: 1.2rem;
    text-align: center; color: var(--muted);
    font-size: 0.82rem; margin-bottom: 0.8rem;
}

/* ── SIDEBAR NAV LABELS ──────────────────────────────────────────────────── */
.nav-lbl {
    font-size: 0.6rem; text-transform: uppercase;
    letter-spacing: 1.5px; color: var(--muted);
    font-weight: 600; margin: 1rem 0 0.3rem 0.3rem;
}
.brand-row {
    display: flex; align-items: center; gap: 9px; margin-bottom: 1.6rem;
}
.brand-icon {
    width: 34px; height: 34px; border-radius: 9px;
    background: var(--accent);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 1rem;
}
.brand-name {
    font-weight: 800; font-size: 1rem;
    color: var(--text); letter-spacing: -0.3px;
}
.brand-name span { color: var(--accent); }

/* ── PROGRESS SIDEBAR ────────────────────────────────────────────────────── */
.progress-wrap-side {
    margin-top: 1.8rem; padding: 0.85rem;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 12px;
}

/* ── FORM SUBMIT ─────────────────────────────────────────────────────────── */
div[data-testid="stFormSubmitButton"] button {
    width: 100% !important;
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #ffffff !important; border: none !important;
    border-radius: 10px !important; padding: 0.6rem 0 !important;
    font-weight: 600 !important; font-size: 0.92rem !important;
    margin-top: 6px !important; justify-content: center !important;
    text-align: center !important;
}
div[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
    box-shadow: 0 4px 16px rgba(59,130,246,0.3) !important;
}

/* ── JOB CARDS ───────────────────────────────────────────────────────────── */
.job-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 12px; padding: 0.85rem 1rem; margin: 0.5rem 0;
    transition: box-shadow 0.2s;
}
.job-card:hover { box-shadow: 0 4px 16px rgba(59,130,246,0.1); }
.job-card-tag {
    display: inline-block; font-size: 0.62rem; font-weight: 700;
    color: var(--accent); background: var(--a-light);
    padding: 2px 9px; border-radius: 999px; margin-bottom: 6px;
    letter-spacing: 0.02em; text-transform: uppercase;
}
.job-card-title { font-weight: 700; font-size: 0.88rem; color: var(--text); margin-bottom: 2px; }
.job-card-why   { font-size: 0.78rem; color: var(--t2); margin: 0; }

/* ── MISC ────────────────────────────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden !important; }
.match-bar-wrap { background: var(--surface3); border-radius: 4px; height: 5px; overflow: hidden; }
.match-bar-fill { height:100%; background: linear-gradient(90deg,var(--accent),var(--accent2)); border-radius:4px; }
.result-count   { font-size:22px; font-weight:700; color:var(--text); letter-spacing:-0.5px; }
.tfidf-badge    {
    display:inline-block;
    background: linear-gradient(135deg,var(--accent),var(--accent2));
    color:#fff; font-size:10px; font-weight:700; letter-spacing:1.2px;
    text-transform:uppercase; padding:5px 12px; border-radius:20px;
}
.job-num {
    display:inline-block; background:var(--a-light);
    color:var(--accent); font-size:11px; font-weight:700;
    padding:2px 9px; border-radius:4px; margin-right:6px;
}
</style>
"""