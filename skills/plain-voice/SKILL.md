---
name: plain-voice
description: >
  Write documents and chat output in plain artifact voice: full sentences,
  full words, concrete actors and actions, each claim beside its evidence.
  Use when drafting or reviewing docs, commit messages, PR bodies, chat
  summaries, or any prose that must read clean six months out. Replaces
  terse compressed modes for anything another person will read later.
license: MIT
metadata:
  version: "0.1.0"
---

# Plain voice

Write for a stranger opening this cold: full sentences, full words,
concrete actors and actions. Keep each artifact self-contained, with
context restated inside. State each claim beside its evidence, number,
or file path. Match wording and detail to the reader's stated level.
Give comments as the reason behind the choice and the alternative
passed over.

Deeper checks live in the humanizer skill. Fast checks run through
the hygiene gate below. Neither replaces the paragraph above; both
enforce it.

## Rewrite process

1. Read the source and mark each AI pattern (humanizer sections 1-35).
2. Write a draft. Read it aloud. Check rhythm, details, simple verbs
   such as is and has, and the right level of formality.
3. Ask two questions: what still sounds AI-generated, and did the
   rewrite add or remove any fact, name, number, date, quote,
   citation, ranking, or other claim. Treat any unsupported addition
   or lost claim as an error.
4. Write the final version. State each point naturally instead of
   patching one flagged phrase at a time.

## Chat output

Chat replies follow the same voice. Conclusion first, then evidence.
Fragments only when clearer than a full sentence. No ceremony, no
hedging, no summary paragraph restating what the reply already said.
The final rewrite must not contain em dashes or en dashes; use a
period, comma, colon, or parentheses instead.

## Hygiene gate

The gate keeps markdown artifacts in plain voice: direct wording,
specific terms, canonical phrasing. It scans files or piped prose and
reports rule ids with repair hints.

```sh
python3 scripts/hygiene_gate.py notes.md
cat draft.md | python3 scripts/hygiene_gate.py
python3 scripts/hygiene_gate.py --staged
python3 scripts/hygiene_gate.py --msg COMMIT_MSG --body COMMIT_BODY
```

| Verdict | Meaning                       | Exit |
| ------- | ----------------------------- | ---- |
| PASS    | artifact reads in plain voice | 0    |
| REVIEW  | polish flagged wording, retry | 2    |
| FAIL    | rework flagged lines, re-run  | 1    |

A FAIL result blocks the change: a residue hit, or more than 3
wording hits, stops the line. For repairs, use the rewrite process
above.

Terms live in `scripts/deny-phrases.txt` (`--terms` overrides the
path); the runner is `scripts/hygiene_gate.py`. The gate uses the
standard library only with a 50 ms budget (`--budget-ms`);
over-budget runs report REVIEW with `over_budget:true`. JSON output
carries rule ids and hints only, so draft text stays private.
