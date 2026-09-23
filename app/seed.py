"""
Seeds the test catalog with a small starter set of common lab tests,
so a fresh install isn't completely empty. Safe to run multiple times
(skips if the catalog already has entries).

Run manually with:  python -m app.seed
"""

from .models import db, TestCatalog
from .utils import generate_code

DEFAULT_TESTS = [
    ("Complete Blood Count (CBC)", "Hematology", "Blood", "cells/uL", "4.5-11.0 x10^9/L", 15.00, 4),
    ("Hemoglobin (Hb)", "Hematology", "Blood", "g/dL", "13.5-17.5 (M) / 12.0-15.5 (F)", 8.00, 2),
    ("Blood Glucose (Fasting)", "Biochemistry", "Blood", "mg/dL", "70-100", 6.00, 2),
    ("Lipid Profile", "Biochemistry", "Blood", "mg/dL", "See individual ranges", 25.00, 6),
    ("Liver Function Test (LFT)", "Biochemistry", "Blood", "U/L", "See individual ranges", 30.00, 8),
    ("Kidney Function Test (KFT)", "Biochemistry", "Blood", "mg/dL", "See individual ranges", 28.00, 8),
    ("Thyroid Stimulating Hormone (TSH)", "Endocrinology", "Blood", "mIU/L", "0.4-4.0", 20.00, 24),
    ("Urinalysis (Routine)", "Microbiology", "Urine", "-", "See report", 10.00, 4),
    ("Stool Routine Exam", "Microbiology", "Stool", "-", "See report", 10.00, 6),
    ("HbA1c", "Biochemistry", "Blood", "%", "4.0-5.6", 22.00, 24),
    ("C-Reactive Protein (CRP)", "Immunology", "Blood", "mg/L", "<5.0", 18.00, 6),
    ("Blood Group & Rh Typing", "Hematology", "Blood", "-", "-", 12.00, 2),
]


def seed_test_catalog():
    if TestCatalog.query.count() > 0:
        return 0

    added = 0
    for name, category, sample_type, unit, ref_range, price, tat in DEFAULT_TESTS:
        t = TestCatalog(
            test_code=generate_code("TST", TestCatalog, "test_code", digits=4),
            name=name,
            category=category,
            sample_type=sample_type,
            unit=unit,
            reference_range=ref_range,
            price=price,
            turnaround_hours=tat,
        )
        db.session.add(t)
        added += 1

    db.session.commit()
    return added


if __name__ == "__main__":
    from . import create_app

    app = create_app()
    with app.app_context():
        n = seed_test_catalog()
        print(f"Seeded {n} test catalog entries.")
