import tempfile
import unittest
from datetime import date
from pathlib import Path

from digest.config import Rules, rules_catalog
from digest.engine import DigestError, build_digest_from_csv, read_students
from digest.export_excel import build_workbook

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "boom_test_students_50.csv"
AS_OF = date(2026, 11, 21)


def digest():
    return build_digest_from_csv(SAMPLE, Rules(), AS_OF)


def by_id(result, student_id):
    for student in result.students:
        if student.student.student_id == student_id:
            return student
    raise AssertionError(student_id)


class DigestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.digest = digest()

    def test_sample_size_and_week(self):
        self.assertEqual(len(self.digest.students), 50)
        self.assertEqual(self.digest.week_label, "Week of November 16–22, 2026")
        self.assertEqual(self.digest.as_of, AS_OF)

    def test_worst_students_lead_the_week(self):
        names = [student.student.name for student in self.digest.flagged[:6]]
        self.assertEqual(
            names,
            [
                "Diego Hernandez",
                "Maria Garcia",
                "Kevin Tran",
                "Aaliyah Williams",
                "Jamal Johnson",
                "Linh Nguyen",
            ],
        )
        diego = self.digest.flagged[0]
        self.assertEqual(diego.priority, "High")
        self.assertEqual(diego.score, sum(finding.points for finding in diego.findings))
        self.assertGreater(diego.score, by_id(self.digest, "S100100").score)

    def test_healthy_students_stay_off_the_list(self):
        for student_id in ("S100138", "S100122", "S100121", "S100140"):
            student = by_id(self.digest, student_id)
            self.assertEqual(student.priority, "Clear")
            self.assertEqual(student.findings, [])
            self.assertIsNone(student.outreach)

    def test_every_reason_shows_up_in_the_message(self):
        catalog = {rule["code"] for rule in rules_catalog(Rules())}
        for student in self.digest.flagged:
            self.assertEqual(student.score, sum(finding.points for finding in student.findings))
            message = student.outreach.message.lower()
            self.assertIn(student.student.first_name.lower(), message)
            for finding in student.findings:
                self.assertIn(finding.code, catalog)
                self.assertIn(
                    finding.cue.lower(),
                    message,
                    f"{student.student.name} missing cue {finding.cue!r} for {finding.code}\n{student.outreach.message}",
                )

    def test_message_matches_the_blocker(self):
        luis = by_id(self.digest, "S100111")
        self.assertEqual(luis.priority, "Medium")
        self.assertIn("verification", luis.outreach.message.lower())
        self.assertNotIn("missing assignment", luis.outreach.message.lower())
        self.assertEqual(luis.outreach.channel, "Email")

        jamal = by_id(self.digest, "S100101")
        self.assertEqual(jamal.outreach.kind, "script")
        self.assertIn("didn't hear back", jamal.outreach.message.lower())
        self.assertNotIn("unpaid", jamal.outreach.message.lower())
        self.assertIn("verification", jamal.outreach.message.lower())
        self.assertIn("8 missing", jamal.outreach.message.lower())

        maria = by_id(self.digest, "S100100")
        self.assertIn("unpaid balance", maria.outreach.message.lower())
        self.assertIn("1.62", maria.outreach.message)
        self.assertIn("november 4", maria.outreach.message.lower())

        keisha = by_id(self.digest, "S100124")
        self.assertEqual(keisha.priority, "Low")
        self.assertIn("not registered for spring", keisha.outreach.message.lower())
        self.assertIn("3.79", keisha.outreach.message)
        self.assertNotIn("missing assignment", keisha.outreach.message.lower())

        elena = by_id(self.digest, "S100114")
        self.assertEqual(elena.outreach.channel, "SMS")
        self.assertIn("an f", elena.outreach.message.lower())

        nia = by_id(self.digest, "S100138")
        self.assertEqual(nia.priority, "Clear")

    def test_advisors_are_ranked_inside_the_caseload(self):
        alvarez = next(group for group in self.digest.advisors if group.name == "R. Alvarez")
        self.assertEqual(alvarez.flagged[0].student.name, "Diego Hernandez")
        self.assertEqual(alvarez.flagged[0].advisor_rank, 1)
        self.assertGreater(alvarez.clear.__len__(), 0)

    def test_workbook_has_the_ranked_rows(self):
        workbook_bytes = build_workbook(self.digest).getvalue()
        self.assertGreater(len(workbook_bytes), 5000)
        from openpyxl import load_workbook

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "digest.xlsx"
            path.write_bytes(workbook_bytes)
            book = load_workbook(path)
        self.assertEqual(book.sheetnames[0], "Rules")
        ranked = book["Ranked digest"]
        self.assertEqual(ranked["G2"].value, "Diego Hernandez")
        self.assertIn("unpaid balance", ranked["T3"].value.lower())

    def test_bad_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text("student_id,first_name\nS1,Ada\n", encoding="utf-8")
            with self.assertRaises(DigestError):
                read_students(path)


if __name__ == "__main__":
    unittest.main()
