"""Parse the student file and score it with the draft rules."""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

from digest.config import Rules
from digest.messages import compose, format_day
from digest.models import AdvisorGroup, Digest, Finding, ScoredStudent, Student

REQUIRED_COLUMNS = [
    "student_id",
    "first_name",
    "last_name",
    "email",
    "phone",
    "program_of_study",
    "stated_goal",
    "enrollment_status",
    "modality",
    "units_enrolled",
    "term_number",
    "cumulative_gpa",
    "lowest_current_grade",
    "lms_last_login",
    "lms_logins_last_14_days",
    "missing_assignments",
    "financial_aid_status",
    "aid_hold_type",
    "aid_hold_since",
    "registration_hold",
    "registered_for_spring",
    "assigned_advisor",
    "last_advisor_contact",
    "last_outreach_date",
    "last_outreach_channel",
    "outreach_response",
]


class DigestError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def parse_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    return datetime.strptime(text, "%Y-%m-%d").date()


def week_label(as_of: date) -> str:
    monday = as_of - timedelta(days=as_of.weekday())
    sunday = monday + timedelta(days=6)
    if monday.year == sunday.year and monday.month == sunday.month:
        return f"Week of {monday.strftime('%B')} {monday.day}–{sunday.day}, {monday.year}"
    if monday.year == sunday.year:
        return (
            f"Week of {monday.strftime('%B')} {monday.day}–"
            f"{sunday.strftime('%B')} {sunday.day}, {monday.year}"
        )
    return (
        f"Week of {monday.strftime('%B')} {monday.day}, {monday.year}–"
        f"{sunday.strftime('%B')} {sunday.day}, {sunday.year}"
    )


def _blank(value: str) -> str:
    return (value or "").strip()


def _yn(value: str) -> bool | None:
    text = _blank(value).upper()
    if text == "Y":
        return True
    if text == "N":
        return False
    if text == "":
        return None
    raise ValueError(text)


def _int_cell(value: str) -> int | None:
    text = _blank(value)
    if not text:
        return None
    return int(text)


def _float_cell(value: str) -> float | None:
    text = _blank(value)
    if not text:
        return None
    return float(text)


