from dataclasses import dataclass, field
from datetime import date

from digest.config import Rules


@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    program: str
    goal: str
    enrollment_status: str
    modality: str
    units: int | None
    term_number: int | None
    gpa: float | None
    grade: str | None
    lms_last_login: date | None
    lms_logins: int | None
    missing: int | None
    aid_status: str
    aid_hold_type: str
    aid_hold_since: date | None
    registration_hold: bool
    registered_for_spring: bool | None
    advisor: str
    last_advisor_contact: date | None
    last_outreach_date: date | None
    last_outreach_channel: str
    outreach_response: str
    source_row: int

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class Finding:
    code: str
    category: str
    points: int
    label: str
    detail: str
    cue: str


@dataclass
class Outreach:
    channel: str
    kind: str
    reason: str
    message: str


PRIORITY_LABELS = {
    "High": "Underperformers",
    "Medium": "Average performers",
    "Low": "Satisfactory performers",
    "Clear": "No flag",
}


@dataclass
class ScoredStudent:
    student: Student
    findings: list[Finding]
    score: int
    priority: str
    days_since_login: int | None
    outreach: Outreach | None
    rank: int | None = None
    advisor_rank: int | None = None

    @property
    def flagged(self) -> bool:
        return self.priority != "Clear"

    @property
    def priority_label(self) -> str:
        return PRIORITY_LABELS.get(self.priority, self.priority)


@dataclass
class AdvisorGroup:
    name: str
    flagged: list[ScoredStudent] = field(default_factory=list)
    clear: list[ScoredStudent] = field(default_factory=list)

    @property
    def caseload(self) -> int:
        return len(self.flagged) + len(self.clear)


@dataclass
class Digest:
    as_of: date
    week_label: str
    source_name: str
    rules: Rules
    students: list[ScoredStudent]
    advisors: list[AdvisorGroup]
    warnings: list[str]

    @property
    def flagged(self) -> list[ScoredStudent]:
        return [student for student in self.students if student.flagged]

    @property
    def top(self) -> list[ScoredStudent]:
        return self.flagged[:5]

    def count(self, priority: str) -> int:
        return sum(1 for student in self.students if student.priority == priority)
