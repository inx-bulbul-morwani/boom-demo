# Advisor digest (phase 1)

Weekly contact list for advisors, built from the student CSV with fixed rules. No machine learning and no language model.

Each flagged student gets:

- a score and a High / Medium / Low priority
- the exact reasons the rules fired
- one suggested message that mentions only those blockers

The draft thresholds are the ones in the plan, made specific enough that similar students do not all tie. They are not approved by the prospect yet. Change them in the page under **Draft scoring rules**, or in `digest/config.py`.

A later phase can keep the same blocker list and replace `digest/messages.py` with model-written wording.

## Run the showcase

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5050

That address only works on this computer. A tunnel such as ngrok or localhost.run also stops when this computer shuts down. To leave a link that stays up, run the same app on a host with Docker. The image listens on `PORT` (8080 by default):

```bash
docker build -t advisor-digest .
docker run --rm -p 8080:8080 -e SECRET_KEY=choose-a-long-secret advisor-digest
```

The sample file is scored as of Saturday, November 21, 2026, which is the week the data describes. Upload another CSV with the same columns to rescore it. **Export Excel** writes the ranked list, an advisor-sorted list, students with no flag, and the rules that were used. **Print / PDF** uses the browser print dialog.

```bash
python -m unittest tests.test_digest
python -m digest.cli
```

The second command writes `output/advisor_digest_week_of_2026-11-16.xlsx`.
