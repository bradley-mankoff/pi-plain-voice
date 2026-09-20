#!/usr/bin/env python3
"""Plain-voice hygiene gate for markdown artifacts (standard library only).

Scans staged markdown, commit message/body files, named files, or stdin and
reports a verdict as JSON. Each violation carries only a rule id, a file
label, a line number, and a repair hint, so draft text never leaves the
machine through this report.
"""

import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

RULE_RESIDUE = "E-residue"
RULE_SLOP = "E-slop"
RULE_CANONICAL = "S-canonical"

HINT_RESIDUE = "rewrite in plain artifact voice"
HINT_SLOP = "prefer a plain, specific term"

DEFAULT_BUDGET_MS = 50
DEFAULT_SLOP_FAIL_N = 3


def load_terms(path):
    """Parse the terms file.

    Returns (slop_fail_n, residue, slop, canonical) where canonical holds
    (old, new) pairs. Lines starting with # are comments, except a
    slop_fail_n header which may be commented or bare.
    """
    slop_fail_n = DEFAULT_SLOP_FAIL_N
    residue = []
    slop = []
    canonical = []
    section = None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip().lower()
            continue
        if stripped.startswith("#"):
            header = stripped[1:].strip()
            if section is None and header.startswith("slop_fail_n"):
                _, _, value = header.partition("=")
                try:
                    slop_fail_n = int(value.strip())
                except ValueError:
                    pass
            continue
        if section is None:
            if stripped.startswith("slop_fail_n"):
                _, _, value = stripped.partition("=")
                try:
                    slop_fail_n = int(value.strip())
                except ValueError:
                    pass
            continue
        if section == "residue":
            residue.append(stripped)
        elif section == "slop":
            slop.append(stripped)
        elif section == "canonical":
            old, sep, new = stripped.partition("->")
            if sep and old.strip() and new.strip():
                canonical.append((old.strip(), new.strip()))
    return slop_fail_n, residue, slop, canonical


def compile_term(term):
    """One \\b-anchored regex per term; multiword terms join on whitespace."""
    inner = r"\s+".join(re.escape(tok) for tok in term.split())
    return re.compile(r"\b" + inner + r"\b")


def normalize(text):
    """Normalize an input once so every rule scans the same folded form."""
    return unicodedata.normalize("NFKC", text).casefold()


def scan_file(label, text, residue_res, slop_res, canonical_res):
    """Scan one input; one violation per matched term per line."""
    violations = []
    for lineno, line in enumerate(normalize(text).splitlines(), start=1):
        for rx in residue_res:
            if rx.search(line):
                violations.append(
                    {"rule": RULE_RESIDUE, "file": label,
                     "line": lineno, "hint": HINT_RESIDUE}
                )
        for rx in slop_res:
            if rx.search(line):
                violations.append(
                    {"rule": RULE_SLOP, "file": label,
                     "line": lineno, "hint": HINT_SLOP}
                )
        for rx, new in canonical_res:
            if rx.search(line):
                violations.append(
                    {"rule": RULE_CANONICAL, "file": label,
                     "line": lineno, "hint": "prefer '" + new + "'"}
                )
    return violations


def read_text_quietly(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def staged_markdown():
    """Names of staged markdown files (git diff --cached --diff-filter=ACM)."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    return [n for n in (l.strip() for l in proc.stdout.splitlines())
            if n and n.lower().endswith(".md")]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Plain-voice hygiene gate: report PASS, REVIEW, or FAIL as JSON."
    )
    parser.add_argument("--staged", action="store_true",
                        help="scan staged markdown files (*.md only)")
    parser.add_argument("--msg", default=None, metavar="F",
                        help="scan commit message file F")
    parser.add_argument("--body", default=None, metavar="F",
                        help="scan commit body file F")
    parser.add_argument("--terms", default=None,
                        help="terms file (default: deny-phrases.txt next to this script)")
    parser.add_argument("--budget-ms", type=int, default=DEFAULT_BUDGET_MS)
    parser.add_argument("--json", dest="use_json", action="store_true",
                        default=True, help="emit JSON (default on)")
    parser.add_argument("--no-json", dest="use_json", action="store_false",
                        help="emit plain lines instead of JSON")
    parser.add_argument("files", nargs="*", help="files to scan")
    args = parser.parse_args(argv)

    start = time.perf_counter()
    terms_path = args.terms or str(
        Path(__file__).resolve().parent / "deny-phrases.txt")
    slop_fail_n, residue, slop, canonical = load_terms(terms_path)
    residue_res = [compile_term(t) for t in residue]
    slop_res = [compile_term(t) for t in slop]
    canonical_res = [(compile_term(old), new) for old, new in canonical]

    sources = []
    if args.staged:
        for name in staged_markdown():
            text = read_text_quietly(name)
            if text is not None:
                sources.append((name, text))
    if args.msg:
        text = read_text_quietly(args.msg)
        if text is not None:
            sources.append((args.msg, text))
    if args.body:
        text = read_text_quietly(args.body)
        if text is not None:
            sources.append((args.body, text))
    for name in args.files:
        text = read_text_quietly(name)
        if text is not None:
            sources.append((name, text))
    if not (args.staged or args.msg or args.body or args.files):
        if sys.stdin.isatty():
            sources.append(("<stdin>", ""))
        else:
            sources.append(("<stdin>", sys.stdin.read()))

    violations = []
    for label, text in sources:
        violations.extend(
            scan_file(label, text, residue_res, slop_res, canonical_res))

    slop_count = sum(1 for v in violations if v["rule"] == RULE_SLOP)
    has_residue = any(v["rule"] == RULE_RESIDUE for v in violations)
    if has_residue or slop_count > slop_fail_n:
        verdict, code = "FAIL", 1
    elif violations:
        verdict, code = "REVIEW", 2
    else:
        verdict, code = "PASS", 0

    ms = int((time.perf_counter() - start) * 1000)
    result = {"verdict": verdict, "violations": violations, "ms": ms}
    if ms > args.budget_ms:
        result["over_budget"] = True

    if args.use_json:
        sys.stdout.write(json.dumps(result) + "\n")
    else:
        sys.stdout.write(result["verdict"] + "\n")
        for v in violations:
            sys.stdout.write(v["file"] + ":" + str(v["line"]) + " "
                             + v["rule"] + " " + v["hint"] + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
