"""Draft scoring rules.

These numbers are a working proposal for the showcase. The prospect has not
confirmed them. Changing a value here changes who is ranked and why.
"""

from dataclasses import asdict, dataclass, fields


SAMPLE_AS_OF = "2026-11-21"


@dataclass
class Rules:
    gpa_critical: float = 2.00
    gpa_warning: float = 2.50
    missing_moderate: int = 3
    missing_high: int = 5
    missing_severe: int = 7
    inactive_days: int = 14
    low_activity_days: int = 7
    low_activity_logins: int = 2
    high_min: int = 45
    medium_min: int = 20
    points_gpa_critical: int = 25
    points_gpa_warning: int = 15
    points_grade_f: int = 18
    points_grade_d: int = 12
    points_missing_severe: int = 20
    points_missing_high: int = 15
    points_missing_moderate: int = 10
    points_inactive: int = 15
    points_low_activity: int = 8
    points_unpaid: int = 18
    points_aid_docs: int = 14
    points_aid_pending: int = 10
    points_reg_hold: int = 10
    points_not_registered: int = 6
    points_no_reply: int = 5

    def problems(self) -> list[str]:
        issues = []
        if self.gpa_critical <= 0 or self.gpa_warning <= 0:
            issues.append("GPA lines have to be greater than zero.")
        if self.gpa_critical >= self.gpa_warning:
            issues.append(
                "The academic-standing GPA has to be lower than the early-alert GPA."
            )
        if not (1 <= self.missing_moderate <= self.missing_high <= self.missing_severe):
            issues.append(
                "Missing-assignment cutoffs have to rise from moderate to severe."
            )
        if self.inactive_days < 1 or self.low_activity_days < 1:
            issues.append("LMS day cutoffs have to be at least 1.")
        if self.low_activity_days > self.inactive_days:
            issues.append(
                "The low-activity day cutoff cannot be later than the inactive cutoff."
            )
        if self.low_activity_logins < 1:
            issues.append("The low-activity login cap has to be at least 1.")
        if self.medium_min < 1 or self.high_min <= self.medium_min:
            issues.append("High priority has to sit above medium priority.")
        point_fields = [f.name for f in fields(self) if f.name.startswith("points_")]
        for name in point_fields:
            if getattr(self, name) < 0:
                issues.append("Point values cannot be negative.")
                break
        return issues


def rules_from_mapping(data: dict | None) -> Rules:
    if not data:
        return Rules()
    allowed = {f.name for f in fields(Rules)}
    clean = {}
    for key, value in data.items():
        if key not in allowed or value is None or value == "":
            continue
        default = getattr(Rules(), key)
        clean[key] = int(value) if isinstance(default, int) else float(value)
    return Rules(**clean)


def rules_to_mapping(rules: Rules) -> dict:
    return asdict(rules)


def form_fields(rules: Rules) -> list[dict]:
    """Inputs for the draft-rules panel. Values come from the live rules."""
    spec = [
        ("Thresholds", "gpa_critical", "Academic-standing GPA is below", "0.01", "0", "4"),
        ("Thresholds", "gpa_warning", "Early-alert GPA is below", "0.01", "0", "4"),
        ("Thresholds", "missing_moderate", "Flag missing assignments starting at", "1", "1", "30"),
        ("Thresholds", "missing_high", "Higher missing-assignment band starts at", "1", "1", "30"),
        ("Thresholds", "missing_severe", "Severe missing-assignment band starts at", "1", "1", "30"),
        ("Thresholds", "inactive_days", "LMS inactive after this many days", "1", "1", "90"),
        ("Thresholds", "low_activity_days", "Low LMS activity after this many days", "1", "1", "90"),
        ("Thresholds", "low_activity_logins", "Low activity means at most this many logins", "1", "1", "20"),
        ("Points", "points_gpa_critical", "GPA below the academic-standing line", "1", "0", "100"),
        ("Points", "points_gpa_warning", "GPA below the early-alert line", "1", "0", "100"),
        ("Points", "points_grade_f", "Current grade is F", "1", "0", "100"),
        ("Points", "points_grade_d", "Current grade is D", "1", "0", "100"),
        ("Points", "points_missing_severe", "Severe missing assignments", "1", "0", "100"),
        ("Points", "points_missing_high", "High missing assignments", "1", "0", "100"),
        ("Points", "points_missing_moderate", "Moderate missing assignments", "1", "0", "100"),
        ("Points", "points_inactive", "LMS inactive", "1", "0", "100"),
        ("Points", "points_low_activity", "Low LMS activity", "1", "0", "100"),
        ("Points", "points_unpaid", "Unpaid balance hold", "1", "0", "100"),
        ("Points", "points_aid_docs", "Verification or missing aid document", "1", "0", "100"),
        ("Points", "points_aid_pending", "Aid pending, with no hold type", "1", "0", "100"),
        ("Points", "points_reg_hold", "Registration hold", "1", "0", "100"),
        ("Points", "points_not_registered", "Not registered for spring", "1", "0", "100"),
        ("Points", "points_no_reply", "Previous outreach got no reply", "1", "0", "100"),
        ("Priority", "high_min", "High priority (underperformers) starts at this score", "1", "1", "500"),
        ("Priority", "medium_min", "Medium priority (average performers) starts at this score", "1", "1", "500"),
    ]
    fields = []
    for group, name, label, step, low, high in spec:
        value = getattr(rules, name)
        fields.append(
            {
                "group": group,
                "name": name,
                "label": label,
                "step": step,
                "min": low,
                "max": high,
                "value": f"{value:.2f}" if isinstance(value, float) else value,
            }
        )
    return fields


