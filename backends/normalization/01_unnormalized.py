"""
Unnormalized Form (0NF)
=======================
Problems demonstrated:
  1. Multi-valued attributes — courses and grades are comma-separated strings,
     not individual values. SQL cannot directly filter or join on them.
  2. Update anomaly — changing a course name means hunting for it inside a text cell.
  3. No clear primary key — the same student can appear on multiple rows.

Domain: University course registration.
"""

import db


SETUP = """
DROP TABLE IF EXISTS unnorm_registration;

CREATE TABLE unnorm_registration (
    student_id    INT,
    student_name  TEXT,
    student_email TEXT,
    courses       TEXT,  -- 'CS101, MATH101, ENG201'  (NOT atomic)
    grades        TEXT   -- 'A, B+, C'                (NOT atomic, order matches courses)
);
"""

SEED = """
INSERT INTO unnorm_registration VALUES
    (1, 'Alice Smith',  'alice@uni.edu',  'CS101, MATH101',        'A, B+'),
    (2, 'Bob Jones',    'bob@uni.edu',    'CS101, ENG201, BIO301', 'B, A-, A'),
    (3, 'Carol White',  'carol@uni.edu',  'MATH101',               'A+'),
    (1, 'Alice Smith',  'alice@uni.edu',  'BIO301',                'B');  -- Alice split across rows
"""


def main():
    with db.cursor() as cur:
        cur.execute(SETUP)
        cur.execute(SEED)

        print("=" * 60)
        print("UNNORMALIZED FORM (0NF)")
        print("=" * 60)

        print("\n--- Raw table ---")
        db.print_table(
            cur,
            "SELECT * FROM unnorm_registration ORDER BY student_id",
            ["student_id", "student_name", "student_email", "courses", "grades"],
        )

        print("PROBLEM 1 — Multi-valued attributes")
        print('  Goal: find all students enrolled in CS101.')
        print('  We have to use LIKE, which is fragile and cannot use an index:')
        print()
        db.print_table(
            cur,
            "SELECT student_id, student_name, courses FROM unnorm_registration"
            "  WHERE courses LIKE '%CS101%'",
            ["student_id", "student_name", "courses"],
        )

        print("PROBLEM 2 — Update anomaly")
        print("  Renaming 'CS101' to 'Intro to CS' requires a text replacement")
        print("  inside a cell — and it breaks if spacing varies:")
        print("    UPDATE unnorm_registration")
        print("      SET courses = REPLACE(courses, 'CS101', 'Intro to CS')")
        print()

        print("PROBLEM 3 — No reliable primary key")
        print("  Alice (student_id=1) appears on TWO rows (courses split across rows).")
        db.print_table(
            cur,
            "SELECT student_id, student_name, courses FROM unnorm_registration"
            "  WHERE student_id = 1",
            ["student_id", "student_name", "courses"],
        )

        print("Fix: move to 1NF — see 02_1nf.py")


if __name__ == "__main__":
    main()
