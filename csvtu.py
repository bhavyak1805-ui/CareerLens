import base64
import csv
import re
from pathlib import Path

import streamlit as st
from mysql.connector import Error

from db   import get_conn            # shared DB connection — same as all other pages
from auth import check_pw            # shared bcrypt verification — same as app.py login
from nav  import back_to_dashboard   # shared back button

# ── Asset paths ───────────────────────────────────────────────────────────────
LOGO_PATH  = Path(__file__).parent / "csvtu.png"
CSV_SKILLS = Path(__file__).parent / "placement_companies.csv"


def _get_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


logo_base64 = _get_base64(LOGO_PATH) if LOGO_PATH.exists() else ""


# ── Auth (uses shared get_conn + check_pw) ────────────────────────────────────
def _authenticate_student(university_id: str, password: str):
    try:
        conn   = get_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT university_id, name, branch, mobile_number, password "
            "FROM students WHERE university_id = %s",
            (university_id,),
        )
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        if not student:
            return None

        stored = student.get("password") or ""
        # bcrypt hashes always start with $2 (e.g. $2b$12$...). Anything else
        # means this row hasn't been migrated from plaintext yet — fall back
        # to a direct comparison so existing accounts still work, but treat
        # every successful bcrypt match as the normal path going forward.
        if stored.startswith("$2"):
            if not check_pw(password, stored):
                return None
        else:
            if stored != password:
                return None

        student.pop("password", None)
        return student
    except Error as e:
        st.error(f"Database error: {e}")
        return None


# ── Load placement_companies.csv ──────────────────────────────────────────────
def _load_placement_csv(path: Path):
    """
    Expected columns: Branch, Company Name, Skills Required, Tools Required
    Returns: {(BRANCH, company_name_lower): {skills: [], tools: []}}
    """
    mapping = {}
    try:
        if not path.exists():
            return mapping

        def _split(raw: str):
            parts = []
            for chunk in re.split(r"[;,/]", raw):
                t = re.sub(r"\s*\(.*?\)", "", chunk).strip().lower()
                if t:
                    parts.append(t)
            return parts

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                branch  = row.get("Branch", "").strip().upper()
                company = row.get("Company Name", "").strip().lower()
                tools   = _split(row.get("Tools Required", ""))
                skills  = _split(row.get("Skills Required", ""))
                mapping[(branch, company)] = {"tools": tools, "skills": skills}
    except Exception:
        pass
    return mapping


PLACEMENT_MAP = _load_placement_csv(CSV_SKILLS)


def _get_required(branch: str, company_name: str):
    """Return combined skill+tool list for a branch/company pair from CSV."""
    key   = (branch.upper().strip(), company_name.strip().lower())
    entry = PLACEMENT_MAP.get(key)
    if not entry:
        return []
    return entry["tools"] + entry["skills"]


def _compute_match(required: list, student_skills_text: str):
    """Return (match_pct, matched_list, missing_list)."""
    if not required or not student_skills_text:
        return 0, [], required
    user_terms = {
        t.strip()
        for t in re.split(r"[,;/|\s]+", student_skills_text.lower())
        if t.strip()
    }

    def _covered(term):
        return any(term == u or term in u or u in term for u in user_terms)

    matched = sorted([r for r in required if _covered(r)])
    missing = sorted([r for r in required if not _covered(r)])
    pct     = round(len(matched) / len(required) * 100) if required else 0
    return pct, matched, missing


