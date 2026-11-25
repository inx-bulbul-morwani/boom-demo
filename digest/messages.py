"""Template messages. Each sentence is tied to a rule that actually fired."""

from digest.models import Finding, Outreach, Student

GOAL_PHRASES = {
    "Transfer to UC": "your transfer to a UC",
    "Transfer to CSU": "your transfer to a CSU",
    "Transfer to a BSN program": "your transfer into a BSN program",
    "Pre-med transfer": "your pre-med transfer",
    "Figure out a major": "your plan to choose a major",
    "Certificate and job in 1 year": "your plan to finish the certificate and be job-ready within a year",
    "Certificate and job": "your plan to finish the certificate and move into a job",
    "Associate degree, then work": "your plan to finish your associate degree and move into work",
    "Associate degree for a teaching aide job": "your plan to finish your associate degree for a teaching aide job",
}

SEVERITY = {
    "aid_unpaid": 0,
    "grade_f": 1,
    "gpa_critical": 2,
    "missing_severe": 3,
    "lms_inactive": 4,
    "aid_verification": 5,
    "aid_missing_doc": 6,
    "aid_other": 7,
    "grade_d": 8,
    "gpa_warning": 9,
    "missing_high": 10,
    "registration_hold": 11,
    "missing_moderate": 12,
    "lms_low": 13,
    "aid_pending": 14,
    "not_registered_spring": 15,
    "outreach_no_reply": 16,
}


def format_day(value) -> str:
    return f"{value.strftime('%B')} {value.day}"


def record_phrase(program: str) -> str:
    if (program or "").strip().lower() == "undecided":
        return "your record"
    return f"your {program} record"


def advisor_line(student: Student) -> str:
    if student.program.strip().lower() == "undecided":
        return f"I'm {student.advisor}, your advisor."
    return f"I'm {student.advisor}, your advisor for {student.program}."


def goal_phrase(goal: str) -> str:
    cleaned = (goal or "").strip()
    if cleaned in GOAL_PHRASES:
        return GOAL_PHRASES[cleaned]
    if not cleaned:
        return "the goal on your record"
    return f"the goal on your record ({cleaned})"


def choose_outreach(student: Student, message: str) -> Outreach:
    response = (student.outreach_response or "").strip().lower()
    previous = (student.last_outreach_channel or "").strip()
    when = format_day(student.last_outreach_date) if student.last_outreach_date else ""
    previous_label = previous or "outreach"

    if response == "no reply":
        reason = f"Last {previous_label.lower()} on {when} got no reply." if when else (
            "The last outreach got no reply."
        )
        reason += " A phone call is the next step."
        return Outreach("Phone call", "script", reason.strip(), message)
    if response == "replied" and previous.lower() == "sms":
        reason = f"They replied to the text on {when}. Stay on SMS." if when else (
            "They replied by text. Stay on SMS."
        )
        return Outreach("SMS", "text", reason, message)
    if response == "replied":
        reason = f"They replied on {when}. Continue on email." if when else (
            "They replied. Continue on email."
        )
        return Outreach("Email", "email", reason, message)
    return Outreach(
        "Email",
        "email",
        "No outreach is logged yet. Start with email.",
        message,
    )


def primary_finding(findings: list[Finding]) -> Finding | None:
    ranked = [finding for finding in findings if finding.code != "outreach_no_reply"]
    if not ranked:
        return findings[0] if findings else None
    return max(ranked, key=lambda finding: (finding.points, -SEVERITY.get(finding.code, 50)))


def _codes(findings: list[Finding]) -> set[str]:
    return {finding.code for finding in findings}


def _academic_sentences(student: Student, codes: set[str]) -> list[str]:
    sentences = []
    gpa = f"{student.gpa:.2f}" if student.gpa is not None else ""
    if "gpa_critical" in codes:
        sentences.append(
            f"Your cumulative GPA is {gpa}, below the 2.00 academic-standing line."
        )
        # The threshold in the sentence is rewritten by the caller when rules differ.
    if "gpa_warning" in codes:
        sentences.append(f"Your cumulative GPA is {gpa}, below the early-alert line.")
    if "grade_f" in codes:
        sentences.append("Your lowest current grade is an F.")
    if "grade_d" in codes:
        sentences.append("Your lowest current grade is a D.")
    if any(code.startswith("missing_") for code in codes) and student.missing is not None:
        noun = "assignment" if student.missing == 1 else "assignments"
        sentences.append(f"You have {student.missing} missing {noun}.")
    return sentences


