"""
migrate_student_passwords.py — run this ONCE to convert the students table
from plaintext passwords to bcrypt hashes.

Usage:
    python migrate_student_passwords.py

Safe to re-run: rows already hashed (start with $2) are skipped automatically.
"""
from db   import get_conn
from auth import hash_pw


def migrate():
    conn = get_conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT university_id, password FROM students")
    rows = cur.fetchall()

    updated, skipped = 0, 0
    for row in rows:
        pw = row.get("password") or ""
        if pw.startswith("$2"):
            skipped += 1
            continue
        new_hash = hash_pw(pw)
        update_cur = conn.cursor()
        update_cur.execute(
            "UPDATE students SET password=%s WHERE university_id=%s",
            (new_hash, row["university_id"]),
        )
        update_cur.close()
        updated += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Done. Hashed {updated} row(s), skipped {skipped} already-hashed row(s).")


if __name__ == "__main__":
    migrate()