def form_groups(rules: Rules) -> list[tuple[str, list[dict]]]:
    grouped: dict[str, list[dict]] = {}
    for field in form_fields(rules):
        grouped.setdefault(field["group"], []).append(field)
    return list(grouped.items())


def rules_catalog(rules: Rules) -> list[dict]:
    """Human-readable copy of the rules that the engine actually uses."""
    return [
        {
            "code": "gpa_critical",
            "category": "Academic",
            "test": f"Cumulative GPA is below {rules.gpa_critical:.2f}",
            "points": rules.points_gpa_critical,
        },
        {
            "code": "gpa_warning",
            "category": "Academic",
            "test": f"Cumulative GPA is {rules.gpa_critical:.2f} up to {rules.gpa_warning:.2f}",
            "points": rules.points_gpa_warning,
        },
        {
            "code": "grade_f",
            "category": "Academic",
            "test": "Lowest current grade is F",
            "points": rules.points_grade_f,
        },
        {
            "code": "grade_d",
            "category": "Academic",
            "test": "Lowest current grade is D",
            "points": rules.points_grade_d,
        },
        {
            "code": "missing_severe",
            "category": "Assignments",
            "test": f"{rules.missing_severe} or more missing assignments",
            "points": rules.points_missing_severe,
        },
        {
            "code": "missing_high",
            "category": "Assignments",
            "test": f"{rules.missing_high}–{rules.missing_severe - 1} missing assignments",
            "points": rules.points_missing_high,
        },
        {
            "code": "missing_moderate",
            "category": "Assignments",
            "test": f"{rules.missing_moderate}–{rules.missing_high - 1} missing assignments",
            "points": rules.points_missing_moderate,
        },
        {
            "code": "lms_inactive",
            "category": "Engagement",
            "test": f"No LMS login date, 0 logins in 14 days, or {rules.inactive_days}+ days since login",
            "points": rules.points_inactive,
        },
        {
            "code": "lms_low",
            "category": "Engagement",
            "test": (
                f"{rules.low_activity_days}+ days since login and at most "
                f"{rules.low_activity_logins} logins in 14 days"
            ),
            "points": rules.points_low_activity,
        },
        {
            "code": "aid_unpaid",
            "category": "Financial",
            "test": "Aid hold is an unpaid balance",
            "points": rules.points_unpaid,
        },
        {
            "code": "aid_verification",
            "category": "Financial",
            "test": "Aid hold is verification documents",
            "points": rules.points_aid_docs,
        },
        {
            "code": "aid_missing_doc",
            "category": "Financial",
            "test": "Aid hold is a missing document",
            "points": rules.points_aid_docs,
        },
        {
            "code": "aid_other",
            "category": "Financial",
            "test": "Any other active aid hold",
            "points": rules.points_aid_docs,
        },
        {
            "code": "aid_pending",
            "category": "Financial",
            "test": "Financial aid is pending and there is no hold type",
            "points": rules.points_aid_pending,
        },
        {
            "code": "registration_hold",
            "category": "Registration",
            "test": "Registration hold is active",
            "points": rules.points_reg_hold,
        },
        {
            "code": "not_registered_spring",
            "category": "Registration",
            "test": "Not registered for spring",
            "points": rules.points_not_registered,
        },
        {
            "code": "outreach_no_reply",
            "category": "Outreach",
            "test": "Last outreach received no reply",
            "points": rules.points_no_reply,
        },
    ]