def _engagement_sentence(student: Student, codes: set[str], days: int | None) -> str:
    if "lms_inactive" not in codes and "lms_low" not in codes:
        return ""
    if student.lms_last_login is None:
        return "I don't have an LMS login date on file for you."
    when = format_day(student.lms_last_login)
    day_word = "day" if days == 1 else "days"
    if "lms_inactive" in codes and student.lms_logins == 0 and days is not None and days < 14:
        return (
            f"The record shows 0 logins in the past 14 days, alongside a login date "
            f"of {when}."
        )
    if student.lms_logins == 0:
        login_clause = ", and you have not logged into the LMS in the past 14 days"
    elif student.lms_logins is not None:
        noun = "login" if student.lms_logins == 1 else "logins"
        login_clause = f", with {student.lms_logins} {noun} in the past 14 days"
    else:
        login_clause = ""
    if "lms_low" in codes:
        times = {1: "once", 2: "twice"}.get(student.lms_logins, f"{student.lms_logins} times")
        return (
            f"You've logged into the LMS {times} in the past 14 days, "
            f"most recently on {when}."
        )
    ago = f", {days} {day_word} ago" if days is not None else ""
    return f"Your last LMS login was {when}{ago}{login_clause}."


def _admin_sentences(student: Student, codes: set[str]) -> list[str]:
    sentences = []
    since = format_day(student.aid_hold_since) if student.aid_hold_since else ""
    since_clause = f" since {since}" if since else ""
    if "aid_unpaid" in codes:
        sentences.append(
            f"An unpaid balance has been on your account{since_clause}."
        )
    elif "aid_verification" in codes:
        origin = f" from {since}" if since else ""
        sentences.append(
            f"Financial aid is still pending verification documents{origin}."
        )
    elif "aid_missing_doc" in codes:
        sentences.append(
            f"Financial aid has been waiting on a missing document{since_clause}."
        )
    elif "aid_other" in codes:
        hold = student.aid_hold_type or "an aid hold"
        sentences.append(f"There is an active aid hold ({hold}){since_clause}.")
    elif "aid_pending" in codes:
        sentences.append("Financial aid is pending, and that still has to be resolved.")

    if "registration_hold" in codes and "not_registered_spring" in codes:
        sentences.append(
            "A registration hold is on your account, so you are not registered for spring yet."
        )
    elif "registration_hold" in codes:
        sentences.append(
            "A registration hold is on your account and will block a registration change until it clears."
        )
    elif "not_registered_spring" in codes:
        sentences.append("You are not registered for spring yet.")
    return sentences


def _join_sentences(sentences: list[str]) -> str:
    cleaned = [sentence.strip() for sentence in sentences if sentence and sentence.strip()]
    if not cleaned:
        return ""
    paragraph = " ".join(cleaned)
    if not paragraph.endswith("."):
        paragraph += "."
    return paragraph


def _reassurance(student: Student, codes: set[str]) -> str:
    academic = {"gpa_critical", "gpa_warning", "grade_f", "grade_d"} & codes
    assignments = {code for code in codes if code.startswith("missing_")}
    engagement = {"lms_inactive", "lms_low"} & codes
    financial = bool(
        {"aid_unpaid", "aid_verification", "aid_missing_doc", "aid_other", "aid_pending"} & codes
    )
    registration = bool({"registration_hold", "not_registered_spring"} & codes)
    if academic or assignments or engagement or not (financial or registration):
        return ""
    if student.gpa is None or student.gpa < 2.5:
        return ""
    if student.grade not in {"A", "B", "C"}:
        return ""
    grade_bit = f", lowest current grade {student.grade}" if student.grade else ""
    if "aid_unpaid" in codes and registration:
        topic = "an unpaid balance and spring registration"
    elif "aid_unpaid" in codes:
        topic = "an unpaid balance"
    elif financial and registration:
        topic = "financial aid and spring registration"
    elif registration:
        topic = "spring registration"
    else:
        topic = "financial aid"
    return (
        f"Your grades are in good shape (cumulative GPA {student.gpa:.2f}{grade_bit}). "
        f"This note is about {topic}, not coursework."
    )


def _goal_sentence(student: Student, codes: set[str]) -> str:
    phrase = goal_phrase(student.goal)
    academic = bool(
        {"gpa_critical", "gpa_warning", "grade_f", "grade_d"} & codes
        or any(code.startswith("missing_") for code in codes)
    )
    admin = bool(
        {
            "aid_unpaid",
            "aid_verification",
            "aid_missing_doc",
            "aid_other",
            "aid_pending",
            "registration_hold",
            "not_registered_spring",
        }
        & codes
    )
    if academic:
        return f"That puts {phrase} at risk."
    if admin:
        return f"Getting this cleared keeps {phrase} on schedule."
    if "lms_inactive" in codes or "lms_low" in codes:
        return f"Staying in the courses matters for {phrase}."
    return ""


