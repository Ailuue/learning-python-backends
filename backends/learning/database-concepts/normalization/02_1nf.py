"""
First Normal Form (1NF)
=======================
Rules satisfied:
  - Every column holds a single (atomic) value.
  - Every row is uniquely identified by a primary key: (student_id, course_id).

Problems that remain (lead to 2NF):
  1. Partial dependencies — student_name/student_email depend only on student_id,
     not on the full composite key. Same for course_name/instructor/instructor_dept.
  2. Update anomaly   — changing Alice's email requires updating every row where
     student_id = 1, not just one place.
  3. Deletion anomaly — deleting Carol's only enrollment also destroys her contact info.
  4. Insertion anomaly — you cannot add a new course until at least one student enrolls.
"""

import db


SETUP = """
DROP TABLE IF EXISTS nf1_registration;

CREATE TABLE nf1_registration (
    student_id      INT,
    student_name    TEXT,            -- partial dep: depends only on student_id
    student_email   TEXT,            -- partial dep: depends only on student_id
    course_id       VARCHAR(10),
    course_name     TEXT,            -- partial dep: depends only on course_id
    instructor      TEXT,            -- partial dep: depends only on course_id
    instructor_dept TEXT,            -- transitive dep (via instructor, see 3NF)
    grade           CHAR(2),
    PRIMARY KEY (student_id, course_id)
);
"""

SEED = """
INSERT INTO nf1_registration VALUES
    (1, 'Alice Smith', 'alice@uni.edu', 'CS101',   'Intro to CS',   'Dr. Patel',  'Computer Science', 'A'),
    (1, 'Alice Smith', 'alice@uni.edu', 'MATH101', 'Calculus I',    'Dr. Lee',    'Mathematics',      'B+'),
    (1, 'Alice Smith', 'alice@uni.edu', 'BIO301',  'Cell Biology',  'Dr. Nguyen', 'Biology',          'B'),
    (2, 'Bob Jones',   'bob@uni.edu',   'CS101',   'Intro to CS',   'Dr. Patel',  'Computer Science', 'B'),
    (2, 'Bob Jones',   'bob@uni.edu',   'ENG201',  'Tech Writing',  'Dr. Kim',    'English',          'A-'),
    (3, 'Carol White', 'carol@uni.edu', 'MATH101', 'Calculus I',    'Dr. Lee',    'Mathematics',      'A+');
"""


def main():
    with db.cursor() as cur:
        cur.execute(SETUP)
        cur.execute(SEED)

        print("=" * 60)
        print("FIRST NORMAL FORM (1NF)")
        print("=" * 60)

        print("\n--- Table (PK: student_id + course_id) ---")
        db.print_table(
            cur,
            "SELECT * FROM nf1_registration ORDER BY student_id, course_id",
            ["student_id", "student_name", "student_email",
             "course_id", "course_name", "instructor", "instructor_dept", "grade"],
        )

        print("IMPROVEMENT over 0NF")
        print("  Finding all students in CS101 is now a clean equality filter:")
        db.print_table(
            cur,
            "SELECT student_id, student_name, grade FROM nf1_registration"
            "  WHERE course_id = 'CS101'",
            ["student_id", "student_name", "grade"],
        )

        print("PROBLEM 1 — Partial dependency / update anomaly")
        print("  Alice's email is stored 3 times (once per course).")
        print("  Changing it requires updating every row where student_id = 1:")
        print("    UPDATE nf1_registration")
        print("      SET student_email = 'alice.new@uni.edu'")
        print("      WHERE student_id = 1;   -- 3 rows touched for one logical change")
        print()

        print("PROBLEM 2 — Deletion anomaly")
        print("  If we remove Carol's only enrollment, her contact info disappears entirely:")
        db.print_table(
            cur,
            "SELECT student_id, student_name, student_email, course_id"
            "  FROM nf1_registration WHERE student_id = 3",
            ["student_id", "student_name", "student_email", "course_id"],
        )
        print("  DELETE FROM nf1_registration WHERE student_id = 3 AND course_id = 'MATH101'")
        print("  => Carol no longer exists in the database at all.\n")

        print("PROBLEM 3 — Insertion anomaly")
        print("  A new course 'PHY401' cannot be recorded until a student enrolls,")
        print("  because course_id is part of the primary key and cannot be NULL.\n")

        print("Root cause: student_name/email depend only on student_id (partial dependency).")
        print("            course_name/instructor depend only on course_id (partial dependency).")
        print("Fix: decompose into separate tables — see 03_2nf.py")


if __name__ == "__main__":
    main()
