#!/usr/bin/env python3
"""Stdlib-only fallback secret scan of the working tree. NOT a substitute for gitleaks
(which also scans Git history). Exit 1 on findings."""
import re, sys
from pathlib import Path

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "aws access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic api key": re.compile(r"(?i)\b(api[_-]?key|secret|token|passwd|password)\b\s*[:=]\s*['\"][A-Za-z0-9_\-/+=]{16,}['\"]"),
    "db url with password": re.compile(r"postgres(?:ql)?(?:\+\w+)?://[^:\s/]+:[^@\s]{4,}@"),
}
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".next"}
SKIP_FILES = {".env.example", "scan_secrets.py"}

def main(root: str = ".") -> int:
    hits = 0
    for p in Path(root).rglob("*"):
        if not p.is_file() or SKIP_DIRS & set(p.parts) or p.name in SKIP_FILES:
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for name, rx in PATTERNS.items():
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                print(f"[{name}] {p}:{line}")  # location only, never the value
                hits += 1
    print(f"{hits} potential finding(s)")
    return 1 if hits else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
