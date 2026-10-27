"""Step 1: code-only checks that run before the AI sees a lead.

These are general rules, not answers for one fixture: they look for missing
fields, unparseable values, repeat submitters, risky links, legal requests,
and text that tries to give orders to an AI.

Most flags are data-quality notes passed to the model. Flags in HARD_ESCALATE
always route the lead to a person (enforced in triage.py).

Usage (prints the flags for every row, no API key needed):
    py work/agent/checks.py [path/to/leads.csv]
"""
import csv
import html
import re
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "inbound_leads.csv"

REQUIRED_FIELDS = ["name", "email", "company", "website", "message"]

DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "temp-mail.org", "yopmail.com", "trashmail.com", "sharklasers.com",
    "getnada.com", "dispostable.com", "maildrop.cc", "throwawaymail.com",
}
FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "live.com", "proton.me", "protonmail.com", "gmx.com",
}
PLACEHOLDER_VALUES = {"test", "testing", "asdf", "asdfasdf", "qwerty", "xxx", "n/a", "na", "foo", "bar", "none"}

# Phrases that address the AI rather than describe the business.
INJECTION_PATTERNS = [
    r"\b(ignore|disregard|forget)\b.{0,30}\b(instructions|prompts?|rules)\b",
    r"\b(classify|mark|label|score|rate|tag)\s+(this|the)\s+(lead|row|entry|submission)\s+as\b",
    r"\b(system prompt|you are now|new instructions|developer mode)\b",
    r"\bconfidence\s*(of|=|:)?\s*1(\.0+)?\b",
]
# Requests a person (often legal or privacy) must handle.
LEGAL_PRIVACY_PATTERNS = [
    r"\bgdpr\b", r"\bccpa\b", r"right to (be forgotten|erasure)",
    r"\bdelete\b.{0,30}\b(personal )?data\b", r"\bdata (subject|access) request\b",
    r"\b(lawyer|attorney|legal action|cease and desist|subpoena)\b",
]
URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
EXECUTABLE_LINK = re.compile(r"\.(exe|scr|bat|cmd|msi|vbs|jar|apk|dmg|ps1|iso)(\?|#|$)", re.IGNORECASE)
HTML_TAG = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")

BUDGET_OUTLIER_USD = 500_000  # [Assumed] monthly budgets above this are implausible for a web form

# Flags that always send the lead to a person, whatever the model says.
HARD_ESCALATE = {"prompt_injection", "legal_privacy_request", "executable_link"}

FLAG_DESCRIPTIONS = {
    "missing_name": "name field is empty",
    "missing_email": "email field is empty",
    "missing_company": "company field is empty",
    "missing_website": "website field is empty",
    "missing_message": "message field is empty",
    "invalid_email": "email address is not a valid format",
    "disposable_email": "email uses a disposable/throwaway domain",
    "personal_email": "email uses a free personal mailbox, not a company domain",
    "email_website_mismatch": "email domain differs from website domain",
    "malformed_timestamp": "submitted_at is not a valid date/time",
    "budget_not_numeric": "monthly budget is not a number",
    "budget_normalized": "monthly budget was written with a suffix (e.g. 15k) and was converted",
    "budget_zero": "monthly budget is 0",
    "budget_implausibly_high": f"monthly budget is above ${BUDGET_OUTLIER_USD:,}",
    "placeholder_values": "fields contain placeholder/test values",
    "html_in_message": "message contained HTML, which was stripped",
    "link_in_message": "message contains a link",
    "executable_link": "message links to a downloadable program file",
    "prompt_injection": "message contains text addressed to an AI system (instructions to classify it)",
    "legal_privacy_request": "message is a legal or data-privacy request",
    "repeat_submitter": "same email as an earlier lead",
}


def domain_of(value):
    value = value.strip().lower()
    if "@" in value:
        value = value.rsplit("@", 1)[1]
    value = re.sub(r"^https?://", "", value).split("/")[0]
    return value[4:] if value.startswith("www.") else value