def read_students(path: Path) -> tuple[list[Student], list[str]]:
    warnings: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing:
            raise DigestError(
                [f"The file is missing required columns: {', '.join(missing)}."]
            )
        students: list[Student] = []
        seen: dict[str, int] = {}
        for index, row in enumerate(reader, start=2):
            student_id = _blank(row.get("student_id", ""))
            first = _blank(row.get("first_name", ""))
            last = _blank(row.get("last_name", ""))
            if not student_id or not first or not last:
                warnings.append(f"Row {index} is missing a name or student id and was skipped.")
                continue
            if student_id in seen:
                warnings.append(
                    f"{student_id} appears on rows {seen[student_id]} and {index}. Both are kept."
                )
            seen[student_id] = index

            def cell_date(column: str) -> date | None:
                raw = _blank(row.get(column, ""))
                if not raw:
                    return None
                try:
                    return parse_date(raw)
                except ValueError:
                    warnings.append(
                        f"Row {index} ({first} {last}): {column} is not a YYYY-MM-DD date."
                    )
                    return None

            def cell_int(column: str) -> int | None:
                raw = _blank(row.get(column, ""))
                if not raw:
                    return None
                try:
                    return _int_cell(raw)
                except ValueError:
                    warnings.append(f"Row {index} ({first} {last}): {column} is not a whole number.")
                    return None

            def cell_float(column: str) -> float | None:
                raw = _blank(row.get(column, ""))
                if not raw:
                    return None
                try:
                    return _float_cell(raw)
                except ValueError:
                    warnings.append(f"Row {index} ({first} {last}): {column} is not a number.")
                    return None

            grade_raw = _blank(row.get("lowest_current_grade", "")).upper()
            grade = grade_raw if grade_raw in {"A", "B", "C", "D", "F"} else None
            if grade_raw and grade is None:
                warnings.append(
                    f"Row {index} ({first} {last}): lowest current grade '{grade_raw}' was ignored."
                )

            try:
                hold = _yn(row.get("registration_hold", ""))
            except ValueError:
                warnings.append(
                    f"Row {index} ({first} {last}): registration hold was not Y or N."
                )
                hold = False
            if hold is None:
                hold = False

            try:
                registered = _yn(row.get("registered_for_spring", ""))
            except ValueError:
                warnings.append(
                    f"Row {index} ({first} {last}): spring registration was not Y or N."
                )
                registered = None

            advisor = _blank(row.get("assigned_advisor", "")) or "Unassigned"
            students.append(
                Student(
                    student_id=student_id,
                    first_name=first,
                    last_name=last,
                    email=_blank(row.get("email", "")),
                    phone=_blank(row.get("phone", "")),
                    program=_blank(row.get("program_of_study", "")) or "Undeclared",
                    goal=_blank(row.get("stated_goal", "")),
                    enrollment_status=_blank(row.get("enrollment_status", "")),
                    modality=_blank(row.get("modality", "")),
                    units=cell_int("units_enrolled"),
                    term_number=cell_int("term_number"),
                    gpa=cell_float("cumulative_gpa"),
                    grade=grade,
                    lms_last_login=cell_date("lms_last_login"),
                    lms_logins=cell_int("lms_logins_last_14_days"),
                    missing=cell_int("missing_assignments"),
                    aid_status=_blank(row.get("financial_aid_status", "")),
                    aid_hold_type=_blank(row.get("aid_hold_type", "")),
                    aid_hold_since=cell_date("aid_hold_since"),
                    registration_hold=bool(hold),
                    registered_for_spring=registered,
                    advisor=advisor,
                    last_advisor_contact=cell_date("last_advisor_contact"),
                    last_outreach_date=cell_date("last_outreach_date"),
                    last_outreach_channel=_blank(row.get("last_outreach_channel", "")),
                    outreach_response=_blank(row.get("outreach_response", "")),
                    source_row=index,
                )
            )
    if not students:
        raise DigestError(["The file has no student rows."])
    return students, warnings


def _hold_label(student: Student) -> str:
    hold = student.aid_hold_type.strip()
    if hold.lower() == "none":
        return ""
    return hold


