"""Check that the Anthropic API key never appears in files, commits, or outputs.

Usage:
    py work/agent/check_secrets.py          # full scan, including all git history
    py work/agent/check_secrets.py --quick  # skip history (used by the pre-commit hook)

Prints only where a key was or wasn't found, never the key itself.
Exit code 1 means a key was found somewhere it shouldn't be.
"""
import re
import subprocess
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent.parent
ENV_FILE = WORK / ".env"
PLACEHOLDER = "paste-your-key-here"
# Shape of any Anthropic key, so we also catch a key that isn't the one in .env.
KEY_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")


def load_key():
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("ANTHROPIC_API_KEY="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            return value if value and value != PLACEHOLDER else None
    return None


def git(*args):
    result = subprocess.run(["git", *args], cwd=WORK, capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    return result.stdout


def contains_key(text, key):
    return bool((key and key in text) or KEY_PATTERN.search(text))


def main():
    quick = "--quick" in sys.argv
    key = load_key()
    problems = []

    print(f"Key in work/.env: {'found' if key else 'not set yet'}")

    # 1. .env must be ignored by git and never tracked.
    if not git("check-ignore", str(ENV_FILE)).strip():
        problems.append("work/.env is NOT ignored by git")
    tracked_env = [p for p in git("ls-files").splitlines() if Path(p).name.startswith(".env") and not p.endswith(".env.example")]
    if tracked_env:
        problems.append(f"tracked .env files: {tracked_env}")

    # 2. Every file in the project folder except .env itself (code, logs, outputs).
    for path in WORK.rglob("*"):
        if not path.is_file() or path == ENV_FILE or "__pycache__" in path.parts:
            continue
        if contains_key(path.read_text(encoding="utf-8", errors="ignore"), key):
            problems.append(f"key found in file: {path.relative_to(WORK)}")

    # 3. Anything staged for the next commit.
    if contains_key(git("diff", "--cached"), key):
        problems.append("key found in staged changes")

    # 4. Every commit on every branch.
    if not quick and contains_key(git("log", "-p", "--all"), key):
        problems.append("key found in git history")

    checked = "files, staged changes" + ("" if quick else ", git history")
    if problems:
        print("FAIL:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print(f"PASS: no API key in {checked}; work/.env is gitignored.")


if __name__ == "__main__":
    main()