def clean_message(raw):
    """Strip HTML tags and decode entities so the model sees plain text."""
    text = HTML_TAG.sub(" ", raw)
    text = html.unescape(html.unescape(text))  # handles double-encoded entities like &amp;amp;
    return re.sub(r"\s+", " ", text).strip()


def parse_budget(raw):
    """Return (budget_usd or None, flag or None)."""
    s = raw.strip().lower().replace(",", "").replace("$", "").replace("usd", "").strip()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(k|m)?", s)
    if not m:
        return None, "budget_not_numeric"
    value = int(float(m[1]) * {"k": 1_000, "m": 1_000_000}.get(m[2], 1))
    return value, ("budget_normalized" if m[2] else None)


def check_lead(row, earlier_by_email):
    flags = []
    for field in REQUIRED_FIELDS:
        if not row.get(field, "").strip():
            flags.append(f"missing_{field}")

    email = row.get("email", "").strip().lower()
    if email:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email):
            flags.append("invalid_email")
        email_domain = domain_of(email)
        if email_domain in DISPOSABLE_EMAIL_DOMAINS:
            flags.append("disposable_email")
        elif email_domain in FREE_EMAIL_DOMAINS:
            flags.append("personal_email")
        website = row.get("website", "").strip()
        if website and email_domain not in FREE_EMAIL_DOMAINS and domain_of(website) != email_domain:
            flags.append("email_website_mismatch")

    try:
        datetime.strptime(row.get("submitted_at", "").strip(), "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        flags.append("malformed_timestamp")

    budget, budget_flag = parse_budget(row.get("monthly_budget_usd", ""))
    if budget_flag:
        flags.append(budget_flag)
    if budget == 0:
        flags.append("budget_zero")
    elif budget is not None and budget > BUDGET_OUTLIER_USD:
        flags.append("budget_implausibly_high")

    raw_message = row.get("message", "")
    message = clean_message(raw_message)
    if message != raw_message.strip() and HTML_TAG.search(raw_message):
        flags.append("html_in_message")

    values = [row.get(f, "").strip().lower() for f in ("name", "company", "message")]
    if sum(v in PLACEHOLDER_VALUES for v in values) >= 2 or (email and email.split("@")[0] in PLACEHOLDER_VALUES):
        flags.append("placeholder_values")

    urls = URL_PATTERN.findall(message)
    if urls:
        flags.append("link_in_message")
    if any(EXECUTABLE_LINK.search(u) for u in urls):
        flags.append("executable_link")

    lowered = message.lower()
    if any(re.search(p, lowered) for p in INJECTION_PATTERNS):
        flags.append("prompt_injection")
    if any(re.search(p, lowered) for p in LEGAL_PRIVACY_PATTERNS):
        flags.append("legal_privacy_request")

    earlier = earlier_by_email.get(email) if email else None
    if earlier:
        flags.append(f"repeat_submitter:{earlier['lead_id']}")

    return {
        "flags": flags,
        "budget_usd": budget,
        "clean_message": message,
        "earlier_same_email": earlier,
    }


def run_checks(rows):
    """Check every row in order. Returns {lead_id: check result}."""
    results, earlier_by_email = {}, {}
    for row in rows:
        results[row["lead_id"]] = check_lead(row, earlier_by_email)
        email = row.get("email", "").strip().lower()
        if email and email not in earlier_by_email:
            earlier_by_email[email] = row
    return results


def describe(flag):
    name, _, detail = flag.partition(":")
    text = FLAG_DESCRIPTIONS.get(name, name)
    return f"{text} ({detail})" if detail else text


def load_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    rows = load_rows(path)
    results = run_checks(rows)
    for lead_id, r in results.items():
        hard = [f for f in r["flags"] if f.split(":")[0] in HARD_ESCALATE]
        marker = "  [HARD ESCALATE]" if hard else ""
        print(f"{lead_id}: {', '.join(r['flags']) or '(no flags)'}{marker}")
    print(f"\n{len(rows)} rows checked.")
