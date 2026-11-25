"""Excel workbook of the current digest."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from digest.config import rules_catalog
from digest.models import Digest, ScoredStudent

INK = "1E2A24"
PAPER = "F6F1E7"
HIGH = "A12D42"
MEDIUM = "8F5608"
LOW = "0D6B56"
LINE = "E2D9CC"
WHITE = "FFFdf8".upper()

THIN = Border(
    left=Side(style="thin", color=LINE),
    right=Side(style="thin", color=LINE),
    top=Side(style="thin", color=LINE),
    bottom=Side(style="thin", color=LINE),
)


def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def _header(cell, fill_color: str = INK) -> None:
    cell.font = Font(name="Calibri", bold=True, color="F6F1E7", size=11)
    cell.fill = _fill(fill_color)
    cell.alignment = Alignment(vertical="center", wrap_text=True)


def _body(cell, priority: str | None = None) -> None:
    colors = {"High": "FFF1F4", "Medium": "FFF5E4", "Low": "E7F6F1"}
    cell.font = Font(name="Calibri", size=11, color="1C1915")
    cell.alignment = Alignment(vertical="top", wrap_text=True)
    cell.border = THIN
    if priority in colors:
        cell.fill = _fill(colors[priority])


def _priority_font(priority: str) -> Font:
    color = {"High": HIGH, "Medium": MEDIUM, "Low": LOW}.get(priority, "1C1915")
    return Font(name="Calibri", bold=True, size=11, color=color)


def _write_sheet(workbook: Workbook, title: str, rows: list[ScoredStudent], include_clear: bool) -> None:
    sheet = workbook.create_sheet(title)
    headers = [
        "Advisor",
        "Advisor rank",
        "College rank",
        "Priority",
        "Score",
        "Student ID",
        "Student",
        "Email",
        "Phone",
        "Program",
        "Goal",
        "Enrollment",
        "Modality",
        "GPA",
        "Current grade",
        "Why flagged",
        "Blockers",
        "Suggested channel",
        "Channel reason",
        "Suggested message",
    ]
    sheet.append(headers)
    for cell in sheet[1]:
        _header(cell)
    sheet.row_dimensions[1].height = 22
    sheet.auto_filter.ref = f"A1:T1"
    sheet.freeze_panes = "A2"

    exported = rows if include_clear else [row for row in rows if row.flagged]
    for item in exported:
        student = item.student
        why = "\n".join(f"• {finding.detail} ({finding.points} pts)" for finding in item.findings)
        blockers = "; ".join(finding.label for finding in item.findings)
        outreach = item.outreach
        sheet.append(
            [
                student.advisor,
                item.advisor_rank or "",
                item.rank or "",
                f"{item.priority} · {item.priority_label}" if item.flagged else item.priority_label,
                item.score,
                student.student_id,
                student.name,
                student.email,
                student.phone,
                student.program,
                student.goal,
                student.enrollment_status,
                student.modality,
                student.gpa if student.gpa is not None else "",
                student.grade or "",
                why,
                blockers,
                outreach.channel if outreach else "",
                outreach.reason if outreach else "",
                outreach.message if outreach else "",
            ]
        )
        for cell in sheet[sheet.max_row]:
            _body(cell, item.priority)
        sheet.cell(sheet.max_row, 4).font = _priority_font(item.priority)
        sheet.row_dimensions[sheet.max_row].height = 78

    widths = [16, 14, 14, 34, 10, 14, 22, 36, 18, 24, 36, 14, 14, 10, 14, 55, 40, 16, 42, 80]
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.oddHeader.left.text = title
    sheet.print_title_rows = "1:1"


def _rules_sheet(workbook: Workbook, digest: Digest) -> None:
    sheet = workbook.create_sheet("Rules", 0)
    sheet["A1"] = "Advisor digest — draft rules"
    sheet["A1"].font = Font(name="Calibri", bold=True, size=16, color=INK)
    sheet["A2"] = (
        f"{digest.week_label}. Scored as of {digest.as_of.strftime('%B')} {digest.as_of.day}, "
        f"{digest.as_of.year}. Source: {digest.source_name}."
    )
    sheet["A3"] = (
        "These thresholds are a working draft. High priority (underperformers) starts at "
        f"{digest.rules.high_min} points. Medium priority (average performers) starts at {digest.rules.medium_min} points. "
        "Low priority (satisfactory performers) is still on the list below that. "
        "A student with no fired rule is left off the contact list."
    )
    sheet["A3"].alignment = Alignment(wrap_text=True)
    sheet.merge_cells("A2:C2")
    sheet.merge_cells("A3:C3")
    sheet.row_dimensions[3].height = 36

    headers = ["Category", "Rule", "Points"]
    for column, header in enumerate(headers, start=1):
        cell = sheet.cell(5, column, header)
        _header(cell)
    for offset, rule in enumerate(rules_catalog(digest.rules), start=6):
        values = [rule["category"], rule["test"], rule["points"]]
        for column, value in enumerate(values, start=1):
            cell = sheet.cell(offset, column, value)
            _body(cell)
    sheet.column_dimensions["A"].width = 18
    sheet.column_dimensions["B"].width = 78
    sheet.column_dimensions["C"].width = 12

    note_row = 6 + len(rules_catalog(digest.rules)) + 1
    sheet.cell(
        note_row,
        1,
        "Messages are written from the rules that fired for that student. Nothing is sent automatically.",
    ).font = Font(name="Calibri", italic=True, color="5E584E")
    if digest.warnings:
        sheet.cell(note_row + 2, 1, "Data notes").font = Font(name="Calibri", bold=True, color=INK)
        for index, warning in enumerate(digest.warnings):
            sheet.cell(note_row + 3 + index, 1, warning).alignment = Alignment(wrap_text=True)


def build_workbook(digest: Digest) -> BytesIO:
    workbook = Workbook()
    default = workbook.active
    workbook.remove(default)
    _rules_sheet(workbook, digest)
    by_rank = list(digest.flagged)
    _write_sheet(workbook, "Ranked digest", by_rank, include_clear=False)
    by_advisor = []
    for group in digest.advisors:
        by_advisor.extend(group.flagged)
    _write_sheet(workbook, "By advisor", by_advisor, include_clear=False)
    clear = [student for student in digest.students if not student.flagged]
    _write_sheet(workbook, "No flag this week", clear, include_clear=True)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer
