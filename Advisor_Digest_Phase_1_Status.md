# Advisor Digest — Phase 1 status

**Prepared for:** prospect review  
**Date:** 23 November 2026  
**Status:** Phase 1 showcase is ready to review  
**Scope of this phase:** a working, rule-based weekly contact list. No machine learning and no language model.

---

## What you asked for

Turn a student CSV into a weekly advisor digest. For each student who needs attention, show why they are on the list, how urgent they are, and one suggested message that fits their specific situation.

The sample file is `boom_test_students_50.csv`: 50 students and 26 columns covering academics, LMS activity, financial aid, registration, and prior outreach.

## What is ready now

A local showcase an advisor can open in a browser. It reads the student file, applies a written set of rules, and produces a ranked contact list.

For every flagged student the digest shows:

- a score and a High, Medium, or Low priority
- the exact reasons the rules fired, with the points behind each reason
- one suggested message that mentions only those reasons
- the channel to use (email, text, or a phone-call script) and why that channel was chosen

Students with no fired rule stay off the contact list. Nothing is sent to a student. The advisor copies, edits, or opens the draft.

The same result can be exported to Excel or printed to PDF.

## Result on the sample file

Scored as of Saturday, 21 November 2026, which is the week the sample data describes (week of 16–22 November 2026).

| | Count |
|---|---|
| Students in the file | 50 |
| On the contact list | 28 |
| High priority (45 points or more) | 11 |
| Medium priority (20–44 points) | 9 |
| Low priority (1–19 points) | 8 |
| No flag this week | 22 |

Caseload by advisor:

| Advisor | Caseload | To contact | No flag |
|---|---:|---:|---:|
| R. Alvarez | 15 | 9 | 6 |
| T. Brooks | 11 | 9 | 2 |
| K. Singh | 12 | 5 | 7 |
| M. Okoro | 12 | 5 | 7 |

The first students an advisor would call this week, under the draft rules:

| Rank | Student | Priority | Score | Advisor | What fired |
|---|---|---|---:|---|---|
| 1 | Diego Hernandez | High | 117 | R. Alvarez | GPA 1.85, grade F, 7 missing assignments, LMS quiet 18 days, unpaid balance, registration hold, not registered for spring, no reply |
| 2 | Maria Garcia | High | 111 | R. Alvarez | GPA 1.62, grade D, 8 missing assignments, LMS quiet 23 days, unpaid balance, registration hold, not registered for spring, no reply |
| 3 | Kevin Tran | High | 106 | R. Alvarez | GPA 1.84, grade D, 5 missing assignments, LMS quiet 14 days, unpaid balance, registration hold, not registered for spring, no reply |
| 4 | Aaliyah Williams | High | 103 | M. Okoro | GPA 2.10, grade F, 7 missing assignments, LMS quiet 21 days, verification documents, registration hold, not registered for spring, no reply |
| 5 | Jamal Johnson | High | 97 | T. Brooks | GPA 2.18, grade D, 8 missing assignments, LMS quiet 18 days, verification documents, registration hold, not registered for spring, no reply |

These six students sit well above the rest of the list. The next high-priority student scores 63. The draft point values are what create that separation. They are a working proposal, not an approved policy.

Suggested channel on the 28 flagged students: 17 email, 9 phone call (used when the last outreach got no reply), 2 SMS (used when the student already replied by text).

Three students have no LMS login date on file (Imani Okafor, Victor Sanchez, Tomas Reyes). They are treated as not recently active, and the digest says so.

## How a student is flagged

Each student is checked against the same written rules. A student can fire several rules at once. The score is the sum of the points. Priority is then:

- **High** — 45 points or more
- **Medium** — 20 to 44 points
- **Low** — any score above zero that is under 20
- **Clear** — no rule fired; left off the contact list

“Financial aid not applied” is not a flag. A blank or invalid cell is skipped for that rule and noted, rather than invented.

Within the same score, the list breaks ties by days since the last LMS login, then missing assignments, then lower GPA, then name. Each advisor also gets a rank inside their own caseload, separate from the college-wide rank.

### Draft rules

These numbers live in the page under **Draft scoring rules**. Changing them and choosing **Recalculate** rebuilds the list immediately. **Reset draft rules** restores the table below.

**When a rule fires**

| Category | Rule | Points |
|---|---|---:|
| Academic | Cumulative GPA below 2.00 | 25 |
| Academic | Cumulative GPA from 2.00 up to 2.50 | 15 |
| Academic | Lowest current grade is F | 18 |
| Academic | Lowest current grade is D | 12 |
| Assignments | 7 or more missing | 20 |
| Assignments | 5 or 6 missing | 15 |
| Assignments | 3 or 4 missing | 10 |
| Engagement | No LMS login on file, 0 logins in 14 days, or 14+ days since login | 15 |
| Engagement | 7+ days since login and at most 2 logins in 14 days | 8 |
| Financial | Unpaid balance hold | 18 |
| Financial | Verification documents, a missing aid document, or any other active aid hold | 14 |
| Financial | Aid is pending and no hold type is listed | 10 |
| Registration | Registration hold is active | 10 |
| Registration | Not registered for spring | 6 |
| Outreach | Last outreach received no reply | 5 |

