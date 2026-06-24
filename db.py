import os
import mysql.connector
import streamlit as st


def get_conn():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
    )


def test_conn():
    try:
        c = get_conn()
        c.close()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)


def load_full_profile(user_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()

    cur.execute("SELECT * FROM education WHERE user_id=%s ORDER BY year_to DESC", (user_id,))
    edu = cur.fetchall()

    cur.execute("SELECT * FROM experience WHERE user_id=%s", (user_id,))
    exp = cur.fetchall()

    cur.execute("SELECT * FROM projects WHERE user_id=%s", (user_id,))
    proj = cur.fetchall()

    cur.execute("SELECT * FROM certifications WHERE user_id=%s", (user_id,))
    certs = cur.fetchall()

    cur.execute("SELECT * FROM achievements WHERE user_id=%s", (user_id,))
    ach = cur.fetchall()

    conn.close()

    st.session_state.profile = {
        "user": user, "education": edu, "experience": exp,
        "projects": proj,
        "certifications": certs, "achievements": ach,
        "loaded": True,
    }


def save_onboarding(user_id, personal, education_list, experience_list,
                     projects_list, certs_list, achievements_list):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users SET
            dob=%s, gender=%s, city=%s, state=%s,
            linkedin_url=%s, github_url=%s,
            target_role=%s, experience_level=%s,
            profile_completed=TRUE
        WHERE user_id=%s
    """, (personal.get("dob"), personal.get("gender"),
          personal.get("city"), personal.get("state"),
          personal.get("linkedin"), personal.get("github"),
          personal.get("target_role"), personal.get("exp_level"),
          user_id))

    for tbl in ["education", "experience", "projects", "certifications", "achievements"]:
        cur.execute(f"DELETE FROM {tbl} WHERE user_id=%s", (user_id,))

    for e in education_list:
        cur.execute("""INSERT INTO education
            (user_id,degree,institution,year_from,year_to,score,score_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (user_id, e.get("degree"), e.get("institution"),
             e.get("year_from"), e.get("year_to"),
             e.get("score"), e.get("score_type")))

    for e in experience_list:
        cur.execute("""INSERT INTO experience
            (user_id,company,role,duration,exp_type)
            VALUES (%s,%s,%s,%s,%s)""",
            (user_id, e.get("company"), e.get("role"),
             e.get("duration"), e.get("exp_type")))

    for p in projects_list:
        cur.execute("""INSERT INTO projects
            (user_id,title,tech_stack,description,github_url,live_url)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (user_id, p.get("title"), p.get("tech_stack"), p.get("description"),
             p.get("github_url"), p.get("live_url")))

    for c in certs_list:
        cur.execute("""INSERT INTO certifications
            (user_id,name,issuer,issue_year,credential_id,verify_url)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (user_id, c.get("name"), c.get("issuer"), c.get("year"),
             c.get("credential_id"), c.get("verify_url")))

    for a in achievements_list:
        cur.execute("INSERT INTO achievements (user_id,title,description,year) VALUES (%s,%s,%s,%s)",
                     (user_id, a.get("title"), a.get("description"), a.get("year")))

    conn.commit()
    conn.close()