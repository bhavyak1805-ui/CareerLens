import re
import csv
import io
from pathlib import Path
from datetime import datetime

import numpy as np
import requests
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from nav import back_to_dashboard   # shared back button — same as csvtu.py

# ── Adzuna credentials ────────────────────────────────────────────────────────
APP_ID  = "b2dc9183"
APP_KEY = "0a53a4aa5fc072d64d5ac6251d3c8794"
BASE    = "https://api.adzuna.com/v1/api/jobs/in/search"

# ── CSV path (sits next to app.py, same as before) ───────────────────────────
CSV_PATH = Path(__file__).parent / "job_skills_mapping_expanded.csv"

# ── Shared CSS (same blue/white palette as csvtu.py) ─────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:      #f0f4ff;
    --surface: #ffffff;
    --s2:      #f7f9ff;
    --border:  #e4e8f5;
    --accent:  #3b82f6;
    --a-light: #dbeafe;
    --text:    #111827;
    --t2:      #6b7280;
    --muted:   #9ca3af;
    --green:   #10b981;
    --red:     #ef4444;
    --orange:  #f59e0b;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: var(--bg); }
#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; }

/* ── HERO ── */
.jobs-hero {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 32px 44px;
    margin-bottom: 28px;
}
.jobs-hero h1 {
    font-size: 1.55rem; font-weight: 800; color: var(--text);
    margin: 0 0 6px 0; line-height: 1.2;
}
.jobs-hero p { font-size: 0.85rem; color: var(--t2); margin: 0; }

/* ── SECTION HEADING ── */
.section-heading {
    font-size: 1.05rem; font-weight: 700; color: var(--text);
    margin: 8px 0 18px 0; padding-bottom: 10px;
    border-bottom: 2px solid var(--border);
}

/* ── INPUT LABELS ── */
.stTextInput > label, .stSelectbox > label {
    font-size: 0.78rem !important; font-weight: 600 !important; color: var(--t2) !important;
}
.stTextInput input {
    border-radius: 10px !important; border: 1.5px solid var(--border) !important;
    background-color: var(--s2) !important; color: var(--text) !important;
}
.stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}

/* ── SEARCH BUTTON ── */
div[data-testid="stButton"] button {
    background: var(--accent) !important;
    color: #ffffff !important; border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 0.85rem !important;
    transition: opacity 0.2s ease !important;
}
div[data-testid="stButton"] button:hover { opacity: 0.88 !important; }

/* ── APPLY LINK BUTTON ── */
.stLinkButton > a {
    background: var(--accent) !important; color: #fff !important;
    border: none !important; border-radius: 7px !important;
    font-size: 0.8rem !important; font-weight: 600 !important;
    padding: 9px 14px !important;
}
.stLinkButton > a:hover { opacity: 0.88 !important; }