# ── Free course suggestions ───────────────────────────────────────────────────
FREE_COURSES = {
    "python":            [{"title": "Python for Everybody",              "platform": "Coursera (Audit Free)",  "url": "https://www.coursera.org/specializations/python"}],
    "java":              [{"title": "Java Programming MOOC",             "platform": "University of Helsinki", "url": "https://java-programming.mooc.fi/"}],
    "sql":               [{"title": "SQL for Data Science",              "platform": "Coursera (Audit Free)",  "url": "https://www.coursera.org/learn/sql-for-data-science"}],
    "react":             [{"title": "React Official Tutorial",           "platform": "React Docs (Free)",      "url": "https://react.dev/learn"}],
    "javascript":        [{"title": "JS Algorithms & Data Structures",   "platform": "freeCodeCamp",           "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/"}],
    "docker":            [{"title": "Docker 101 Tutorial",               "platform": "Docker Official",        "url": "https://www.docker.com/101-tutorial/"}],
    "kubernetes":        [{"title": "Kubernetes Basics",                 "platform": "Kubernetes.io",          "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/"}],
    "aws":               [{"title": "AWS Cloud Practitioner",            "platform": "AWS Skill Builder",      "url": "https://explore.skillbuilder.aws/learn/course/134"}],
    "azure":             [{"title": "Azure Fundamentals AZ-900",         "platform": "Microsoft Learn",        "url": "https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/"}],
    "linux":             [{"title": "Linux Command Line Basics",         "platform": "Udacity (Free)",         "url": "https://www.udacity.com/course/linux-command-line-basics--ud595"}],
    "git":               [{"title": "Pro Git Book",                      "platform": "git-scm.com (Free)",     "url": "https://git-scm.com/book/en/v2"}],
    "machine learning":  [{"title": "ML Specialization",                 "platform": "Coursera (Audit Free)",  "url": "https://www.coursera.org/specializations/machine-learning-introduction"}],
    "deep learning":     [{"title": "Deep Learning Specialization",      "platform": "Coursera (Audit Free)",  "url": "https://www.coursera.org/specializations/deep-learning"}],
    "tensorflow":        [{"title": "TensorFlow Official Tutorials",     "platform": "TensorFlow.org",         "url": "https://www.tensorflow.org/tutorials"}],
    "pytorch":           [{"title": "PyTorch Official Tutorials",        "platform": "PyTorch.org",            "url": "https://pytorch.org/tutorials/"}],
    "pandas":            [{"title": "Pandas Getting Started",            "platform": "pandas.pydata.org",      "url": "https://pandas.pydata.org/docs/getting_started/"}],
    "data analysis":     [{"title": "Google Data Analytics",             "platform": "Coursera (Audit Free)",  "url": "https://www.coursera.org/professional-certificates/google-data-analytics"}],
    "cybersecurity":     [{"title": "Google Cybersecurity Certificate",  "platform": "Coursera (Audit Free)",  "url": "https://www.coursera.org/professional-certificates/google-cybersecurity"}],
    "devops":            [{"title": "DevOps Prerequisites Course",       "platform": "freeCodeCamp/YouTube",   "url": "https://www.youtube.com/watch?v=Wvf0mBNGjXY"}],
    "power bi":          [{"title": "Microsoft Power BI Learning",       "platform": "Microsoft Learn",        "url": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi"}],
    "tableau":           [{"title": "Tableau Public Free Training",      "platform": "Tableau",                "url": "https://www.tableau.com/learn/training"}],
    "html":              [{"title": "Responsive Web Design",             "platform": "freeCodeCamp",           "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/"}],
    "css":               [{"title": "CSS Full Course",                   "platform": "freeCodeCamp/YouTube",   "url": "https://www.youtube.com/watch?v=1Rs2ND1ryYc"}],
    "figma":             [{"title": "Figma for Beginners",               "platform": "Figma Official",         "url": "https://www.figma.com/resources/learn-design/"}],
    "git/github":        [{"title": "Git & GitHub Crash Course",         "platform": "freeCodeCamp/YouTube",   "url": "https://www.youtube.com/watch?v=RGOj5yH7evk"}],
    "c/c++":             [{"title": "C++ Tutorial for Beginners",        "platform": "freeCodeCamp/YouTube",   "url": "https://www.youtube.com/watch?v=vLnPwxZdW4Y"}],
    "matlab":            [{"title": "MATLAB Onramp",                     "platform": "MathWorks (Free)",       "url": "https://matlabacademy.mathworks.com/"}],
    "autocad":           [{"title": "AutoCAD Free Learning",             "platform": "Autodesk (Free)",        "url": "https://www.autodesk.com/certification/learn"}],
    "solidworks":        [{"title": "SolidWorks MySolidWorks",           "platform": "SolidWorks (Free Tier)", "url": "https://my.solidworks.com/"}],
    "plc":               [{"title": "PLC Programming Basics",            "platform": "RealPars (Free Tier)",   "url": "https://realpars.com/"}],
    "scada":             [{"title": "SCADA Introduction",                "platform": "RealPars (Free Tier)",   "url": "https://realpars.com/"}],
    "embedded":          [{"title": "Embedded Systems – Shape the World","platform": "edX – UT Austin",        "url": "https://www.edx.org/learn/embedded-systems/the-university-of-texas-at-austin-embedded-systems-shape-the-world-microcontroller-input-output"}],
    "verilog":           [{"title": "HDL Bits – Verilog Practice",       "platform": "HDLBits (Free)",         "url": "https://hdlbits.01xz.net/"}],
    "etap":              [{"title": "ETAP Learning Resources",           "platform": "ETAP Official (Free)",   "url": "https://etap.com/resources"}],
    "staad pro":         [{"title": "STAAD.Pro Tutorial Series",         "platform": "Bentley (Free Trial)",   "url": "https://www.bentley.com/software/staad-pro/"}],
    "ansys":             [{"title": "ANSYS Learning Hub (Free Tier)",    "platform": "ANSYS",                  "url": "https://www.ansys.com/academic"}],
    "excel":             [{"title": "Excel Skills for Business",         "platform": "Coursera (Audit Free)",  "url": "https://www.coursera.org/specializations/excel"}],
    "communication":     [{"title": "Communication Foundations",         "platform": "LinkedIn Learning",      "url": "https://www.linkedin.com/learning/communication-foundations"}],
    "project management":[{"title": "Google Project Management",         "platform": "Coursera (Audit Free)",  "url": "https://www.coursera.org/professional-certificates/google-project-management"}],
}

PLATFORM_COLORS = {
    "coursera": "#0056D2", "freecodecamp": "#0A0A23", "youtube": "#FF0000",
    "microsoft": "#00A4EF", "google": "#4285F4",      "mathworks": "#E16737",
    "autodesk": "#E86C00",  "mongodb": "#13AA52",     "tableau": "#E97627",
    "udacity": "#02B3E4",   "edx": "#02262B",          "aws": "#FF9900",
    "docker": "#2496ED",    "bentley": "#00519C",      "ansys": "#FFB71B",
    "default": "#3b82f6",
}


def _platform_color(p: str) -> str:
    pl = p.lower()
    for k, c in PLATFORM_COLORS.items():
        if k in pl:
            return c
    return PLATFORM_COLORS["default"]


def _course_for(term: str):
    if term in FREE_COURSES:
        return FREE_COURSES[term]
    for key in FREE_COURSES:
        if key in term or term in key:
            return FREE_COURSES[key]
    return []


# ── Company data ──────────────────────────────────────────────────────────────
COMPANIES = {
    "CSE": [
        {"name": "Nexvora Technologies",  "role": "Software Developer",       "package": "4.2 LPA", "location": "Pune"},
        {"name": "Bytecraft Solutions",   "role": "Backend Engineer",          "package": "3.8 LPA", "location": "Hyderabad"},
        {"name": "Infrabit Systems",      "role": "Full Stack Developer",      "package": "4.5 LPA", "location": "Bengaluru"},
        {"name": "Cloudpine Infotech",    "role": "Cloud Support Engineer",    "package": "3.6 LPA", "location": "Chennai"},
        {"name": "Pixelnode Labs",        "role": "Frontend Developer",        "package": "4.0 LPA", "location": "Noida"},
        {"name": "Stackware Pvt Ltd",     "role": "Python Developer",          "package": "3.9 LPA", "location": "Indore"},
        {"name": "Devforge IT",           "role": "Java Developer",            "package": "4.1 LPA", "location": "Bhopal"},
        {"name": "Netquill Systems",      "role": "Network Engineer",          "package": "3.5 LPA", "location": "Raipur"},
        {"name": "Codebridge India",      "role": "QA Engineer",               "package": "3.4 LPA", "location": "Nagpur"},
        {"name": "Datasync Technologies", "role": "Data Analyst",              "package": "4.3 LPA", "location": "Pune"},
        {"name": "Apexloop Software",     "role": "DevOps Engineer",           "package": "4.8 LPA", "location": "Bengaluru"},
        {"name": "Trigon Infotech",       "role": "Mobile App Developer",      "package": "4.0 LPA", "location": "Ahmedabad"},
        {"name": "Webvault Solutions",    "role": "UI/UX Developer",           "package": "3.7 LPA", "location": "Delhi"},
        {"name": "Zerobit Labs",          "role": "Cybersecurity Analyst",     "package": "5.0 LPA", "location": "Hyderabad"},
        {"name": "Linkcore Systems",      "role": "System Analyst",            "package": "3.8 LPA", "location": "Kolkata"},
        {"name": "Tasknode Pvt Ltd",      "role": "Software Tester",           "package": "3.3 LPA", "location": "Jaipur"},
        {"name": "Orbitline IT",          "role": "React Developer",           "package": "4.2 LPA", "location": "Mumbai"},
        {"name": "Gridstack India",       "role": "Database Administrator",    "package": "4.0 LPA", "location": "Chennai"},
        {"name": "Codehive Technologies", "role": "AI/ML Engineer",            "package": "5.5 LPA", "location": "Bengaluru"},
        {"name": "Streampath Solutions",  "role": "Tech Support Engineer",     "package": "3.2 LPA", "location": "Indore"},
    ],
    "ECE": [
        {"name": "Wavegen Electronics",   "role": "Embedded Systems Engineer",  "package": "4.0 LPA", "location": "Pune"},
        {"name": "Circuitnode Pvt Ltd",   "role": "PCB Design Engineer",        "package": "3.8 LPA", "location": "Bengaluru"},
        {"name": "Signalcraft Systems",   "role": "RF Engineer",                "package": "4.5 LPA", "location": "Hyderabad"},
        {"name": "Voltpeak Industries",   "role": "VLSI Design Engineer",       "package": "5.0 LPA", "location": "Chennai"},
        {"name": "Antennatech India",     "role": "Telecom Engineer",           "package": "3.9 LPA", "location": "Mumbai"},
        {"name": "Microlink Solutions",   "role": "IoT Developer",              "package": "4.2 LPA", "location": "Noida"},
        {"name": "Pulsegate Labs",        "role": "Hardware Engineer",          "package": "3.7 LPA", "location": "Raipur"},
        {"name": "Sensorix Technologies", "role": "Sensor Systems Engineer",    "package": "4.1 LPA", "location": "Indore"},
        {"name": "Broadband Nexus",       "role": "Network Planning Engineer",  "package": "3.6 LPA", "location": "Jaipur"},
        {"name": "Digitrend Systems",     "role": "Signal Processing Engineer", "package": "4.4 LPA", "location": "Delhi"},
        {"name": "Chipframe India",       "role": "Chip Design Analyst",        "package": "5.2 LPA", "location": "Bengaluru"},
        {"name": "Radiovox Pvt Ltd",      "role": "Communication Engineer",     "package": "3.8 LPA", "location": "Kolkata"},
        {"name": "Etherlogic Systems",    "role": "Firmware Developer",         "package": "4.3 LPA", "location": "Ahmedabad"},
        {"name": "Resonance Infotech",    "role": "Electronics Support Engg",   "package": "3.5 LPA", "location": "Nagpur"},
        {"name": "Datawave Labs",         "role": "Test Engineer",              "package": "3.4 LPA", "location": "Bhopal"},
        {"name": "Powerlink Electronics", "role": "Power Electronics Engg",     "package": "4.0 LPA", "location": "Pune"},
        {"name": "Navlink Systems",       "role": "Navigation Systems Engg",    "package": "4.6 LPA", "location": "Hyderabad"},
        {"name": "Tronix Pvt Ltd",        "role": "Production Engineer",        "package": "3.3 LPA", "location": "Raipur"},
        {"name": "Spectracom India",      "role": "Spectrum Analyst",           "package": "4.1 LPA", "location": "Chennai"},
        {"name": "Wiredge Technologies",  "role": "Circuit Design Engineer",    "package": "3.9 LPA", "location": "Indore"},
    ],
    "ME": [
        {"name": "Gearshift Industries",    "role": "Mechanical Design Engineer", "package": "3.9 LPA", "location": "Pune"},
        {"name": "Forgetech Pvt Ltd",       "role": "Production Engineer",        "package": "3.6 LPA", "location": "Raipur"},
        {"name": "Thermocore Systems",      "role": "Thermal Engineer",           "package": "4.0 LPA", "location": "Chennai"},
        {"name": "Axlepoint Manufacturing", "role": "CAD/CAM Engineer",           "package": "3.8 LPA", "location": "Indore"},
        {"name": "Driveline India",         "role": "Automobile Engineer",        "package": "4.2 LPA", "location": "Mumbai"},
        {"name": "Steelcraft Solutions",    "role": "Structural Engineer",        "package": "3.7 LPA", "location": "Nagpur"},
        {"name": "Fluid Dynamics Labs",     "role": "Hydraulics Engineer",        "package": "4.1 LPA", "location": "Hyderabad"},
        {"name": "Castronix Pvt Ltd",       "role": "Casting Process Engineer",   "package": "3.5 LPA", "location": "Bhopal"},
        {"name": "Turbovane Industries",    "role": "Turbine Engineer",           "package": "4.5 LPA", "location": "Bengaluru"},
        {"name": "Pressfit Systems",        "role": "Quality Control Engineer",   "package": "3.4 LPA", "location": "Ahmedabad"},
        {"name": "Moldtech India",          "role": "Tool & Die Engineer",        "package": "3.8 LPA", "location": "Pune"},
        {"name": "Weldpro Solutions",       "role": "Welding Engineer",           "package": "3.3 LPA", "location": "Raipur"},
        {"name": "Robocraft Labs",          "role": "Robotics Engineer",          "package": "5.0 LPA", "location": "Bengaluru"},
        {"name": "Nanofit Technologies",    "role": "Precision Engineer",         "package": "4.3 LPA", "location": "Chennai"},
        {"name": "Pipeflow Systems",        "role": "Piping Engineer",            "package": "3.9 LPA", "location": "Mumbai"},
        {"name": "Machinelink Pvt Ltd",     "role": "CNC Operator Engineer",      "package": "3.2 LPA", "location": "Indore"},
        {"name": "Heatshield India",        "role": "HVAC Engineer",              "package": "4.0 LPA", "location": "Delhi"},
        {"name": "Driveaxis Industries",    "role": "Plant Maintenance Engg",     "package": "3.6 LPA", "location": "Nagpur"},
        {"name": "Compressor Tech",         "role": "Compressor Engineer",        "package": "3.8 LPA", "location": "Jaipur"},
        {"name": "Alloyedge Pvt Ltd",       "role": "Materials Engineer",         "package": "4.1 LPA", "location": "Hyderabad"},
    ],
    "CE": [
        {"name": "Buildframe Constructions", "role": "Site Engineer",              "package": "3.6 LPA", "location": "Raipur"},
        {"name": "Concretech Pvt Ltd",       "role": "Structural Engineer",        "package": "4.0 LPA", "location": "Pune"},
        {"name": "Soilcraft Labs",           "role": "Geotechnical Engineer",      "package": "3.8 LPA", "location": "Bhopal"},
        {"name": "Bridgelink India",         "role": "Bridge Design Engineer",     "package": "4.2 LPA", "location": "Mumbai"},
        {"name": "Urbanplan Systems",        "role": "Urban Planner",              "package": "3.9 LPA", "location": "Delhi"},
        {"name": "Roadpave Solutions",       "role": "Highway Engineer",           "package": "3.7 LPA", "location": "Nagpur"},
        {"name": "Aquaflow Engineers",       "role": "Water Resources Engg",       "package": "4.1 LPA", "location": "Chennai"},
        {"name": "Terrasolid Pvt Ltd",       "role": "Foundation Engineer",        "package": "3.5 LPA", "location": "Indore"},
        {"name": "Canaltech India",          "role": "Irrigation Engineer",        "package": "3.4 LPA", "location": "Jaipur"},
        {"name": "Drainex Systems",          "role": "Sanitation Engineer",        "package": "3.3 LPA", "location": "Kolkata"},
        {"name": "Skyframe Builders",        "role": "High-Rise Structural Engg",  "package": "4.5 LPA", "location": "Bengaluru"},
        {"name": "Pavecraft Solutions",      "role": "Pavement Engineer",          "package": "3.6 LPA", "location": "Hyderabad"},
        {"name": "Greenzone Infra",          "role": "Environmental Engineer",     "package": "3.9 LPA", "location": "Pune"},
        {"name": "Draftline Consultants",    "role": "AutoCAD Designer",           "package": "3.2 LPA", "location": "Raipur"},
        {"name": "Tensiontech Pvt Ltd",      "role": "Pre-stressed Concrete Engg", "package": "4.0 LPA", "location": "Mumbai"},
        {"name": "Watershield India",        "role": "Waterproofing Engineer",     "package": "3.5 LPA", "location": "Delhi"},
        {"name": "Vaultcon Builders",        "role": "Construction Manager",       "package": "4.3 LPA", "location": "Ahmedabad"},
        {"name": "Geomap Solutions",         "role": "Survey Engineer",            "package": "3.7 LPA", "location": "Bhopal"},
        {"name": "Stormline Systems",        "role": "Drainage Engineer",          "package": "3.8 LPA", "location": "Nagpur"},
        {"name": "Pilecap Infra",            "role": "Pile Foundation Engineer",   "package": "4.1 LPA", "location": "Chennai"},
    ],
    "EE": [
        {"name": "Voltedge Power",      "role": "Electrical Design Engineer", "package": "4.0 LPA", "location": "Pune"},
        {"name": "Switchgear India",    "role": "Switchgear Engineer",        "package": "3.8 LPA", "location": "Hyderabad"},
        {"name": "Powernet Systems",    "role": "Power Systems Engineer",     "package": "4.3 LPA", "location": "Chennai"},
        {"name": "Gridvolt Pvt Ltd",    "role": "Grid Engineer",              "package": "4.5 LPA", "location": "Delhi"},
        {"name": "Illuminex Solutions", "role": "Lighting Design Engineer",   "package": "3.6 LPA", "location": "Bengaluru"},
        {"name": "Cabletek India",      "role": "Cable Engineer",             "package": "3.5 LPA", "location": "Mumbai"},
        {"name": "Motorworks Pvt Ltd",  "role": "Motor Design Engineer",      "package": "4.1 LPA", "location": "Indore"},
        {"name": "Substationix",        "role": "Substation Engineer",        "package": "4.2 LPA", "location": "Raipur"},
        {"name": "Transformix India",   "role": "Transformer Engineer",       "package": "3.9 LPA", "location": "Nagpur"},
        {"name": "Relaytech Systems",   "role": "Protection Engineer",        "package": "4.0 LPA", "location": "Ahmedabad"},
        {"name": "Solarmax Pvt Ltd",    "role": "Solar Energy Engineer",      "package": "4.6 LPA", "location": "Jaipur"},
        {"name": "Windgate Energy",     "role": "Wind Energy Engineer",       "package": "4.8 LPA", "location": "Pune"},
        {"name": "Loadflow Labs",       "role": "Load Flow Analyst",          "package": "3.7 LPA", "location": "Kolkata"},
        {"name": "Autovolt Systems",    "role": "Automation Engineer",        "package": "4.4 LPA", "location": "Bengaluru"},
        {"name": "Controllogic India",  "role": "PLC/SCADA Engineer",         "package": "4.3 LPA", "location": "Chennai"},
        {"name": "Earthlink Pvt Ltd",   "role": "Earthing Engineer",          "package": "3.4 LPA", "location": "Bhopal"},
        {"name": "Metering Solutions",  "role": "Energy Meter Engineer",      "package": "3.3 LPA", "location": "Indore"},
        {"name": "Capacitorx India",    "role": "Reactive Power Engineer",    "package": "3.8 LPA", "location": "Hyderabad"},
        {"name": "Panelcraft Systems",  "role": "Control Panel Engineer",     "package": "3.6 LPA", "location": "Raipur"},
        {"name": "Powerline Infra",     "role": "Transmission Line Engg",     "package": "4.0 LPA", "location": "Mumbai"},
    ],
}

DEFAULT_COMPANIES = [
    {"name": "Nexvora Technologies",     "role": "Graduate Trainee Engineer", "package": "3.5 LPA", "location": "Indore"},
    {"name": "Bytecraft Solutions",      "role": "Technical Support",         "package": "3.2 LPA", "location": "Bhopal"},
    {"name": "Infrabit Systems",         "role": "Operations Engineer",       "package": "3.8 LPA", "location": "Raipur"},
    {"name": "Cloudpine Infotech",       "role": "IT Support Engineer",       "package": "3.3 LPA", "location": "Pune"},
    {"name": "Trigon Infotech",          "role": "Project Trainee",           "package": "3.0 LPA", "location": "Nagpur"},
    {"name": "Stackware Pvt Ltd",        "role": "Junior Engineer",           "package": "3.4 LPA", "location": "Mumbai"},
    {"name": "Devforge IT",              "role": "System Engineer",           "package": "3.6 LPA", "location": "Delhi"},
    {"name": "Netquill Systems",         "role": "Technical Analyst",         "package": "3.5 LPA", "location": "Hyderabad"},
    {"name": "Apexloop Software",        "role": "Graduate Engineer Trainee", "package": "3.7 LPA", "location": "Chennai"},
    {"name": "Linkcore Systems",         "role": "Business Analyst",          "package": "3.8 LPA", "location": "Bengaluru"},
    {"name": "Tasknode Pvt Ltd",         "role": "Operations Analyst",        "package": "3.2 LPA", "location": "Ahmedabad"},
    {"name": "Orbitline IT",             "role": "ERP Support Engineer",      "package": "3.4 LPA", "location": "Kolkata"},
    {"name": "Gridstack India",          "role": "Field Engineer",            "package": "3.6 LPA", "location": "Jaipur"},
    {"name": "Codehive Technologies",    "role": "R&D Trainee",               "package": "4.0 LPA", "location": "Pune"},
    {"name": "Streampath Solutions",     "role": "Process Engineer",          "package": "3.3 LPA", "location": "Indore"},
    {"name": "Gearshift Industries",     "role": "Maintenance Engineer",      "package": "3.5 LPA", "location": "Raipur"},
    {"name": "Forgetech Pvt Ltd",        "role": "Quality Engineer",          "package": "3.4 LPA", "location": "Nagpur"},
    {"name": "Buildframe Constructions", "role": "Site Supervisor",           "package": "3.2 LPA", "location": "Bhopal"},
    {"name": "Voltedge Power",           "role": "Service Engineer",          "package": "3.7 LPA", "location": "Chennai"},
    {"name": "Robocraft Labs",           "role": "Automation Trainee",        "package": "4.2 LPA", "location": "Bengaluru"},
]


def get_companies_for_branch(branch: str):
    branch_upper = branch.upper().strip()
    for key in COMPANIES:
        if key in branch_upper or branch_upper in key:
            return COMPANIES[key]
    return DEFAULT_COMPANIES


# ── CSS (matches dashboard.py blue/white palette) ─────────────────────────────
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
    --a2:      #10b981;
    --a3:      #f59e0b;
    --a4:      #ef4444;
    --text:    #111827;
    --t2:      #6b7280;
    --muted:   #9ca3af;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: var(--bg); }
#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; }

/* ── HERO ── */
.uni-hero {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 16px; padding: 32px 44px;
    display: flex; align-items: center; gap: 28px; margin-bottom: 28px;
}
.uni-hero img {
    width: 96px; height: 96px; border-radius: 14px;
    background: var(--s2); padding: 6px; flex-shrink: 0;
    object-fit: contain; border: 1px solid var(--border);
}
.uni-hero-text h1 {
    font-size: 1.55rem; font-weight: 800; color: var(--text);
    margin: 0 0 6px 0; line-height: 1.2;
}
.uni-hero-text p  { font-size: 0.85rem; color: var(--t2); margin: 0 0 12px 0; }
.student-badge    { display: inline-flex; gap: 14px; flex-wrap: wrap; }
.student-badge span {
    background: var(--a-light); border: 1px solid var(--border);
    color: var(--accent); font-size: 0.74rem; font-weight: 600;
    padding: 5px 13px; border-radius: 20px;
}

/* ── SKILL INPUT BAR ── */
.skill-input-bar {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 16px 24px; margin-bottom: 20px;
}
.skill-input-bar .label {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--accent); margin-bottom: 8px;
}

/* ── SECTION HEADING ── */
.section-heading {
    font-size: 1.05rem; font-weight: 700; color: var(--text);
    margin: 8px 0 18px 0; padding-bottom: 10px;
    border-bottom: 2px solid var(--border);
}

/* ── COMPANY CARD ── */
.company-card {
    background: var(--surface); border-radius: 14px;
    border: 1px solid var(--border);
    padding: 18px 20px 14px 20px; transition: box-shadow 0.2s;
}
.company-card:hover { box-shadow: 0 8px 24px rgba(59,130,246,0.12); }
.company-name { font-size: 0.92rem; font-weight: 700; color: var(--text); margin: 0 0 6px 0; }
.company-role {
    font-size: 0.76rem; color: var(--accent); font-weight: 600;
    background: var(--a-light); display: inline-block;
    padding: 2px 10px; border-radius: 12px; margin-bottom: 10px;
}
.company-meta        { font-size: 0.75rem; color: var(--muted); margin: 3px 0; }
.company-meta strong { color: var(--t2); }

/* ── SKILL GAP PANEL ── */
.sgap-wrap {
    background: var(--s2); border: 1.5px solid var(--border);
    border-radius: 10px; padding: 14px 16px; margin-top: 12px;
}
.sgap-header {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--accent); margin-bottom: 10px;
}
.sgap-bar-wrap {
    background: #e7eaf3; border-radius: 4px;
    height: 7px; overflow: hidden; margin-bottom: 4px;
}
.sgap-bar-fill { height: 100%; border-radius: 4px; }
.sgap-pct      { font-size: 1.1rem; font-weight: 800; margin-bottom: 10px; }
.chip {
    display: inline-block; font-size: 0.7rem; font-weight: 600;
    padding: 2px 9px; border-radius: 14px; margin: 2px 3px 2px 0;
}
.chip-have { background: #edfaf4; color: #17864f; border: 1px solid #b8edcf; }
.chip-miss { background: #fef0f0; color: #d0312d; border: 1px solid #facacb; }
.sgap-sublabel {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; color: var(--muted); margin: 10px 0 5px;
}
.course-link {
    display: flex; align-items: center; gap: 9px;
    background: #fff; border: 1px solid var(--border);
    border-radius: 7px; padding: 7px 10px; margin-bottom: 5px;
    text-decoration: none;
}
.course-link:hover { border-color: var(--accent); }
.cdot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.ctitle { font-size: 0.72rem; font-weight: 600; color: var(--text); flex: 1; }
.cplat  { font-size: 0.65rem; color: var(--muted); }

/* ── BUTTONS ── */
div[data-testid="stButton"] button {
    background: var(--accent);
    color: #ffffff !important; border: none; border-radius: 8px;
    padding: 0.38rem 0; font-weight: 600; font-size: 0.8rem;
    width: 100%; margin-top: 10px; transition: opacity 0.2s ease;
}
div[data-testid="stButton"] button:hover { opacity: 0.88; }

/* ── LOGIN CARD ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface); border-radius: 16px;
    border: 1px solid var(--border); padding: 8px 6px;
}
.login-title { font-size: 1.15rem; font-weight: 600; color: var(--text); margin-bottom: 2px; }
.login-sub   { font-size: 0.8rem; color: var(--t2); margin-bottom: 20px; }
.stTextInput > label { font-size: 0.78rem; font-weight: 600; color: var(--t2); }
.stTextInput input {
    border-radius: 10px; border: 1.5px solid var(--border);
    padding: 10px 14px; background-color: var(--s2); color: var(--text);
}
.stTextInput input:focus {
    border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent);
}
div[data-testid="stFormSubmitButton"] button {
    width: 100%; background: var(--accent);
    color: #ffffff !important; border: none; border-radius: 10px;
    padding: 0.6rem 0; font-weight: 600; font-size: 0.92rem; margin-top: 6px;
}
.helper-row {
    display: flex; justify-content: flex-end;
    margin-top: -6px; margin-bottom: 6px; font-size: 0.78rem;
}
.helper-row a { color: var(--accent); text-decoration: none; font-weight: 500; }
.uni-login-header {
    display: flex; align-items: center; justify-content: center;
    gap: 14px; margin-bottom: 4px;
}
.uni-login-header img { width: 52px; height: 52px; }
.uni-login-name { font-size: 1.0rem; font-weight: 700; color: var(--text); line-height: 1.3; }
.uni-login-sub {
    text-align: center; color: var(--t2); font-size: 0.8rem;
    margin-top: 4px; margin-bottom: 24px; letter-spacing: 0.3px;
}
</style>
"""


# ── Skill gap panel renderer ──────────────────────────────────────────────────
def _render_skill_gap(branch: str, company_name: str, student_skills: str):
    required = _get_required(branch, company_name)
    if not required:
        return   # no CSV data for this company — skip silently

    pct, matched, missing = _compute_match(required, student_skills)

    if pct >= 60:
        bar_color = pct_color = "#17864f"
    elif pct >= 30:
        bar_color = pct_color = "#e97627"
    else:
        bar_color = pct_color = "#d0312d"

    matched_chips = "".join(f'<span class="chip chip-have">{s}</span>' for s in matched)
    missing_chips = "".join(f'<span class="chip chip-miss">{s}</span>' for s in missing)

    courses_html = ""
    shown = 0
    for term in missing:
        if shown >= 4:
            break
        for course in _course_for(term)[:1]:
            dot = _platform_color(course["platform"])
            courses_html += f"""
<a href="{course['url']}" target="_blank" class="course-link">
  <div class="cdot" style="background:{dot};"></div>
  <div>
    <div class="ctitle">🎓 {course['title']}
      <span style="font-size:0.62rem;color:#9ca3af;font-weight:400;">— {term.title()}</span>
    </div>
    <div class="cplat">📌 {course['platform']}</div>
  </div>
</a>"""
            shown += 1

    matched_block = f"""
<div class="sgap-sublabel">✅ Skills You Have ({len(matched)} / {len(required)})</div>
<div style="margin-bottom:8px;">{matched_chips}</div>
""" if matched else ""

    if missing:
        missing_block = f"""
<div class="sgap-sublabel">❗ Skills to Gain ({len(missing)} / {len(required)})</div>
<div style="margin-bottom:10px;">{missing_chips}</div>
{'<div class="sgap-sublabel">🆓 Free Courses</div>' + courses_html if courses_html else ''}
"""
    else:
        missing_block = (
            '<div style="font-size:0.78rem;color:#17864f;font-weight:700;margin-top:6px;">'
            '🎉 Your profile covers all required skills!</div>'
        )

    st.markdown(f"""
<div class="sgap-wrap">
  <div class="sgap-header">🧩 Skill Match</div>
  <div class="sgap-bar-wrap">
    <div class="sgap-bar-fill" style="width:{pct}%;background:{bar_color};"></div>
  </div>
  <div class="sgap-pct" style="color:{pct_color};">{pct}% Match</div>
  {matched_block}
  {missing_block}
</div>
""", unsafe_allow_html=True)


# ── Main entry point (called from app.py) ─────────────────────────────────────
def render_csvtu():
    st.markdown(_CSS, unsafe_allow_html=True)
    back_to_dashboard()   # highlights correct nav item in shared sidebar

    # ── Session state defaults ─────────────────────────────────────────────
    if "csvtu_logged_in" not in st.session_state:
        st.session_state.csvtu_logged_in = False
    if "csvtu_student" not in st.session_state:
        st.session_state.csvtu_student = None
    if "csvtu_applied" not in st.session_state:
        st.session_state.csvtu_applied = set()
    if "csvtu_student_skills" not in st.session_state:
        st.session_state.csvtu_student_skills = ""

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD — shown after login
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.csvtu_logged_in and st.session_state.csvtu_student:
        student   = st.session_state.csvtu_student
        companies = get_companies_for_branch(student["branch"])

        img_tag = (
            f'<img src="data:image/png;base64,{logo_base64}" />'
            if logo_base64 else "🎓"
        )
        st.markdown(f"""
        <div class="uni-hero">
            {img_tag}
            <div class="uni-hero-text">
                <h1>Chhattisgarh Swami Vivekanand Technical University</h1>
                <p>BHILAI, CHHATTISGARH &nbsp;|&nbsp; PLACEMENT PORTAL</p>
                <div class="student-badge">
                    <span>👤 {student['name']}</span>
                    <span>🎓 {student['branch']}</span>
                    <span>🪪 {student['university_id']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Skills input bar ──────────────────────────────────────────────
        st.markdown("""
        <div class="skill-input-bar">
          <div class="label">🎯 Enter your skills for Skill Gap Analysis</div>
        </div>
        """, unsafe_allow_html=True)

        skills_col, _ = st.columns([3, 1])
        with skills_col:
            entered = st.text_input(
                "Your Skills & Tools",
                value=st.session_state.csvtu_student_skills,
                placeholder="e.g. Python, SQL, Django, Git, Docker, React…",
                key="csvtu_skills_input",
                label_visibility="collapsed",
            )
        if entered != st.session_state.csvtu_student_skills:
            st.session_state.csvtu_student_skills = entered
            st.rerun()

        student_skills = st.session_state.csvtu_student_skills

        # ── Header row with Logout ────────────────────────────────────────
        col_head, col_logout = st.columns([6, 1])
        with col_head:
            st.markdown(
                f'<div class="section-heading">🏢 Companies Visiting for '
                f'{student["branch"]} — {len(companies)} Opportunities</div>',
                unsafe_allow_html=True,
            )
        with col_logout:
            if st.button("Logout", key="csvtu_logout"):
                st.session_state.csvtu_logged_in      = False
                st.session_state.csvtu_student        = None
                st.session_state.csvtu_applied        = set()
                st.session_state.csvtu_student_skills = ""
                st.rerun()

        # ── Company cards — 2 per row so skill gap fits comfortably ──────
        for row_start in range(0, len(companies), 2):
            cols = st.columns(2)
            for col_idx, col in enumerate(cols):
                company_idx = row_start + col_idx
                if company_idx >= len(companies):
                    break
                c = companies[company_idx]
                with col:
                    st.markdown(f"""
                    <div class="company-card">
                        <div class="company-name">{c['name']}</div>
                        <div class="company-role">{c['role']}</div>
                        <div class="company-meta">💰 <strong>Package:</strong> {c['package']}</div>
                        <div class="company-meta">📍 <strong>Location:</strong> {c['location']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    already   = company_idx in st.session_state.csvtu_applied
                    btn_label = "✅ Applied" if already else "Apply Now"
                    if st.button(btn_label, key=f"csvtu_apply_{company_idx}", disabled=already):
                        st.session_state.csvtu_applied.add(company_idx)
                        st.toast(f"Applied to {c['name']} successfully!", icon="🎉")
                        st.rerun()

                    # Skill gap — only when student has typed something
                    if student_skills.strip():
                        _render_skill_gap(student["branch"], c["name"], student_skills)
                    else:
                        st.markdown(
                            '<div style="font-size:0.72rem;color:#9ca3af;margin-top:8px;">'
                            '💡 Enter your skills above to see match %</div>',
                            unsafe_allow_html=True,
                        )

        # ── Applied count ─────────────────────────────────────────────────
        if st.session_state.csvtu_applied:
            st.markdown(f"""
            <div style="margin-top:28px;text-align:center;color:var(--t2);font-size:0.82rem;">
                ✅ You have applied to <strong>{len(st.session_state.csvtu_applied)}</strong>
                out of {len(companies)} companies listed for your branch.
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # LOGIN PAGE — shown before login
    # ══════════════════════════════════════════════════════════════════════════
    else:
        _, center, _ = st.columns([1, 1.4, 1])
        with center:
            logo_img = (
                f'<img src="data:image/png;base64,{logo_base64}" />'
                if logo_base64 else '<span style="font-size:2.2rem;">🎓</span>'
            )
            st.markdown(f"""
            <div class="uni-login-header">
                {logo_img}
                <div class="uni-login-name">
                    Chhattisgarh Swami Vivekanand<br>Technical University
                </div>
            </div>
            <div class="uni-login-sub">BHILAI, CHHATTISGARH</div>
            """, unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown('<div class="login-title">Student Login</div>',
                            unsafe_allow_html=True)
                st.markdown(
                    '<div class="login-sub">Enter your University ID and password to continue</div>',
                    unsafe_allow_html=True,
                )

                with st.form("csvtu_login_form", clear_on_submit=False):
                    university_id = st.text_input(
                        "University ID",
                        placeholder="Enter 12-digit University ID",
                        max_chars=12,
                    )
                    password = st.text_input(
                        "Password", type="password",
                        placeholder="Enter your password",
                    )
                    st.markdown(
                        '<div class="helper-row"><a href="#">Forgot password?</a></div>',
                        unsafe_allow_html=True,
                    )
                    submitted = st.form_submit_button("Login")

                    if submitted:
                        if not university_id or not password:
                            st.error("Please enter both your University ID and Password.")
                        elif not university_id.strip().isdigit() or len(university_id.strip()) != 12:
                            st.error("University ID must be exactly 12 digits (numbers only).")
                        else:
                            with st.spinner("Verifying credentials…"):
                                student = _authenticate_student(
                                    university_id.strip(), password
                                )
                            if student:
                                st.session_state.csvtu_logged_in = True
                                st.session_state.csvtu_student   = student
                                st.rerun()
                            else:
                                st.error(
                                    "Invalid University ID or password. "
                                    "Please check your credentials and try again."
                                )