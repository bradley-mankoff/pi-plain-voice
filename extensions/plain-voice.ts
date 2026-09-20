/**
 * plain-voice — enforce plain artifact voice in Pi chat.
 *
 * Appends the voice rules to the system prompt on `before_agent_start`
 * so every turn writes for a stranger opening the artifact cold: full
 * sentences, full words, concrete actors, each claim beside its
 * evidence. `/voice` reports state; `/voice strict|relaxed|off`
 * changes enforcement for this session only.
 *
 * No automatic rewriting and no automatic gate runs. The agent rewrites
 * on request via skill `plain-voice` and runs
 * `skills/plain-voice/scripts/hygiene_gate.py` before committing docs
 * or sending prose drafts.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const VOICE = [
	"Plain artifact voice: write for a stranger opening this cold.",
	"Full sentences, full words, concrete actors and actions.",
	"Keep each artifact self-contained, with context restated inside.",
	"State each claim beside its evidence, number, or file path.",
	"Match wording and detail to the reader's stated level.",
	"Give comments as the reason behind the choice and the alternative passed over.",
	"Conclusion first, then evidence. No ceremony, hedging, or summary restatement.",
	"No em dashes or en dashes in the final text; use a period, comma, colon, or parentheses.",
	"Deeper checks: skill plain-voice (humanizer patterns). Fast check: skills/plain-voice/scripts/hygiene_gate.py.",
].join("\n");

type Mode = "strict" | "relaxed" | "off";

export default function plainVoiceExtension(pi: ExtensionAPI): void {
	let mode: Mode = "strict";

	pi.on("before_agent_start", async (event) => {
		if (mode === "off") return;
		const extra =
			mode === "strict"
				? `\n\n${VOICE}`
				: "\n\nPlain artifact voice (relaxed): full sentences, concrete actors, claims beside evidence.";
		return { systemPrompt: event.systemPrompt + extra };
	});

	pi.registerCommand("voice", {
		description: "Show or set plain-voice enforcement (strict|relaxed|off, session only)",
		handler: async (args, ctx) => {
			const want = args.trim().toLowerCase();
			if (want === "strict" || want === "relaxed" || want === "off") {
				mode = want;
				ctx.ui.notify(`plain-voice: ${mode}`, "info");
				return;
			}
			ctx.ui.notify(`plain-voice: ${mode} (strict|relaxed|off)`, "info");
		},
	});
}
