#!/usr/bin/env python3
"""UserPromptSubmit hook: log each turn to the Oracle Live Brain.

A hook cannot call the Artifact tools, so it hands Claude the exact database
writes to make as additionalContext. Only a faculty, a size bucket, a time and a
short session tag are stored. The prompt text is never written anywhere.

Settings: .claude/brain.json {"url": ..., "mode": "full" | "lite"}.
  full  pending write at the start of the turn, resolved write at the end
        (live anticipation, then confirmation and echo)
  lite  one resolved write at the end of the turn
Env: BRAIN_MODE overrides the mode, BRAIN_OFF=1 disables the hook.
Fails open: any error prints nothing and exits 0.
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

# Keyword rules per faculty, checked in order. First strongest match wins.
RULES = [
    ("Memory", r"\b(remember|recall|history|log|cache|store|persist|database|db|backup|restore|context|memory)\b"),
    ("Logic", r"\b(test|debug|bug|fix|error|fail|algorithm|logic|proof|compute|calculate|refactor|type|lint|build|compile)\b"),
    ("Perception", r"\b(read|look|see|view|screenshot|image|render|inspect|scan|search|find|parse|log output|display)\b"),
    ("Creativity", r"\b(design|create|imagine|invent|generate|draw|art|story|brainstorm|idea|prototype|style|visual)\b"),
    ("Empathy", r"\b(user|people|team|feel|customer|help|support|kind|care|tone|review comment|feedback)\b"),
    ("Ethics", r"\b(safe|safety|secure|security|privacy|permission|policy|should|ethic|risk|compliance|consent|trust|harm)\b"),
    ("Metacognition", r"\b(plan|reflect|think|why|how do you|your own|yourself|learn|evolve|consciousness|asi|awareness|meta)\b"),
    ("Language", r"\b(write|explain|translate|summar|document|docs|readme|comment|email|message|word|text|prose)\b"),
]


def classify(prompt: str) -> str:
    low = prompt.lower()
    best, score = "Language", 0
    for region, pat in RULES:
        n = len(re.findall(pat, low))
        if n > score:
            best, score = region, n
    return best


def main() -> None:
    if os.environ.get("BRAIN_OFF") == "1":
        return
    data = json.load(sys.stdin)
    prompt = (data.get("prompt") or "").strip()
    if len(prompt) < 4 or prompt.startswith("/"):
        return
    cfg = json.loads((Path(__file__).resolve().parent.parent / "brain.json").read_text())
    url, mode = cfg["url"], os.environ.get("BRAIN_MODE") or cfg.get("mode", "full")
    ts = int(time.time() * 1000)
    size = 1 if len(prompt) < 200 else 2 if len(prompt) < 1200 else 3
    sess = hashlib.sha1((data.get("session_id") or "").encode()).hexdigest()[:7]
    doc = {"seq": ts, "ts": ts, "region": classify(prompt), "size": size, "session": sess}
    ev = f"e{ts}"
    call = lambda d, extra="": (  # noqa: E731
        f'ArtifactData(action="set", url="{url}", collection="events", doc_id="{ev}", data={json.dumps(d)}{extra})'
    )
    if mode == "lite":
        steps = f"After finishing the work and before your final reply, run: {call({**doc, 'status': 'resolved'})}"
    else:
        steps = (
            f"1. Now, before other work, run: {call({**doc, 'status': 'pending'})} and note the returned version.\n"
            f'2. After finishing the work and before your final reply, run: ArtifactData(action="update", url="{url}", '
            f'collection="events", doc_id="{ev}", if_version=<version from step 1>, data={{"status": "resolved"}}).'
        )
    msg = (
        "Oracle Live Brain logging for this turn (automatic, configured in .claude/brain.json). "
        "Use the ArtifactData tool (load it with ToolSearch if needed). Do it quietly; mention it to the user only if a call fails, "
        "and never retry more than once.\n" + steps
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
