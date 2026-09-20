# pi-plain-voice

Plain artifact voice for Pi. One extension plus one skill. The extension
injects the voice rules into chat; the skill rewrites drafts and checks
them with a fast stdlib-only gate.

This package replaces the earlier caveman terse mode. Caveman compressed
prose by dropping articles and filler. That saved tokens but read as
compressed chat, not as a document. Plain voice keeps full sentences and
full words, stated for a stranger opening the artifact cold. It reads
slower to write and faster to reuse six months out.

## What it contains

- `extensions/plain-voice.ts`: appends the voice rules to the system
  prompt on `before_agent_start`; adds a `/voice` command to check or
  relax enforcement for one turn.
- `skills/plain-voice/SKILL.md`: the same rules as a loadable skill,
  plus rewrite and gate instructions. Used by the extension and by
  other agents that read skills instead of extensions.
- `skills/plain-voice/scripts/hygiene_gate.py`: the stdlib-only gate.
  Reads files or stdin, reports PASS, REVIEW, or FAIL as JSON. Rule
  ids and hints only, so draft text stays on the machine.
- `skills/plain-voice/scripts/deny-phrases.txt`: the gate term lists.

## Install

Local path, for development:

```sh
pi install /Users/bradley_mankoff/Developer/personal_code/pi-plain-voice
```

Git, once published:

```sh
pi install git:github.com/bradley-mankoff/pi-plain-voice
```

## Wire at the root

The package is also wired outside the repo at the root, as if a future
project had said it in action. The wiring lives in `AGENTS.md` files
and points at `skill://plain-voice`, which resolves to this repo's
`skills/plain-voice/SKILL.md`:

- `~/AGENTS.md` carries the one-paragraph contract.
- `~/.omp/agent/AGENTS.md` names the same voice for factory work.

Hygiene gate scripts stay manual. No hook or extension runs them
automatically; the agent runs the gate before committing docs or
sending prose drafts.

## License

MIT. The bundled humanizer rules derive from
[Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
maintained by WikiProject AI Cleanup.
