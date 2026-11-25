"""Write the sample digest workbook without starting the web app."""

from datetime import datetime
from pathlib import Path

from digest.config import SAMPLE_AS_OF, Rules
from digest.engine import build_digest_from_csv
from digest.export_excel import build_workbook

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "boom_test_students_50.csv"
OUTPUT = ROOT / "output" / "advisor_digest_week_of_2026-11-16.xlsx"


def main() -> None:
    as_of = datetime.strptime(SAMPLE_AS_OF, "%Y-%m-%d").date()
    digest = build_digest_from_csv(SAMPLE, Rules(), as_of)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(build_workbook(digest).getvalue())
    print(f"Wrote {OUTPUT}")
    print(
        f"{digest.week_label}: {len(digest.flagged)} flagged "
        f"({digest.count('High')} underperformers, {digest.count('Medium')} average performers, "
        f"{digest.count('Low')} satisfactory performers)"
    )


if __name__ == "__main__":
    main()
