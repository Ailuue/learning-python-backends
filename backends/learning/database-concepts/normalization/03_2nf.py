"""
Second Normal Form (2NF)
========================
Rules satisfied:
  - All 1NF rules.
  - No partial dependencies — every non-key column depends on the WHOLE primary key,
    not just part of it.

How we got here:
  - Moved student_name / student_email into a dedicated students table (PK: student_id).
  - Moved course_name / instructor / instructor_dept into a courses table (PK: course_id).
  - enrollments holds only what truly needs both halves of the key: the grade.

Problem that remains (leads to 3NF):
  Transitive dependency in the courses table:
      course_id  -->  instructor  -->  instructor_dept

  instructor_dept does NOT depend directly on course_id; it depends on instructor.
  If Dr. Patel moves to a new department, every course they teach must be updated.
"""

import db


SETUP = """
DROP TABLE IF EXISTS nf2_enrollments;
DROP TABLE IF EXISTS nf2_courses;
DROP TABLE IF EXISTS nf2_students;

CREATE TABLE nf2_students (
    student_id    INT  PRIMARY KEY,
    student_name  TEXT NOT NULL,
    student_email TEXT NOT NULL
);

CREATE TABLE nf2_courses (
    course_id       VARCHAR(10) PRIMARY KEY,
    course_name     TEXT NOT NULL,
    instructor      TEXT NOT NULL,
    instructor_dept TEXT NOT NULL   -- transitive dep: course_id -> instructor -> dept
);

CREATE TABLE nf2_enrollments (
    student_id INT         REFERENCES nf2_students,
    course_id  VARCHAR(10) REFERENCES nf2_courses,
    grade      CHAR(2),
    PRIMARY KEY (student_id, course_id)
);
"""

SEED = """
INSERT INTO nf2_students VALUES
    (1, 'Alice Smith', 'alice@uni.edu'),
    (2, 'Bob Jones',   'bob@uni.edu'),
    (3, 'Carol White', 'carol@uni.edu');

INSERT INTO nf2_courses VALUES
    ('CS101',   'Intro to CS',  'Dr. Patel',  'Computer Science'),
    ('CS201',   'Data Structs', 'Dr. Patel',  'Computer Science'),  -- Dr. Patel again
    ('MATH101', 'Calculus I',   'Dr. Lee',    'Mathematics'),
    ('ENG201',  'Tech Writing', 'Dr. Kim',    'English'),
    ('BIO301',  'Cell Biology', 'Dr. Nguyen', 'Biology');

INSERT INTO nf2_enrollments VALUES
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
        print("SECOND NORMAL FORM (2NF)")
        print("=" * 60)

        print("\n--- nf2_students ---")
        db.print_table(
            cur,
            "SELECT * FROM nf2_students ORDER BY student_id",
            ["student_id", "student_name", "student_email"],
        )

        print("--- nf2_courses ---")
        db.print_table(
            cur,
            "SELECT * FROM nf2_courses ORDER BY course_id",
            ["course_id", "course_name", "instructor", "instructor_dept"],
        )

        print("--- nf2_enrollments ---")
        db.print_table(
            cur,
            "SELECT * FROM nf2_enrollments ORDER BY student_id, course_id",
            ["student_id", "course_id", "grade"],
        )

        print("IMPROVEMENT over 1NF")
        print("  Alice's email lives in exactly one row — one update, done:")
        print("    UPDATE nf2_students SET student_email = 'alice.new@uni.edu'")
        print("      WHERE student_id = 1;\n")
        print("  Carol can be deleted from enrollments without losing her contact info.\n")

        print("PROBLEM — Transitive dependency in nf2_courses")
        print("  Dr. Patel teaches two courses. instructor_dept is stored twice:")
        db.print_table(
            cur,
            "SELECT course_id, instructor, instructor_dept"
            "  FROM nf2_courses WHERE instructor = 'Dr. Patel'",
            ["course_id", "instructor", "instructor_dept"],
        )
        print("  If Dr. Patel transfers to 'Software Engineering', both rows must change.")
        print("  Miss one and the data becomes inconsistent.\n")

        print("  Dependency chain: course_id -> instructor -> instructor_dept")
        print("  instructor_dept does not depend directly on course_id.")
        print("Fix: extract instructors into their own table — see 04_3nf.py")


if __name__ == "__main__":
    main()