/* ── JOB CARD ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.06) !important;
    margin-bottom: 14px !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: var(--a-light) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important; padding: 10px 12px !important;
}
[data-testid="stMetricLabel"] p {
    color: var(--t2) !important; font-size: 0.7rem !important;
    font-weight: 600 !important; text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: var(--text) !important; font-weight: 600 !important; font-size: 0.85rem !important;
}

/* ── SKILL GAP PANEL ── */
.sgap-wrap {
    background: var(--s2); border: 1.5px solid var(--border);
    border-radius: 12px; padding: 20px 24px; margin: 20px 0 10px;
}
.sgap-header {
    font-size: 0.8rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--accent); margin-bottom: 14px;
}
.sgap-sublabel {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: var(--t2); margin: 12px 0 6px;
}
.chip {
    display: inline-block; font-size: 0.72rem; font-weight: 600;
    padding: 3px 11px; border-radius: 20px; margin: 2px 3px 2px 0;
}
.chip-have { background: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
.chip-miss { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
.course-row {
    display: flex; align-items: center; gap: 10px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 9px 13px; margin-bottom: 6px;
    text-decoration: none !important;
}
.course-row:hover { border-color: var(--accent) !important; }
.cdot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.ctitle { font-size: 0.8rem; font-weight: 600; color: var(--text); flex: 1; }
.cplat  { font-size: 0.7rem; color: var(--muted); }
.carr   { font-size: 0.85rem; color: var(--muted); }

.result-count { font-size: 1.2rem; font-weight: 700; color: var(--text); }
.job-num {
    display: inline-block; background: var(--a-light); color: var(--accent);
    font-size: 0.72rem; font-weight: 700; padding: 2px 9px;
    border-radius: 4px; margin-right: 6px;
}
</style>
"""

# ── Course catalogue (unchanged from original) ────────────────────────────────
FREE_COURSES = {
    "python": [{"title":"Python for Everybody","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/specializations/python"},{"title":"Python Full Course","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=eWRfhZUzrAc"}],
    "java": [{"title":"Java Programming MOOC","platform":"University of Helsinki","url":"https://java-programming.mooc.fi/"},{"title":"Java Full Course","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=grEKMHGYyns"}],
    "javascript": [{"title":"JS Algorithms & Data Structures","platform":"freeCodeCamp","url":"https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/"},{"title":"The Modern JavaScript Tutorial","platform":"javascript.info","url":"https://javascript.info/"}],
    "typescript": [{"title":"TypeScript Handbook","platform":"Official Docs (Free)","url":"https://www.typescriptlang.org/docs/handbook/intro.html"}],
    "sql": [{"title":"SQL for Data Science","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/learn/sql-for-data-science"},{"title":"SQLZoo Interactive Tutorials","platform":"SQLZoo","url":"https://sqlzoo.net/"}],
    "nosql": [{"title":"MongoDB Basics","platform":"MongoDB University (Free)","url":"https://university.mongodb.com/"}],
    "mongodb": [{"title":"MongoDB University (Free)","platform":"MongoDB","url":"https://university.mongodb.com/"}],
    "postgresql": [{"title":"PostgreSQL Tutorial","platform":"postgresqltutorial.com (Free)","url":"https://www.postgresqltutorial.com/"}],
    "mysql": [{"title":"MySQL Tutorial","platform":"mysqltutorial.org (Free)","url":"https://www.mysqltutorial.org/"}],
    "redis": [{"title":"Redis University","platform":"Redis (Free)","url":"https://university.redis.com/"}],
    "react": [{"title":"React Official Tutorial","platform":"React Docs (Free)","url":"https://react.dev/learn"},{"title":"Full Stack Open","platform":"University of Helsinki","url":"https://fullstackopen.com/en/"}],
    "angular": [{"title":"Angular Tour of Heroes","platform":"Angular.io (Free)","url":"https://angular.io/tutorial/tour-of-heroes"}],
    "vue": [{"title":"Vue.js Official Guide","platform":"vuejs.org (Free)","url":"https://vuejs.org/guide/introduction.html"}],
    "nodejs": [{"title":"The Odin Project – Node","platform":"The Odin Project","url":"https://www.theodinproject.com/paths/full-stack-javascript/courses/nodejs"}],
    "django": [{"title":"Django Official Tutorial","platform":"Django Docs (Free)","url":"https://docs.djangoproject.com/en/stable/intro/tutorial01/"},{"title":"CS50 Web with Django","platform":"Harvard CS50 (Free)","url":"https://cs50.harvard.edu/web/2020/"}],
    "flask": [{"title":"Flask Mega-Tutorial","platform":"Miguel Grinberg (Free)","url":"https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world"}],
    "fastapi": [{"title":"FastAPI Official Tutorial","platform":"fastapi.tiangolo.com (Free)","url":"https://fastapi.tiangolo.com/tutorial/"}],
    "aws": [{"title":"AWS Cloud Practitioner Essentials","platform":"AWS Skill Builder (Free)","url":"https://explore.skillbuilder.aws/learn/course/134"},{"title":"AWS Fundamentals","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/specializations/aws-fundamentals"}],
    "azure": [{"title":"Azure Fundamentals AZ-900","platform":"Microsoft Learn (Free)","url":"https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/"}],
    "gcp": [{"title":"Google Cloud Skills Boost","platform":"Google Cloud (Free Tier)","url":"https://cloudskillsboost.google/"}],
    "docker": [{"title":"Docker 101 Tutorial","platform":"Docker Official (Free)","url":"https://www.docker.com/101-tutorial/"},{"title":"Docker Full Course","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=fqMOX6JJhGo"}],
    "kubernetes": [{"title":"Kubernetes Basics","platform":"Kubernetes.io (Free)","url":"https://kubernetes.io/docs/tutorials/kubernetes-basics/"},{"title":"Intro to Kubernetes","platform":"edX – Linux Foundation","url":"https://www.edx.org/learn/kubernetes/the-linux-foundation-introduction-to-kubernetes"}],
    "machine learning": [{"title":"Machine Learning Specialization","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/specializations/machine-learning-introduction"},{"title":"Fast.ai Practical Deep Learning","platform":"Fast.ai (Free)","url":"https://course.fast.ai/"}],
    "deep learning": [{"title":"Deep Learning Specialization","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/specializations/deep-learning"}],
    "natural language processing": [{"title":"HuggingFace NLP Course","platform":"HuggingFace (Free)","url":"https://huggingface.co/learn/nlp-course/"},{"title":"NLP Specialization","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/specializations/natural-language-processing"}],
    "computer vision": [{"title":"CS231n: CNNs for Visual Recognition","platform":"Stanford (Free)","url":"https://cs231n.github.io/"}],
    "tensorflow": [{"title":"TensorFlow Official Tutorials","platform":"TensorFlow.org (Free)","url":"https://www.tensorflow.org/tutorials"}],
    "pytorch": [{"title":"PyTorch Official Tutorials","platform":"PyTorch.org (Free)","url":"https://pytorch.org/tutorials/"}],
    "scikit-learn": [{"title":"Scikit-learn User Guide","platform":"scikit-learn.org (Free)","url":"https://scikit-learn.org/stable/user_guide.html"}],
    "scikit learn": [{"title":"Scikit-learn User Guide","platform":"scikit-learn.org (Free)","url":"https://scikit-learn.org/stable/user_guide.html"}],
    "pandas": [{"title":"Pandas Getting Started","platform":"pandas.pydata.org (Free)","url":"https://pandas.pydata.org/docs/getting_started/"},{"title":"Data Analysis with Python","platform":"freeCodeCamp","url":"https://www.freecodecamp.org/learn/data-analysis-with-python/"}],
    "numpy": [{"title":"NumPy Official Tutorials","platform":"numpy.org (Free)","url":"https://numpy.org/learn/"}],
    "spark": [{"title":"Apache Spark Fundamentals","platform":"edX – IBM (Audit Free)","url":"https://www.edx.org/learn/apache-spark"}],
    "kafka": [{"title":"Apache Kafka Quickstart","platform":"Apache Kafka Docs (Free)","url":"https://kafka.apache.org/quickstart"}],
    "airflow": [{"title":"Apache Airflow Tutorial","platform":"Airflow Docs (Free)","url":"https://airflow.apache.org/docs/apache-airflow/stable/tutorial/"}],
    "snowflake": [{"title":"Snowflake Free Hands-On Labs","platform":"Snowflake (Free)","url":"https://www.snowflake.com/en/developers/tutorials/"}],
    "tableau": [{"title":"Tableau Public Free Training","platform":"Tableau (Free)","url":"https://www.tableau.com/learn/training"}],
    "power bi": [{"title":"Microsoft Power BI Learning","platform":"Microsoft Learn (Free)","url":"https://learn.microsoft.com/en-us/training/powerplatform/power-bi"}],
    "linux": [{"title":"Linux Command Line Basics","platform":"Udacity (Free)","url":"https://www.udacity.com/course/linux-command-line-basics--ud595"},{"title":"The Linux Command Line Book","platform":"linuxcommand.org (Free)","url":"https://linuxcommand.org/tlcl.php"}],
    "git": [{"title":"Pro Git Book","platform":"git-scm.com (Free)","url":"https://git-scm.com/book/en/v2"},{"title":"Git & GitHub Crash Course","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=RGOj5yH7evk"}],
    "data science": [{"title":"IBM Data Science Professional","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/professional-certificates/ibm-data-science"},{"title":"Kaggle Learn","platform":"Kaggle (Free)","url":"https://www.kaggle.com/learn"}],
    "data analysis": [{"title":"Google Data Analytics Certificate","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/professional-certificates/google-data-analytics"}],
    "data engineering": [{"title":"Data Engineering Zoomcamp","platform":"DataTalks.Club (Free)","url":"https://github.com/DataTalksClub/data-engineering-zoomcamp"}],
    "business intelligence": [{"title":"Business Intelligence Concepts","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/learn/business-intelligence-tools"}],
    "devops": [{"title":"DevOps Prerequisites Course","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=Wvf0mBNGjXY"}],
    "ci/cd": [{"title":"GitHub Actions Getting Started","platform":"GitHub Docs (Free)","url":"https://docs.github.com/en/actions/writing-workflows/quickstart"}],
    "terraform": [{"title":"HashiCorp Learn Terraform","platform":"HashiCorp (Free)","url":"https://developer.hashicorp.com/terraform/tutorials"}],
    "graphql": [{"title":"How to GraphQL","platform":"howtographql.com (Free)","url":"https://www.howtographql.com/"}],
    "rest api": [{"title":"APIs for Beginners","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=GZvSYJDk-us"}],
    "microservices": [{"title":"Microservices with Node & React","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=nH4qjmP2KEE"}],
    "html": [{"title":"Responsive Web Design","platform":"freeCodeCamp (Free)","url":"https://www.freecodecamp.org/learn/2022/responsive-web-design/"}],
    "css": [{"title":"CSS Full Course","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=1Rs2ND1ryYc"}],
    "agile": [{"title":"Agile with Atlassian Jira","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/learn/agile-atlassian-jira"}],
    "scrum": [{"title":"Scrum Guide","platform":"Scrum.org (Free)","url":"https://scrumguides.org/scrum-guide.html"}],
    "project management": [{"title":"Google Project Management","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/professional-certificates/google-project-management"}],
    "cybersecurity": [{"title":"Google Cybersecurity Certificate","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/professional-certificates/google-cybersecurity"}],
    "blockchain": [{"title":"Blockchain Basics","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/learn/blockchain-basics"}],
    "excel": [{"title":"Excel Skills for Business","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/specializations/excel"}],
    "communication": [{"title":"Communication Foundations","platform":"LinkedIn Learning (Free Trial)","url":"https://www.linkedin.com/learning/communication-foundations"}],
    "leadership": [{"title":"Inspiring and Motivating Individuals","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/learn/inspiring-leadership"}],
    "golang": [{"title":"A Tour of Go","platform":"go.dev (Free)","url":"https://go.dev/tour/"}],
    "scala": [{"title":"Functional Programming in Scala","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/learn/scala-functional-programming"}],
    "c++": [{"title":"C++ Tutorial for Beginners","platform":"freeCodeCamp / YouTube","url":"https://www.youtube.com/watch?v=vLnPwxZdW4Y"}],
    "elasticsearch": [{"title":"Elasticsearch Getting Started","platform":"Elastic Docs (Free)","url":"https://www.elastic.co/guide/en/elasticsearch/reference/current/getting-started.html"}],
    "dbt": [{"title":"dbt Learn (Free)","platform":"dbt Labs","url":"https://courses.getdbt.com/"}],
    "databricks": [{"title":"Databricks Academy (Free)","platform":"Databricks","url":"https://www.databricks.com/learn/training/home"}],
    "keras": [{"title":"Keras Getting Started","platform":"keras.io (Free)","url":"https://keras.io/getting_started/"}],
    "bash": [{"title":"Bash Scripting Tutorial","platform":"ryanstutorials.net (Free)","url":"https://ryanstutorials.net/bash-scripting-tutorial/"}],
    "nginx": [{"title":"NGINX Official Docs","platform":"nginx.org (Free)","url":"https://nginx.org/en/docs/beginners_guide.html"}],
    "salesforce": [{"title":"Trailhead Salesforce","platform":"Salesforce (Free)","url":"https://trailhead.salesforce.com/"}],
    "figma": [{"title":"Figma for Beginners","platform":"Figma Official (Free)","url":"https://www.figma.com/resources/learn-design/"}],
    "ux": [{"title":"Google UX Design Certificate","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/professional-certificates/google-ux-design"}],
    "cloud computing": [{"title":"Cloud Computing Basics","platform":"Coursera (Audit Free)","url":"https://www.coursera.org/learn/cloud-computing-basics"}],
    "tailwind": [{"title":"Tailwind CSS Docs","platform":"tailwindcss.com (Free)","url":"https://tailwindcss.com/docs/installation"}],
}

PLATFORM_COLORS = {
    "coursera":"#0056D2","freecodecamp":"#0A0A23","youtube":"#FF0000",
    "kaggle":"#20BEFF","fast.ai":"#1A1A2E","microsoft":"#00A4EF",
    "google":"#4285F4","hashicorp":"#7B42BC","mongodb":"#13AA52",
    "snowflake":"#29B5E8","figma":"#F24E1E","tableau":"#E97627",
    "udacity":"#02B3E4","edx":"#02262B","harvard":"#A51C30",
    "atlassian":"#0052CC","salesforce":"#00A1E0","elastic":"#005571",
    "databricks":"#FF3621","dbt":"#FF694A","redis":"#DC382D","default":"#3b82f6",
}


# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_job_skills_csv(path: Path):
    job_map   = {}
    skill_set = set()

    def split_terms(raw):
        terms = []
        for chunk in raw.split(","):
            for sub in chunk.split("/"):
                t = re.sub(r'\s*\(.*?\)', '', sub).strip().lower()
                if t:
                    terms.append(t)
        return terms

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title  = row["Job Title"].strip()
            skills = split_terms(row.get("Core Skills", ""))
            tools  = split_terms(row.get("Tools & Platforms", ""))
            job_map[title.lower()] = {"title": title, "skills": skills, "tools": tools}
            skill_set.update(skills)
            skill_set.update(tools)

    skill_keywords = sorted(skill_set, key=len, reverse=True)
    return job_map, skill_keywords


def get_platform_color(p):
    pl = p.lower()
    for k, c in PLATFORM_COLORS.items():
        if k in pl:
            return c
    return PLATFORM_COLORS["default"]


def extract_skills(text, skill_keywords):
    t = " " + re.sub(r'[/,;|()\[\]{}]', ' ', text.lower()) + " "
    found = set()
    for skill in sorted(skill_keywords, key=len, reverse=True):
        if re.search(r'(?<![a-z])' + re.escape(skill) + r'(?![a-z])', t):
            found.add(skill)
    return found


def split_user_terms(text):
    if not text or not text.strip():
        return []
    parts = re.split(r"[,/;|]", text)
    return [p.strip().lower() for p in parts if p.strip()]


def get_courses(skills):
    result = {}
    for skill in skills:
        if skill in FREE_COURSES:
            result[skill] = FREE_COURSES[skill]
        else:
            for key in FREE_COURSES:
                if key in skill or skill in key:
                    result[skill] = FREE_COURSES[key]
                    break
    return result


def fmt_salary(job):
    lo, hi = job.get("salary_min"), job.get("salary_max")
    if lo and hi: return f"₹{int(lo):,} – ₹{int(hi):,}"
    if lo:        return f"₹{int(lo):,}+"
    if hi:        return f"Up to ₹{int(hi):,}"
    return "Not disclosed"


def fmt_date(raw):
    try:    return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except: return raw[:10] if raw else "—"


def job_to_text(job):
    return " ".join(filter(None, [
        job.get("title", ""),
        job.get("company", {}).get("display_name", ""),
        job.get("category", {}).get("label", ""),
        job.get("description", ""),
        job.get("location", {}).get("display_name", ""),
    ]))


def compute_scores(jobs, user_profile):
    job_texts = [job_to_text(j) for j in jobs]
    corpus    = job_texts + [user_profile]
    vec       = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
    matrix    = vec.fit_transform(corpus)
    scores    = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    return scores


def match_job_title(api_title, job_map):
    t = api_title.lower()
    if t in job_map:
        return job_map[t]
    best, best_len = None, 0
    for key, entry in job_map.items():
        if key in t and len(key) > best_len:
            best, best_len = entry, len(key)
    if best:
        return best
    listing_tokens = set(re.findall(r"[a-z]+", t))
    for key, entry in job_map.items():
        key_tokens = set(re.findall(r"[a-z]+", key))
        if key_tokens and key_tokens.issubset(listing_tokens):
            return entry
    return None


def render_skill_gap_panel(user_skills_text, user_tools_text, keyword, job_map, skill_keywords):
    user_terms = split_user_terms(user_skills_text) + split_user_terms(user_tools_text)
    if not user_terms:
        return

    entry = match_job_title(keyword, job_map)
    if entry:
        required   = entry["skills"] + entry["tools"]
        role_label = entry["title"]
    else:
        required   = list(extract_skills(keyword, skill_keywords))
        role_label = keyword

    if not required:
        return

    user_set = set(user_terms)

    def is_covered(term):
        return any(term == u or term in u or u in term for u in user_set)

    matched   = sorted([r for r in required if is_covered(r)])
    missing   = sorted([r for r in required if not is_covered(r)])
    total     = len(required)
    match_pct = round((len(matched) / total) * 100) if total else 0
    bar_color = "#10b981" if match_pct >= 60 else ("#f59e0b" if match_pct >= 30 else "#ef4444")

    course_recs   = get_courses(missing)
    matched_chips = "".join(f'<span class="chip chip-have">{s}</span>' for s in matched)
    missing_chips = "".join(f'<span class="chip chip-miss">{s}</span>' for s in missing)

    courses_html = ""
    for skill, cl in course_recs.items():
        for c in cl[:1]:
            dot = get_platform_color(c["platform"])
            courses_html += f"""
            <a href="{c['url']}" target="_blank" class="course-row">
              <div class="cdot" style="background:{dot};"></div>
              <div>
                <div class="ctitle">🎓 {c['title']}
                  <span style="font-size:0.7rem;color:#9ca3af;font-weight:400;">— {skill.title()}</span>
                </div>
                <div class="cplat">📌 {c['platform']}</div>
              </div>
              <div class="carr">→</div>
            </a>"""

    matched_sec = f"""
      <div class="sgap-sublabel">✅ Skills You Have ({len(matched)} of {total})</div>
      <div style="margin-bottom:10px;">{matched_chips}</div>
    """ if matched else ""

    missing_sec = (
        f"""
      <div class="sgap-sublabel">❗ Skills Missing ({len(missing)} of {total})</div>
      <div style="margin-bottom:14px;">{missing_chips}</div>
      {'<div class="sgap-sublabel">🆓 Free Courses to Close the Gap</div>' + courses_html if courses_html else ''}
    """ if missing else
        '<div style="font-size:0.82rem;color:#10b981;font-weight:600;margin-top:8px;">✅ Your profile covers all required skills!</div>'
    )

    st.markdown(f"""
    <div class="sgap-wrap">
      <div class="sgap-header">🧩 Profile Match — {role_label}</div>
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;">
        <div style="flex:1;">
          <div style="font-size:0.72rem;color:#6b7280;font-weight:600;margin-bottom:5px;">
            Profile match against standard role requirements
          </div>
          <div style="background:#e4e8f5;border-radius:4px;height:8px;overflow:hidden;">
            <div style="width:{match_pct}%;height:100%;background:{bar_color};border-radius:4px;"></div>
          </div>
        </div>
        <div style="font-size:1.4rem;font-weight:700;color:{bar_color};min-width:52px;text-align:right;">
          {match_pct}%
        </div>
      </div>
      {matched_sec}
      {missing_sec}
    </div>""", unsafe_allow_html=True)


# ── Main render function (called from app.py) ─────────────────────────────────
def render_job_recommendations():
    st.markdown(_CSS, unsafe_allow_html=True)
    back_to_dashboard()

    # ── CSV guard ─────────────────────────────────────────────────────────────
    if not CSV_PATH.exists():
        st.error(f"CSV not found: {CSV_PATH} — place job_skills_mapping_expanded.csv next to app.py")
        return

    job_map, skill_keywords = load_job_skills_csv(CSV_PATH)

    # ── Hero header ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="jobs-hero">
        <h1>💼 Recommended Jobs</h1>
        <p>Live listings across India &nbsp;·&nbsp; TF-IDF powered smart matching</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Search parameters ─────────────────────────────────────────────────────
    st.markdown('<div class="section-heading">🔍 Search Parameters</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    keyword   = c1.text_input("Role / Keyword", value="Python Developer")
    location  = c2.text_input("Location", placeholder="Mumbai, Bangalore…")
    sort_by   = c3.selectbox("Sort By", ["relevance", "date", "salary"])
    results_n = c4.selectbox("Results", [10, 20, 30, 50])

    st.markdown('<div class="section-heading">👤 Your Profile — for Skill Gap Analysis</div>',
                unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    user_skills = p1.text_input("Your Skills", placeholder="Python, Machine Learning, SQL…")
    user_tools  = p2.text_input("Tools & Platforms", placeholder="Docker, AWS, Jupyter…")

    st.markdown("<br>", unsafe_allow_html=True)
    search = st.button("🔎 Search & Rank Opportunities", use_container_width=True)

    # ── Fetch + display results ───────────────────────────────────────────────
    if not (search or keyword):
        return

    params = {
        "app_id": APP_ID, "app_key": APP_KEY,
        "what": keyword, "sort_by": sort_by,
        "results_per_page": results_n,
    }
    if location:
        params["where"] = location

    with st.spinner("Fetching listings…"):
        try:
            r = requests.get(f"{BASE}/1", params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            st.error(f"Connection error: {e}")
            return

    jobs  = data.get("results", [])
    total = data.get("count", 0)

    if not jobs:
        st.warning("No positions found. Try a different keyword or location.")
        return

    user_profile = f"{keyword} {user_skills} {user_tools}".strip()
    using_tfidf  = bool(user_skills or user_tools)

    if using_tfidf:
        scores = compute_scores(jobs, user_profile)
        for i, job in enumerate(jobs):
            job["_score"] = float(scores[i])
        jobs = sorted(jobs, key=lambda j: j["_score"], reverse=True)
        render_skill_gap_panel(user_skills, user_tools, keyword, job_map, skill_keywords)

    st.markdown('<div class="section-heading">📋 Results</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="result-count">{total:,} positions &nbsp;·&nbsp; Showing {len(jobs)}</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    for rank, job in enumerate(jobs, 1):
        title    = job.get("title", "N/A")
        company  = job.get("company", {}).get("display_name", "Unknown")
        loc_disp = job.get("location", {}).get("display_name", "—")
        category = job.get("category", {}).get("label", "—")
        created  = fmt_date(job.get("created", ""))
        apply    = job.get("redirect_url", "#")
        salary   = fmt_salary(job)
        desc     = job.get("description", "")
        desc_short = (desc[:300] + "…") if len(desc) > 300 else desc
        contract = job.get("contract_type", "")

        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f'<span class="job-num">#{rank}</span>', unsafe_allow_html=True)
                st.markdown(f"#### {title}")
                st.markdown(f"🏢 **{company}** &nbsp;&nbsp; 📍 {loc_disp} &nbsp;&nbsp; 🏷 {category}")
            with col2:
                st.link_button("Apply →", apply, use_container_width=True)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Salary",   salary)
            m2.metric("Posted",   created)
            m3.metric("Contract", contract.replace("_", " ").title() if contract else "—")
            m4.metric("City",     loc_disp.split(",")[0])

            if desc_short:
                st.caption(desc_short)