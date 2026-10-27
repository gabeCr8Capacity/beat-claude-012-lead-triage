"""Step 5: compare the agent's decisions with the user's blind manual labels.

Run only after triage.py has finished. This is the only script that reads
manual_labels.csv; the agent never sees it.

Usage:
    py work/agent/compare.py
Writes output/comparison.md.
"""
import csv
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent.parent
OUT_DIR = WORK / "output"
DECISIONS = ["QUALIFY", "NURTURE", "REJECT", "ESCALATE"]


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {r["lead_id"]: r for r in csv.DictReader(f)}


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def main():
    agent = read_csv(OUT_DIR / "decisions.csv")
    human = read_csv(WORK / "manual_labels.csv")
    with open(OUT_DIR / "run_log.jsonl", encoding="utf-8") as f:
        run = json.loads(f.readline())

    ids = sorted(set(agent) | set(human))
    missing = [i for i in ids if i not in agent or i not in human]
    both = [i for i in ids if i in agent and i in human]
    final_match = [i for i in both if agent[i]["decision"] == human[i]["decision"]]
    model_match = [i for i in both if agent[i]["model_decision"] == human[i]["decision"]]
    overridden = [i for i in both if agent[i]["decided_by"].startswith("rule")]

    lines = [
        "# Agent vs. manual labels",
        "",
        f"- Run `{run['run_id']}`, started {run['started_at']}, model `{run['model']}` (effort {run['effort']}), "
        f"git commit `{run['git_commit']}`",
        f"- Fixture `{run['fixture']}`, SHA-256 `{run['fixture_sha256']}`",
        f"- Manual labels: `manual_labels.csv`, written blind before the agent was built",
        "",
        "## Summary",
        "",
        f"- [Observed] Leads compared: {len(both)} of {len(ids)}" + (f" (missing: {', '.join(missing)})" if missing else ""),
        f"- [Observed] Final decision matches manual label: {len(final_match)}/{len(both)}",
        f"- [Observed] Model's own decision (before safety rules) matches manual label: {len(model_match)}/{len(both)}",
        f"- [Observed] Decisions changed by a safety rule: {len(overridden)}",
        "",
        "## Decision counts",
        "",
        "| Decision | Manual | Agent |",
        "|---|---|---|",
    ]
    for d in DECISIONS:
        lines.append(f"| {d} | {sum(human[i]['decision'] == d for i in both)} | {sum(agent[i]['decision'] == d for i in both)} |")

    lines += ["", "## Confusion matrix (rows = manual label, columns = agent final decision)", "",
              "| Manual \\ Agent | " + " | ".join(DECISIONS) + " |", "|---" * (len(DECISIONS) + 1) + "|"]
    for h in DECISIONS:
        counts = [sum(human[i]["decision"] == h and agent[i]["decision"] == a for i in both) for a in DECISIONS]
        lines.append(f"| **{h}** | " + " | ".join(str(c) for c in counts) + " |")

    lines += ["", "## Disagreements", ""]
    disagreements = [i for i in both if i not in final_match]
    if not disagreements:
        lines.append("None.")
    for i in disagreements:
        a, h = agent[i], human[i]
        lines += [
            f"### {i}: manual {h['decision']}, agent {a['decision']}",
            f"- Model said: {a['model_decision'] or '(no model output)'}; decided by: `{a['decided_by']}`; confidence {a['confidence']}",
            f"- Flags: {a['flags'] or '(none)'}",
            f"- Agent reason: {a['reason']}",
            f"- Manual reason: {h['reason']}",
            "",
        ]

    lines += ["## All leads", "",
              "| Lead | Manual | Agent | Match | Model said | Decided by | Conf. | Agent reason |",
              "|---|---|---|---|---|---|---|---|"]
    for i in both:
        a, h = agent[i], human[i]
        match = "yes" if i in final_match else "**no**"
        lines.append(f"| {i} | {h['decision']} | {a['decision']} | {match} | {a['model_decision']} | "
                     f"`{a['decided_by']}` | {a['confidence']} | {cell(a['reason'])} |")

    (OUT_DIR / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Final match {len(final_match)}/{len(both)}; model-only match {len(model_match)}/{len(both)}; "
          f"rule overrides {len(overridden)}. Wrote output/comparison.md")


if __name__ == "__main__":
    main()
