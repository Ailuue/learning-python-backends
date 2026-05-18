"""
Third Normal Form (3NF)
=======================
Rules satisfied:
  - All 2NF rules.
  - No transitive dependencies — every non-key column depends DIRECTLY on the
    primary key, not on another non-key column.

How we got here:
  - Extracted instructors into their own table (PK: instructor_id).
  - courses now references instructor_id; instructor_dept lives only in instructors.

For most real-world applications 3NF is the target. The data is clean:
  - One fact lives in exactly one place.
  - Any update touches exactly one row.
  - No anomalies remain in this domain.

The remaining normal form (BCNF) only matters when there are multiple overlapping
candidate keys — a situation that doesn't arise here. See 05_bcnf.py.
"""

import db


SETUP = """
DROP TABLE IF EXISTS nf3_enrollments;
DROP TABLE IF EXISTS nf3_courses;
DROP TABLE IF EXISTS nf3_instructors;
DROP TABLE IF EXISTS nf3_students;

CREATE TABLE nf3_students (
    student_id    INT  PRIMARY KEY,
    student_name  TEXT NOT NULL,
    student_email TEXT NOT NULL
);

CREATE TABLE nf3_instructors (
    instructor_id   SERIAL PRIMARY KEY,
    instructor_name TEXT NOT NULL,
    instructor_dept TEXT NOT NULL
);

CREATE TABLE nf3_courses (
    course_id     VARCHAR(10) PRIMARY KEY,
    course_name   TEXT NOT NULL,
    instructor_id INT  NOT NULL REFERENCES nf3_instructors
);

CREATE TABLE nf3_enrollments (
    student_id INT         REFERENCES nf3_students,
    course_id  VARCHAR(10) REFERENCES nf3_courses,
    grade      CHAR(2),
    PRIMARY KEY (student_id, course_id)
);
"""

SEED = """
INSERT INTO nf3_students VALUES
    (1, 'Alice Smith', 'alice@uni.edu'),
    (2, 'Bob Jones',   'bob@uni.edu'),
    (3, 'Carol White', 'carol@uni.edu');

INSERT INTO nf3_instructors (instructor_name, instructor_dept) VALUES
    ('Dr. Patel',  'Computer Science'),
    ('Dr. Lee',    'Mathematics'),
    ('Dr. Kim',    'English'),
    ('Dr. Nguyen', 'Biology');

INSERT INTO nf3_courses VALUES
    ('CS101',   'Intro to CS',  1),
    ('CS201',   'Data Structs', 1),
    ('MATH101', 'Calculus I',   2),
    ('ENG201',  'Tech Writing', 3),
    ('BIO301',  'Cell Biology', 4);

INSERT INTO nf3_enrollments VALUES
    (1, 'CS101',   'A'),
    (1, 'MATH101', 'B+'),
    (1, 'BIO301',  'B'),
    (2, 'CS101',   'B'),
    (2, 'ENG201',  'A-'),
    (3, 'MATH101', 'A+');
"""


def main():
    with db.cursor() as cur:
        cur.execute(SETUP)
        cur.execute(SEED)

        print("=" * 60)
        print("THIRD NORMAL FORM (3NF)")
        print("=" * 60)

        print("\n--- nf3_students ---")
        db.print_table(
            cur,
            "SELECT * FROM nf3_students ORDER BY student_id",
            ["student_id", "student_name", "student_email"],
        )

        print("--- nf3_instructors ---")
        db.print_table(
            cur,
            "SELECT * FROM nf3_instructors ORDER BY instructor_id",
            ["instructor_id", "instructor_name", "instructor_dept"],
        )

        print("--- nf3_courses ---")
        db.print_table(
            cur,
            "SELECT * FROM nf3_courses ORDER BY course_id",
            ["course_id", "course_name", "instructor_id"],
        )

        print("--- nf3_enrollments ---")
        db.print_table(
            cur,
            "SELECT * FROM nf3_enrollments ORDER BY student_id, course_id",
            ["student_id", "course_id", "grade"],
        )

        print("IMPROVEMENT over 2NF")
        print("  Dr. Patel transfers to 'Software Engineering'.")
        print("  Exactly ONE row changes, regardless of how many courses they teach:\n")
        print("    UPDATE nf3_instructors")
        print("      SET instructor_dept = 'Software Engineering'")
        print("      WHERE instructor_id = 1;\n")

        print("--- Full enrolment report (JOIN across all four tables) ---")
        db.print_table(
            cur,
            """
            SELECT
                s.student_name,
                c.course_name,
                i.instructor_name,
                i.instructor_dept,
                e.grade
            FROM nf3_enrollments e
            JOIN nf3_students    s ON s.student_id    = e.student_id
            JOIN nf3_courses     c ON c.course_id     = e.course_id
            JOIN nf3_instructors i ON i.instructor_id = c.instructor_id
            ORDER BY s.student_name, c.course_name
            """,
            ["student", "course", "instructor", "department", "grade"],
        )

        print("Every non-key column now depends directly and only on its table's primary key.")
        print("For most production schemas, 3NF is the right stopping point.\n")
        print("When does 3NF fall short? When there are multiple overlapping candidate keys.")
        print("See 05_bcnf.py for that scenario.")


if __name__ == "__main__":
    main()