def score_student(student: Student, rules: Rules, as_of: date) -> ScoredStudent:
    findings: list[Finding] = []
    days = None
    if student.lms_last_login and student.lms_last_login <= as_of:
        days = (as_of - student.lms_last_login).days

    if student.gpa is not None and student.gpa < rules.gpa_critical:
        findings.append(
            Finding(
                code="gpa_critical",
                category="Academic",
                points=rules.points_gpa_critical,
                label=f"GPA {student.gpa:.2f}",
                detail=(
                    f"Cumulative GPA is {student.gpa:.2f}, below the "
                    f"{rules.gpa_critical:.2f} academic-standing line."
                ),
                cue=f"{student.gpa:.2f}",
            )
        )
    elif student.gpa is not None and student.gpa < rules.gpa_warning:
        findings.append(
            Finding(
                code="gpa_warning",
                category="Academic",
                points=rules.points_gpa_warning,
                label=f"GPA {student.gpa:.2f}",
                detail=(
                    f"Cumulative GPA is {student.gpa:.2f}, below the "
                    f"{rules.gpa_warning:.2f} early-alert line."
                ),
                cue=f"{student.gpa:.2f}",
            )
        )

    if student.grade == "F":
        findings.append(
            Finding(
                code="grade_f",
                category="Academic",
                points=rules.points_grade_f,
                label="Grade F",
                detail="Lowest current grade is an F.",
                cue="an f",
            )
        )
    elif student.grade == "D":
        findings.append(
            Finding(
                code="grade_d",
                category="Academic",
                points=rules.points_grade_d,
                label="Grade D",
                detail="Lowest current grade is a D.",
                cue="a d",
            )
        )

    if student.missing is not None:
        if student.missing >= rules.missing_severe:
            code, points = "missing_severe", rules.points_missing_severe
        elif student.missing >= rules.missing_high:
            code, points = "missing_high", rules.points_missing_high
        elif student.missing >= rules.missing_moderate:
            code, points = "missing_moderate", rules.points_missing_moderate
        else:
            code, points = "", 0
        if code:
            noun = "assignment" if student.missing == 1 else "assignments"
            findings.append(
                Finding(
                    code=code,
                    category="Assignments",
                    points=points,
                    label=f"{student.missing} missing {noun}",
                    detail=f"{student.missing} missing {noun}.",
                    cue=f"{student.missing} missing",
                )
            )

    inactive = (
        student.lms_last_login is None
        or student.lms_logins == 0
        or (days is not None and days >= rules.inactive_days)
    )
    if inactive:
        if student.lms_last_login is None and student.lms_logins is None:
            detail = "No LMS login date is on file, and the 14-day login count is blank."
            label = "No LMS login on file"
            cue = "lms login date"
        elif student.lms_last_login is None:
            detail = (
                f"No LMS login date is on file. The 14-day login count is {student.lms_logins}."
            )
            label = "No LMS login on file"
            cue = "lms login date"
        else:
            when = format_day(student.lms_last_login)
            if student.lms_logins is None:
                login_bit = ""
            else:
                noun = "login" if student.lms_logins == 1 else "logins"
                login_bit = f", with {student.lms_logins} {noun} in the past 14 days"
            ago = f", {days} days ago" if days is not None else ""
            detail = f"Last LMS login was {when}{ago}{login_bit}."
            label = f"LMS quiet {days} days" if days is not None else "LMS inactive"
            cue = when.lower()
        findings.append(
            Finding(
                code="lms_inactive",
                category="Engagement",
                points=rules.points_inactive,
                label=label,
                detail=detail,
                cue=cue,
            )
        )
    elif (
        student.lms_logins is not None
        and 0 < student.lms_logins <= rules.low_activity_logins
        and days is not None
        and days >= rules.low_activity_days
    ):
        when = format_day(student.lms_last_login)
        noun = "login" if student.lms_logins == 1 else "logins"
        findings.append(
            Finding(
                code="lms_low",
                category="Engagement",
                points=rules.points_low_activity,
                label=f"{student.lms_logins} LMS {noun} / 14 days",
                detail=(
                    f"Only {student.lms_logins} LMS {noun} in the past 14 days, "
                    f"most recently on {when}."
                ),
                cue=when.lower(),
            )
        )

    hold = _hold_label(student)
    hold_since = format_day(student.aid_hold_since) if student.aid_hold_since else ""
    since_bit = f" since {hold_since}" if hold_since else ""
    if hold:
        lowered = hold.lower()
        if "unpaid" in lowered:
            code, points, label = "aid_unpaid", rules.points_unpaid, f"Unpaid balance{since_bit}"
            detail = f"Unpaid balance hold{since_bit}."
            cue = "unpaid balance"
        elif "verification" in lowered:
            code, points = "aid_verification", rules.points_aid_docs
            label = f"Verification documents{since_bit}"
            detail = f"Financial aid is pending verification documents{since_bit}."
            cue = "verification"
        elif "missing document" in lowered:
            code, points = "aid_missing_doc", rules.points_aid_docs
            label = f"Missing aid document{since_bit}"
            detail = f"Financial aid is waiting on a missing document{since_bit}."
            cue = "missing document"
        else:
            code, points = "aid_other", rules.points_aid_docs
            label = hold
            detail = f"Active aid hold: {hold}{since_bit}."
            cue = hold.lower()
        findings.append(
            Finding(code=code, category="Financial", points=points, label=label, detail=detail, cue=cue)
        )
    elif student.aid_status.lower() == "pending":
        findings.append(
            Finding(
                code="aid_pending",
                category="Financial",
                points=rules.points_aid_pending,
                label="Aid pending",
                detail="Financial aid is pending and no hold type is listed.",
                cue="financial aid is pending",
            )
        )

    if student.registration_hold:
        findings.append(
            Finding(
                code="registration_hold",
                category="Registration",
                points=rules.points_reg_hold,
                label="Registration hold",
                detail="A registration hold is active.",
                cue="registration hold",
            )
        )
    if student.registered_for_spring is False:
        findings.append(
            Finding(
                code="not_registered_spring",
                category="Registration",
                points=rules.points_not_registered,
                label="Not registered for spring",
                detail="Not registered for spring.",
                cue="not registered for spring",
            )
        )

    if student.outreach_response.lower() == "no reply":
        when = format_day(student.last_outreach_date) if student.last_outreach_date else "the last try"
        channel = student.last_outreach_channel or "Outreach"
        findings.append(
            Finding(
                code="outreach_no_reply",
                category="Outreach",
                points=rules.points_no_reply,
                label=f"No reply to {channel.lower()} on {when}" if student.last_outreach_date else "No reply to last outreach",
                detail=f"{channel} on {when} received no reply.",
                cue="didn't hear back",
            )
        )

    score = sum(finding.points for finding in findings)
    if score >= rules.high_min:
        priority = "High"
    elif score >= rules.medium_min:
        priority = "Medium"
    elif score > 0:
        priority = "Low"
    else:
        priority = "Clear"

    outreach = compose(student, findings, rules, days) if findings else None
    return ScoredStudent(
        student=student,
        findings=findings,
        score=score,
        priority=priority,
        days_since_login=days,
        outreach=outreach,
    )


