# Lead Triage Agent

First-pass triage for inbound website leads: each lead gets QUALIFY, NURTURE, REJECT, or ESCALATE, with a one-sentence reason and a confidence score. Built for Single Grain's Beat Claude challenge, AI Automation Intern 012 (brief version 2026-07).

The write-up is in [WRITEUP.md](WRITEUP.md). The submitted run's outputs are in [output/](output/).

## Run it

Needs Python 3.10+ and an Anthropic API key.

```
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
# put your key in .env:  ANTHROPIC_API_KEY=...
py agent/checks.py              # step 1 only: code checks, no key needed
py agent/triage.py              # full run on fixtures/inbound_leads.csv
py agent/triage.py other.csv    # run on another CSV with the same columns
py agent/compare.py             # compare output/decisions.csv with manual_labels.csv
py agent/check_secrets.py       # confirm no API key is in any file or commit
```

Outputs:
- `output/decisions.csv`: one row per lead
- `output/run_log.jsonl`: every prompt and response, the fixture checksum, and the code commit
- `output/run_console.txt`: the console output

## How it works

1. `agent/checks.py`: code-only flags (missing or malformed data, repeat submitters, risky links, legal requests, text addressed to an AI).
2. `agent/triage.py`: Claude Opus 5.5 decides each lead, with the lead text passed as data and never as instructions. Safety rules then send hard-flagged, manipulative, low-confidence (≤ 0.60) or failed leads to a person.
3. `agent/compare.py`: compares the agent's decisions with the blind manual labels. The agent itself never reads those labels.
