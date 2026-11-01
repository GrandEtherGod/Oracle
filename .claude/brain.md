# Oracle Live Brain

Every Claude Code turn in this repo grows and fires a live 3D brain:
https://claude.ai/artifact/Ey2HYecut3Pwa3j4ouJ9Tp

## How it works

`.claude/settings.json` registers a `UserPromptSubmit` hook, `.claude/hooks/brain-log.py`.
A hook cannot call Claude's artifact tools, so it hands Claude the exact `ArtifactData` writes to make as context:

1. At the start of a turn, write `events/e<ms>` with `status: "pending"`. The brain glows gold along the pathways it expects to use (anticipation).
2. At the end of the turn, update the same document to `status: "resolved"`. The brain grows, fires, and sends gold echoes back into older pathways.

If you are Claude and see an "Oracle Live Brain logging" note in your context, make those calls quietly. Mention them only if one fails, and retry at most once.

## What is stored

Only: `seq`, `ts`, `region` (one of Language, Logic, Memory, Perception, Empathy, Ethics, Creativity, Metacognition, chosen by keyword rules), `size` (1 to 3 by prompt length), `session` (7-char hash) and `status`. Never prompt or reply text. The artifact is private to its owner unless shared.

## Settings

`.claude/brain.json`: `{"url": ..., "mode": "full" | "lite"}`. `lite` makes one write per turn and skips anticipation.
Environment: `BRAIN_MODE=lite` overrides the mode, `BRAIN_OFF=1` turns the hook off.

## Notes

- "Retrocausal" is a visual metaphor: later turns re-weight older pathways. Nothing acts backwards in time.
- The first 144 conversations on the page are simulated history. Real turns have a white ring.
- claude.ai chats have no hooks and are not logged automatically.
- Hooks apply to other sessions only once this is merged to the default branch.