def _sort_key(scored: ScoredStudent):
    days = scored.days_since_login if scored.days_since_login is not None else -1
    if scored.student.lms_last_login is None:
        days = 10_000
    missing = scored.student.missing if scored.student.missing is not None else -1
    gpa = scored.student.gpa if scored.student.gpa is not None else 9.99
    return (
        -scored.score,
        -days,
        -missing,
        gpa,
        scored.student.last_name.lower(),
        scored.student.first_name.lower(),
    )


def _login_warnings(students: list[Student]) -> list[str]:
    missing_dates = [student.name for student in students if student.lms_last_login is None]
    if not missing_dates:
        return []
    shown = ", ".join(missing_dates[:8])
    extra = len(missing_dates) - 8
    suffix = f" and {extra} more" if extra > 0 else ""
    return [
        f"{len(missing_dates)} students have no LMS login date ({shown}{suffix}). "
        "They are scored as not recently active."
    ]


def build_digest(
    students: list[Student],
    rules: Rules,
    as_of: date,
    source_name: str,
    warnings: list[str] | None = None,
) -> Digest:
    scored = [score_student(student, rules, as_of) for student in students]
    scored.sort(key=_sort_key)
    rank = 0
    advisor_ranks: dict[str, int] = {}
    for item in scored:
        if not item.flagged:
            continue
        rank += 1
        item.rank = rank
        advisor_ranks[item.student.advisor] = advisor_ranks.get(item.student.advisor, 0) + 1
        item.advisor_rank = advisor_ranks[item.student.advisor]

    groups: dict[str, AdvisorGroup] = {}
    for item in scored:
        group = groups.setdefault(item.student.advisor, AdvisorGroup(name=item.student.advisor))
        if item.flagged:
            group.flagged.append(item)
        else:
            group.clear.append(item)
    advisors = sorted(groups.values(), key=lambda group: group.name.lower())
    for group in advisors:
        group.clear.sort(key=lambda item: (item.student.last_name.lower(), item.student.first_name.lower()))

    notes = list(warnings or [])
    notes.extend(_login_warnings(students))
    return Digest(
        as_of=as_of,
        week_label=week_label(as_of),
        source_name=source_name,
        rules=rules,
        students=scored,
        advisors=advisors,
        warnings=notes,
    )


def build_digest_from_csv(path: Path, rules: Rules, as_of: date) -> Digest:
    students, warnings = read_students(path)
    return build_digest(students, rules, as_of, path.name, warnings)