def _ask(student: Student, kind: str, codes: set[str]) -> str:
    academic = bool(
        {"gpa_critical", "gpa_warning", "grade_f", "grade_d"} & codes
        or any(code.startswith("missing_") for code in codes)
    )
    engagement = bool({"lms_inactive", "lms_low"} & codes)
    financial = bool(
        {"aid_unpaid", "aid_verification", "aid_missing_doc", "aid_other", "aid_pending"}
        & codes
    )
    registration = bool({"registration_hold", "not_registered_spring"} & codes)

    if academic and (financial or registration):
        spoken = (
            "Can we set a time this week to handle the hold and the missing coursework, "
            "in that order?"
        )
        written = (
            "Reply with a time this week. We can handle the hold and the missing coursework "
            "in that order."
        )
    elif academic:
        spoken = "Can we set a time this week to pick which work to submit first?"
        written = "Reply with a time this week and we will pick which work to submit first."
    elif engagement and not (financial or registration):
        spoken = "Can you log in this week and tell me once you are in the course?"
        written = "Log in this week and reply once you are in the course. If this login record is wrong, tell me and I will correct it."
    elif financial and "aid_unpaid" in codes:
        spoken = (
            "Can you check the unpaid balance with the business office this week, "
            "then tell me once it is paid so registration can move?"
        )
        written = (
            "Please check the unpaid balance with the business office this week, "
            "then reply once it is paid so registration can move."
        )
    elif financial:
        spoken = (
            "Can you submit the financial aid documents this week and tell me once they are in, "
            "so I can watch the hold?"
        )
        written = (
            "Please submit the financial aid documents this week and reply once they are in, "
            "so I can watch the hold."
        )
    elif registration:
        spoken = "Can we set a time this week to finish spring registration together?"
        written = "Reply with a time this week and I will sit with you to finish spring registration."
    else:
        spoken = "Can we set a time this week to take the next step?"
        written = "Reply with a time this week and I will help with the next step."

    if kind == "script":
        return spoken + " I can stay on the line and walk through it."
    if kind == "text":
        return written
    return written


def _apply_rule_thresholds(sentences: list[str], rules) -> list[str]:
    """Keep GPA sentences aligned with the live thresholds, not the defaults."""
    updated = []
    critical = f"{rules.gpa_critical:.2f}"
    warning = f"{rules.gpa_warning:.2f}"
    for sentence in sentences:
        sentence = sentence.replace(
            "below the 2.00 academic-standing line",
            f"below the {critical} academic-standing line",
        )
        sentence = sentence.replace(
            "below the early-alert line",
            f"below the {warning} early-alert line",
        )
        updated.append(sentence)
    return updated


def compose(student: Student, findings: list[Finding], rules, days_since_login: int | None) -> Outreach:
    codes = _codes(findings)
    response = (student.outreach_response or "").strip().lower()
    previous = (student.last_outreach_channel or "").strip().lower()
    if response == "no reply":
        kind = "script"
    elif response == "replied" and previous == "sms":
        kind = "text"
    else:
        kind = "email"

    if response == "no reply":
        verb = {"email": "emailed", "sms": "texted"}.get(previous, "contacted")
        if student.last_outreach_date:
            hello = (
                f"Hi {student.first_name}, this is {student.advisor} from advising. "
                f"I {verb} you on {format_day(student.last_outreach_date)} and didn't hear back, "
                f"so I'm calling about {record_phrase(student.program)}."
            )
        else:
            hello = (
                f"Hi {student.first_name}, this is {student.advisor} from advising. "
                f"I reached out and didn't hear back, so I'm calling about "
                f"{record_phrase(student.program)}."
            )
    elif kind == "text":
        when = format_day(student.last_outreach_date) if student.last_outreach_date else "your last text"
        hello = (
            f"Hi {student.first_name}, it's {student.advisor}. "
            f"Thank you for replying on {when}."
        )
    else:
        hello = f"Hi {student.first_name}, {advisor_line(student)}"

    academic = _apply_rule_thresholds(_academic_sentences(student, codes), rules)
    engagement = _engagement_sentence(student, codes, days_since_login)
    if engagement:
        academic.append(engagement)
    admin = _admin_sentences(student, codes)
    goal = _goal_sentence(student, codes)
    if goal:
        if academic:
            academic.append(goal)
        elif admin:
            admin.append(goal)

    paragraphs = [hello]
    reassurance = _reassurance(student, codes)
    if reassurance:
        paragraphs.append(reassurance)
    course_paragraph = _join_sentences(academic)
    admin_paragraph = _join_sentences(admin)
    if course_paragraph:
        paragraphs.append(course_paragraph)
    if admin_paragraph:
        paragraphs.append(admin_paragraph)
    paragraphs.append(_ask(student, kind, codes))
    message = "\n\n".join(paragraphs)
    return choose_outreach(student, message)
