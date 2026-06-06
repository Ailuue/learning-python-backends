"""
Boyce-Codd Normal Form (BCNF)
==============================
Rule: For every non-trivial functional dependency  X --> Y,
      X must be a superkey (able to uniquely identify every row).

3NF has a small loophole: it allows X --> Y where X is NOT a superkey,
as long as Y is part of some candidate key. BCNF closes that loophole.

Scenario: student academic advisors
  - Each student has exactly one advisor per subject.
  - Each advisor advises only one subject.

  Table: student_advisors(student_id, subject, advisor_id)

  Functional dependencies:
    (student_id, subject)  -->  advisor_id    [a student + subject maps to one advisor]
    (student_id, advisor_id) -->  subject      [an advisor covers one subject, so this follows]
    advisor_id             -->  subject        [each advisor handles only one subject]

  Candidate keys: (student_id, subject)  and  (student_id, advisor_id)

  Is this in 3NF?  YES — in  advisor_id --> subject, 'subject' is a prime attribute
                   (part of the candidate key (student_id, subject)), so 3NF's loophole applies.

  Is this in BCNF? NO  — advisor_id --> subject, but advisor_id alone is NOT a superkey.

  Anomaly: if advisor A1 is reassigned from 'Maths' to 'Physics', every row containing
  A1 must change. Miss one and the database becomes inconsistent.

BCNF decomposition:
  advisor_subjects  (advisor_id, subject)         -- captures: advisor_id --> subject
  student_advisors  (student_id, advisor_id)       -- captures enrollment
"""

import db


SETUP_VIOLATION = """
DROP TABLE IF EXISTS bcnf_student_advisors_3nf;

CREATE TABLE bcnf_student_advisors_3nf (
    student_id INT,
    subject    TEXT,
    advisor_id INT,
    PRIMARY KEY (student_id, subject)
    -- Second candidate key: (student_id, advisor_id) — not declared but exists logically.
    -- BCNF violation: advisor_id --> subject, yet advisor_id is not a superkey.
);
"""

SEED_VIOLATION = """
INSERT INTO bcnf_student_advisors_3nf VALUES
    (1, 'Mathematics', 10),
    (1, 'Physics',     20),
    (2, 'Mathematics', 10),   -- advisor 10 appears again for Mathematics
    (2, 'Chemistry',   30),
    (3, 'Physics',     20);   -- advisor 20 appears again for Physics
"""

SETUP_BCNF = """
DROP TABLE IF EXISTS bcnf_student_advisors;
DROP TABLE IF EXISTS bcnf_advisor_subjects;

CREATE TABLE bcnf_advisor_subjects (
    advisor_id INT  PRIMARY KEY,
    subject    TEXT NOT NULL
    -- advisor_id --> subject is now captured with advisor_id as the PK (a superkey). BCNF satisfied.
);

CREATE TABLE bcnf_student_advisors (
    student_id INT,
    advisor_id INT REFERENCES bcnf_advisor_subjects,
    PRIMARY KEY (student_id, advisor_id)
);
"""

SEED_BCNF = """
INSERT INTO bcnf_advisor_subjects VALUES
    (10, 'Mathematics'),
    (20, 'Physics'),
    (30, 'Chemistry');

INSERT INTO bcnf_student_advisors VALUES
    (1, 10),
    (1, 20),
    (2, 10),
    (2, 30),
    (3, 20);
"""


def main():
    with db.cursor() as cur:
        # --- Show the 3NF (but not BCNF) table ---
        cur.execute(SETUP_VIOLATION)
        cur.execute(SEED_VIOLATION)

        print("=" * 60)
        print("BOYCE-CODD NORMAL FORM (BCNF)")
        print("=" * 60)

        print("\n--- In 3NF but NOT BCNF ---")
        db.print_table(
            cur,
            "SELECT * FROM bcnf_student_advisors_3nf ORDER BY student_id, subject",
            ["student_id", "subject", "advisor_id"],
        )

        print("FD violation: advisor_id --> subject, but advisor_id is not a superkey.")
        print("Advisor 10 appears on two rows, both carrying 'Mathematics':")
        db.print_table(
            cur,
            "SELECT * FROM bcnf_student_advisors_3nf WHERE advisor_id = 10",
            ["student_id", "subject", "advisor_id"],
        )

        print("ANOMALY — reassigning advisor 10 to 'Statistics':")
        print("  UPDATE bcnf_student_advisors_3nf")
        print("    SET subject = 'Statistics' WHERE advisor_id = 10;")
        print("  => Must update N rows. Partial update = inconsistent state.\n")

        # --- Show the BCNF decomposition ---
        cur.execute(SETUP_BCNF)
        cur.execute(SEED_BCNF)

        print("--- BCNF decomposition ---")
        print("\n  bcnf_advisor_subjects  (advisor_id is the PK — superkey for advisor_id --> subject)")
        db.print_table(
            cur,
            "SELECT * FROM bcnf_advisor_subjects ORDER BY advisor_id",
            ["advisor_id", "subject"],
        )

        print("  bcnf_student_advisors  (enrollment facts only)")
        db.print_table(
            cur,
            "SELECT * FROM bcnf_student_advisors ORDER BY student_id, advisor_id",
            ["student_id", "advisor_id"],
        )

        print("IMPROVEMENT — reassigning advisor 10 to 'Statistics':")
        print("  UPDATE bcnf_advisor_subjects")
        print("    SET subject = 'Statistics' WHERE advisor_id = 10;")
        print("  => Exactly ONE row. No risk of partial inconsistency.\n")

        print("--- Reconstructed view (same info, no redundancy) ---")
        db.print_table(
            cur,
            """
            SELECT sa.student_id, ads.subject, sa.advisor_id
            FROM bcnf_student_advisors sa
            JOIN bcnf_advisor_subjects ads ON ads.advisor_id = sa.advisor_id
            ORDER BY sa.student_id, ads.subject
            """,
            ["student_id", "subject", "advisor_id"],
        )

        print("Summary of all four forms:")
        print("  0NF  -> 1NF:  eliminate multi-valued / non-atomic columns")
        print("  1NF  -> 2NF:  eliminate partial dependencies on a composite key")
        print("  2NF  -> 3NF:  eliminate transitive dependencies (A -> B -> C)")
        print("  3NF  -> BCNF: eliminate FDs where the determinant is not a superkey")


if __name__ == "__main__":
    main()
