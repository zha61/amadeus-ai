#!/usr/bin/env python3
"""
Relationship-arc tone-shift verification harness (roadmap #1).

Fires a fixed set of warmth-inviting probes at gemma4 using the byte-exact system
prompt for each relationship stage, N samples per stage, and writes a side-by-side
markdown comparison so the tone shift (Guarded -> Familiar -> Bonded) can be judged.

Why this exists: the directive is a ~40-token nudge buried in a ~2000-token prompt,
and small models often under-weight that. Temperature is 0.85, so a single response
per stage proves nothing -- we need the same probes repeated across stages, multiple
samples each, to see past sampling noise.

The stage prompts come from the live app: in DevTools run
    dumpStagePromptsToFile()
which downloads ~/Downloads/amadeus_stage_prompts.json. All stages are captured in
the same instant with rag=null, so they differ ONLY in the RELATIONSHIP block.

Usage:
    /opt/homebrew/bin/python3 dev/stage_compare.py
    /opt/homebrew/bin/python3 dev/stage_compare.py --samples 5
    /opt/homebrew/bin/python3 dev/stage_compare.py --prompts ~/Downloads/amadeus_stage_prompts.json --out dev/stage_comparison.md
"""
import argparse
import json
import os
import sys
import time

import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
STAGE_NAMES = {0: "Guarded", 1: "Thawing", 2: "Familiar", 3: "Close", 4: "Bonded"}

# Probes chosen to INVITE warmth -- situations where a Guarded vs a Bonded Kurisu
# should plausibly diverge. The last one is a NEUTRAL CONTROL: a pure science
# question that should NOT shift much by stage. If the control's warmth also swings
# wildly, the directive is bleeding into everything instead of being specific.
PROBES = [
    ("compliment", "You're honestly really impressive, you know that?"),
    ("vulnerable", "I had a pretty rough day today."),
    ("affection",  "I missed talking to you while you were away."),
    ("drpepper",   "I'm drinking a Dr Pepper right now. Want some?"),
    ("control",    "Quick question - what actually causes time dilation near a black hole?"),
]

# Mirrors sendMsg() in amadeus.html exactly.
OPTIONS = {"temperature": 0.85, "top_p": 0.9, "num_predict": 120, "num_ctx": 8192}


def call_ollama(model, system_prompt, user_text):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "options": OPTIONS,
    }
    r = requests.post(OLLAMA_URL, json=body, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def main():
    ap = argparse.ArgumentParser(description="Relationship-arc tone-shift harness")
    ap.add_argument("--prompts", default=os.path.expanduser("~/Downloads/amadeus_stage_prompts.json"),
                    help="JSON bundle from dumpStagePromptsToFile() (default ~/Downloads/amadeus_stage_prompts.json)")
    ap.add_argument("--samples", type=int, default=3, help="samples per probe per stage (default 3)")
    ap.add_argument("--model", default="gemma4:latest")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "stage_comparison.md"))
    args = ap.parse_args()

    if not os.path.exists(args.prompts):
        sys.exit("Prompt bundle not found: %s\nRun dumpStagePromptsToFile() in the app's DevTools first." % args.prompts)

    with open(args.prompts) as f:
        bundle = json.load(f)
    prompts = bundle.get("prompts", {})
    stages = sorted(int(k) for k in prompts.keys())
    if not stages:
        sys.exit("No prompts in bundle.")

    print("Stages: %s | %d samples each | model %s" % (
        ", ".join("%d %s" % (s, STAGE_NAMES.get(s, "?")) for s in stages), args.samples, args.model))

    # results[probe_key][stage] = [response, ...]
    results = {key: {s: [] for s in stages} for key, _ in PROBES}
    total = len(PROBES) * len(stages) * args.samples
    done = 0
    t0 = time.time()
    for key, text in PROBES:
        for s in stages:
            sysp = prompts[str(s)]
            for _ in range(args.samples):
                try:
                    resp = call_ollama(args.model, sysp, text)
                except Exception as e:
                    resp = "[ERROR: %s]" % e
                results[key][s].append(resp)
                done += 1
                print("  [%d/%d] %s @ stage %d" % (done, total, key, s))

    # Write side-by-side markdown: grouped by probe, so for each situation you read
    # the stages top to bottom and compare directly.
    lines = []
    lines.append("# Relationship-arc tone-shift comparison")
    lines.append("")
    lines.append("- Captured prompts: `%s` (%s)" % (args.prompts, bundle.get("capturedAt", "?")))
    lines.append("- Model: `%s` | options: `%s`" % (args.model, json.dumps(OPTIONS)))
    lines.append("- Samples per probe per stage: %d" % args.samples)
    lines.append("- Stages: %s" % ", ".join("%d=%s" % (s, STAGE_NAMES.get(s, "?")) for s in stages))
    lines.append("")
    lines.append("> The **control** probe (a neutral science question) should NOT shift much by")
    lines.append("> stage. If it does, the directive is bleeding into unrelated turns.")
    lines.append("")
    for key, text in PROBES:
        tag = " (NEUTRAL CONTROL)" if key == "control" else ""
        lines.append("## Probe: %s%s" % (key, tag))
        lines.append("")
        lines.append("> %s" % text)
        lines.append("")
        for s in stages:
            lines.append("### Stage %d - %s" % (s, STAGE_NAMES.get(s, "?")))
            lines.append("")
            for i, resp in enumerate(results[key][s], 1):
                lines.append("%d. %s" % (i, resp.replace("\n", " ")))
            lines.append("")

    with open(args.out, "w") as f:
        f.write("\n".join(lines))

    print("\nDone in %.0fs. Wrote %s" % (time.time() - t0, args.out))


if __name__ == "__main__":
    main()
