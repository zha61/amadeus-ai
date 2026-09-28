#!/usr/bin/env python3
"""
model_compare.py — gemma4:latest vs qwen3.5:9b bake-off for the Amadeus brain.

System prompt is extracted LIVE from amadeus.html (the SYSTEM_PROMPT template
literal + the stage-2 RELATIONSHIP directive, mirroring buildSystemPrompt) —
always current, no stale DevTools bundle needed. Same probes, N samples each.
Runs MODEL-MAJOR (all of one model, then all of the other) — both models can't
co-reside in 16GB RAM, so this costs exactly one load per model.

Probes = 4 stage-harness probes + 2 real-world naturalness failures from
Zani's testing (the screenshot cases the brain upgrade must fix).

Usage: /opt/homebrew/bin/python3 dev/model_compare.py [--samples 3] [--stage 2]
"""
import argparse, json, os, re, time
import requests

AMADEUS_HTML = os.path.join(os.path.dirname(__file__), '..', 'amadeus.html')

def build_system_prompt(stage):
    """Extract SYSTEM_PROMPT literal + inject the stage RELATIONSHIP directive
    before TWO MODES — mirrors buildSystemPrompt() (memory/time/rag omitted:
    identical for both models, so a fair A/B without them)."""
    html = open(AMADEUS_HTML, encoding='utf-8').read()
    m = re.search(r'const SYSTEM_PROMPT=`(.*?)`\n', html, re.S)
    if not m:
        raise SystemExit('SYSTEM_PROMPT literal not found in amadeus.html')
    prompt = m.group(1)
    dm = re.findall(r'"RELATIONSHIP\\n(.*?)"', html, re.S)
    if dm and stage < len(dm):
        directive = 'RELATIONSHIP\n' + dm[stage].replace('\\n', '\n')
        prompt = prompt.replace('\nTWO MODES\n', '\n' + directive + '\n\nTWO MODES\n', 1)
    return prompt

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

PROBES = [
    ("compliment", "You're honestly really impressive, you know that?"),
    ("vulnerable", "I had a pretty rough day today."),
    ("affection",  "I missed talking to you while you were away."),
    ("game_money", "I'm building a game from scratch to make money."),
    ("japan",      "I'm in Japan right now."),
    ("control",    "Quick question - what actually causes time dilation near a black hole?"),
]
# drpepper probe dropped: the curated canon pool intercepts it before the LLM in
# the live app, so model behaviour there no longer matters.

OPTIONS = {"temperature": 0.85, "top_p": 0.9, "num_predict": 120, "num_ctx": 8192}
THINK_RE = [re.compile(r'<\|channel>thought[\s\S]*?<channel\|>', re.I),
            re.compile(r'<think>[\s\S]*?</think>', re.I)]

def call(model, system_prompt, user_text):
    body = {"model": model,
            "messages": [{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_text}],
            "stream": False, "think": False, "keep_alive": "10m", "options": OPTIONS}
    t0 = time.time()
    r = requests.post(OLLAMA_URL, json=body, timeout=300)
    r.raise_for_status()
    d = r.json()
    text = d["message"]["content"].strip()
    for rx in THINK_RE:
        text = rx.sub('', text).strip()
    tok_s = 0.0
    if d.get("eval_count") and d.get("eval_duration"):
        tok_s = d["eval_count"] / (d["eval_duration"] / 1e9)
    return text, time.time() - t0, tok_s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--stage", type=int, default=2, help="relationship stage directive to use (default 2 Familiar)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "model_comparison.md"))
    args = ap.parse_args()

    sys_prompt = build_system_prompt(args.stage)
    print(f"System prompt: {len(sys_prompt)} chars (stage {args.stage} directive injected)")

    models = ["gemma4:latest", "qwen3.5:9b"]
    results = {m: {} for m in models}   # model -> probe -> [(text, secs, tok_s)]
    for m in models:                     # MODEL-MAJOR: one load per model
        print(f"\n### {m}")
        for pid, ptext in PROBES:
            results[m][pid] = []
            for i in range(args.samples):
                text, secs, tok_s = call(m, sys_prompt, ptext)
                results[m][pid].append((text, secs, tok_s))
                print(f"  {pid:11s} #{i+1} {secs:5.1f}s {tok_s:5.1f}tok/s | {text[:80]}")

    lines = [f"# Model bake-off — gemma4:latest vs qwen3.5:9b",
             f"Stage {args.stage} prompt, {args.samples} samples/probe, options={OPTIONS}", ""]
    for pid, ptext in PROBES:
        lines += [f"## {pid}: \"{ptext}\"", ""]
        for m in models:
            lines.append(f"### {m}")
            for i, (text, secs, tok_s) in enumerate(results[m][pid]):
                lines.append(f"{i+1}. ({secs:.1f}s, {tok_s:.0f} tok/s) {text}")
            lines.append("")
    # speed summary
    lines.append("## Speed summary")
    for m in models:
        all_calls = [c for probe in results[m].values() for c in probe]
        mean_s = sum(c[1] for c in all_calls) / len(all_calls)
        mean_t = sum(c[2] for c in all_calls) / len(all_calls)
        lines.append(f"- {m}: mean {mean_s:.1f}s/reply, {mean_t:.0f} tok/s")
    open(args.out, "w").write("\n".join(lines))
    print(f"\nWrote {args.out}")

if __name__ == "__main__":
    main()