Only one GPA band and one missing-assignment band can fire for a student. An inactive student is not also marked low-activity.

### How the message is written

The message is assembled from the rules that fired for that student. It does not mention a problem the file does not show.

- It opens from the assigned advisor and names the student’s program.
- It states each fired blocker in plain language, including dates and counts from the file.
- If grades are in good shape and the only issues are financial or registration, it says so, so the note is not read as an academic warning.
- It ties the ask to the student’s stated goal (transfer, certificate, degree, and so on).
- The closing ask matches the blockers: coursework, a hold, aid documents, a login, or spring registration.
- Channel follows outreach history: no reply becomes a call script, a text reply stays on SMS, any other reply or no prior outreach starts as email.

The advisor can edit the draft in the card, copy it, open an email, or place the call. The product does not send the message.

**Example — financial and registration only, grades left alone**

Luis Martinez, Biology, advisor T. Brooks. Medium, 30 points. No outreach is logged, so the draft is an email.

> Hi Luis, I'm T. Brooks, your advisor for Biology.
>
> Your grades are in good shape (cumulative GPA 3.25, lowest current grade C). This note is about financial aid and spring registration, not coursework.
>
> Financial aid is still pending verification documents from October 23. A registration hold is on your account, so you are not registered for spring yet. Getting this cleared keeps your pre-med transfer on schedule.
>
> Please submit the financial aid documents this week and reply once they are in, so I can watch the hold.

**Example — a single low-priority registration note**

Keisha Walker, Business Admin, advisor M. Okoro. Low, 6 points. GPA 3.79, grade C, not registered for spring. The draft asks to finish spring registration and does not mention assignments, aid, or the LMS.

## What an advisor can do in the showcase

- See the week’s contact-first list, then each advisor’s caseload with a rank inside that caseload and a college-wide rank.
- Filter by High, Medium, or Low, filter to one advisor, and search by name, student ID, or program.
- Read the reasons and points on the card, edit the suggested message, copy it, open email, or call.
- See who had no flag this week, grouped under the same advisor.
- Upload another CSV with the same columns and rescore it. A file with the wrong columns is rejected. A bad date or number is skipped and reported.
- Change the digest date, the cutoffs, and the point values, then recalculate.
- Export Excel. The workbook has four sheets: the rules that were used, the college-wide ranked list, the same students sorted by advisor, and students with no flag.
- Print or save a PDF from the browser.

## What this phase deliberately does not do

- It does not predict dropout or future failure. It reports the conditions that are already in the file.
- It does not use a language model to write the message. Wording is fixed to the fired rules so a reviewer can see why each sentence is there. A later phase can keep this same blocker list and replace only the wording.
- It does not send email, text, or place a call.
- It does not store a history of prior weeks. Each upload is scored on its own.
- It does not compare this week with last week (improved, worse, or unchanged).
- It is a local showcase for review, not a deployed campus system. There is no login, no live student-information feed, and no advisor inbox integration.

## What we need from you to lock Phase 1

The behavior above is built and can be demonstrated on the sample file. The numbers in the rules table are a proposal. Confirming or replacing them is the main decision left in this phase.

1. **Rules.** Are the GPA lines (2.00 and 2.50), the missing-assignment bands (3, 5, and 7), and the LMS windows (14 days inactive, 7 days and at most 2 logins for low activity) the right cutoffs?
2. **Points and priority.** Are unpaid balance, a failing grade, and severe missing work the right things to weigh most heavily? Is High at 45 and Medium at 20 the split you want, or should the list be shorter or longer?
3. **Messages.** Are blocker-specific drafts enough for the first version, or do you want a later phase to rewrite them with a language model? Do you already have advisor templates we should follow? Should one message cover every blocker, as it does now?
4. **Delivery.** Is a browser digest plus Excel and print-to-PDF the right handoff, or do you also want the file emailed to each advisor with only their own students?
5. **Cadence.** Should each weekly CSV stand alone, or should a later phase keep history and show whether a student improved, worsened, or stayed the same?

## Suggested next step

Review the sample week in the showcase, especially the top of R. Alvarez’s and T. Brooks’s lists and a clear case such as Luis Martinez or Keisha Walker. Tell us which draft thresholds to keep and which to change. Once those are confirmed, Phase 1 can be treated as the agreed rules, and a follow-on phase can add model-written wording, week-over-week history, or delivery into the tools advisors already use.
