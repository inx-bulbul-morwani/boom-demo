"""Weekly advisor digest. Local showcase, or a hosted server via gunicorn."""

import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for
from werkzeug.utils import secure_filename

from digest.config import SAMPLE_AS_OF, Rules, form_groups, rules_catalog, rules_from_mapping, rules_to_mapping
from digest.engine import DigestError, build_digest, read_students
from digest.export_excel import build_workbook

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / "data" / "boom_test_students_50.csv"
UPLOADS = ROOT / "instance" / "uploads"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "advisor-digest-local-demo")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

KIND_LABEL = {
    "script": "Call script",
    "text": "Text draft",
    "email": "Email draft",
}


def _as_of():
    raw = session.get("as_of") or SAMPLE_AS_OF
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _rules() -> Rules:
    return rules_from_mapping(session.get("rules"))


def _csv_path() -> Path:
    raw = session.get("csv_path")
    if raw:
        path = Path(raw)
        if path.exists():
            return path
    return SAMPLE


def _source_name() -> str:
    if session.get("csv_path") and Path(session["csv_path"]).exists():
        return session.get("source_name") or "uploaded.csv"
    return SAMPLE.name


def _digest():
    students, warnings = read_students(_csv_path())
    return build_digest(students, _rules(), _as_of(), _source_name(), warnings)


def _format_day(value):
    if not value:
        return ""
    return f"{value.strftime('%B')} {value.day}, {value.year}"


@app.template_filter("day")
def day_filter(value):
    return _format_day(value)


@app.template_filter("tel")
def tel_filter(phone: str) -> str:
    digits = "".join(character for character in (phone or "") if character.isdigit())
    if len(digits) == 10:
        digits = "1" + digits
    return f"tel:+{digits}" if digits else ""


@app.context_processor
def extras():
    return {"kind_label": KIND_LABEL}


@app.route("/")
def index():
    error = None
    digest = None
    try:
        digest = _digest()
    except DigestError as exc:
        error = " ".join(exc.errors)
    return render_template(
        "index.html",
        digest=digest,
        error=error,
        catalog=rules_catalog(_rules()),
        form_groups=form_groups(_rules()),
        as_of=_as_of().isoformat(),
        as_of_label=_format_day(_as_of()),
    )


@app.post("/settings")
def settings():
    try:
        posted = rules_from_mapping(request.form)
    except ValueError:
        flash("Rules need to be numbers. The digest was not changed.")
        return redirect(url_for("index"))
    issues = posted.problems()
    as_of_raw = (request.form.get("as_of") or "").strip()
    try:
        datetime.strptime(as_of_raw, "%Y-%m-%d")
    except ValueError:
        issues.append("The digest date needs to be a real date.")
    if issues:
        for issue in issues:
            flash(issue)
        return redirect(url_for("index"))
    session["rules"] = rules_to_mapping(posted)
    session["as_of"] = as_of_raw
    flash("Digest recalculated with the draft rules.")
    return redirect(url_for("index"))


@app.post("/upload")
def upload():
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        flash("Choose a CSV file first.")
        return redirect(url_for("index"))
    filename = secure_filename(uploaded.filename)
    if not filename.lower().endswith(".csv"):
        flash("Upload a .csv file with the same columns as the sample.")
        return redirect(url_for("index"))
    UPLOADS.mkdir(parents=True, exist_ok=True)
    destination = UPLOADS / f"{uuid4().hex}.csv"
    uploaded.save(destination)
    try:
        read_students(destination)
    except DigestError as exc:
        destination.unlink(missing_ok=True)
        for issue in exc.errors:
            flash(issue)
        return redirect(url_for("index"))
    except UnicodeDecodeError:
        destination.unlink(missing_ok=True)
        flash("That file is not a UTF-8 CSV.")
        return redirect(url_for("index"))
    session["csv_path"] = str(destination)
    session["source_name"] = filename
    flash(f"Loaded {filename}.")
    return redirect(url_for("index"))


@app.post("/reset-rules")
def reset_rules():
    session.pop("rules", None)
    session.pop("as_of", None)
    flash("Draft rules restored.")
    return redirect(url_for("index"))


@app.post("/reset-file")
def reset_file():
    session.pop("csv_path", None)
    session.pop("source_name", None)
    flash("Sample student file restored.")
    return redirect(url_for("index"))


@app.get("/export.xlsx")
def export_xlsx():
    try:
        digest = _digest()
    except DigestError as exc:
        flash(" ".join(exc.errors))
        return redirect(url_for("index"))
    stamp = digest.as_of.isoformat()
    return send_file(
        build_workbook(digest),
        as_attachment=True,
        download_name=f"advisor_digest_{stamp}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.errorhandler(413)
def too_large(_error):
    flash("That file is larger than 2 MB.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
