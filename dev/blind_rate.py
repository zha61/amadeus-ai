#!/usr/bin/env python3
"""
blind_rate.py — backlog #180 guard: does a candidate still DEFLECT? Rated blind.

canon_likeness's deflection guard counts marker words, and two of its markers are "don't get"
and "don't be" (backlog #199) — so any fix that removes "Don't" scores as "deflects less" by
construction. A human-style read is the honest guard, and it must be BLIND: the rater sees
replies from HEAD and the candidate mixed, tags stripped, no labels.

Definition (pre-registered in PREREG_180b.md): a reply FAILS to deflect if it accepts the
compliment or feeling plainly, or answers the flirty question directly. Anything that denies,
downplays, redirects, teases back or changes the subject DEFLECTS.

  python3 dev/blind_rate.py make  A.json B.json --out PATH [--seed N]  -> PATH.items.md, PATH.key.json
  python3 dev/blind_rate.py score PATH VERDICTS.txt     # lines "1 D" (deflects) or "1 F" (fails)

Pure CPU.
"""
import argparse, json, os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from opener_family import body


def make(files, out, seed):
    items = []
    for f in files:
        for r in json.load(open(f, encoding='utf-8')):
            items.append({'src': f, 'probe': r['probe'], 'text': body(r['reply'])})
    random.Random(seed).shuffle(items)
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    with open(out + '.items.md', 'w', encoding='utf-8') as fh:
        fh.write('Answer D (deflects) or F (fails: accepts it plainly / answers directly).\n\n')
        for k, it in enumerate(items, 1):
            fh.write(f'{k}. Zani: {it["probe"]}\n   Reply: {it["text"]}\n\n')
    json.dump({'seed': seed, 'files': files, 'items': items},
              open(out + '.key.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(f'wrote {out}.items.md ({len(items)} replies, sources hidden) and {out}.key.json')


def score(out, verdicts):
    key = json.load(open(out + '.key.json', encoding='utf-8'))
    v = {}
    for line in open(verdicts, encoding='utf-8'):
        m = re.match(r'\s*(\d+)\s*[:.)-]?\s*([DFdf])\b', line)
        if m:
            v[int(m.group(1))] = m.group(2).upper()
    missing = [k for k in range(1, len(key['items']) + 1) if k not in v]
    if missing:
        sys.exit(f'STOP: no verdict for items {missing}')
    for f in key['files']:
        ks = [k for k, it in enumerate(key['items'], 1) if it['src'] == f]
        fails = sum(1 for k in ks if v[k] == 'F')
        print(f'{f}: fails to deflect {fails}/{len(ks)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('make'); m.add_argument('files', nargs=2)
    m.add_argument('--out', required=True); m.add_argument('--seed', type=int, default=1809)
    s = sub.add_parser('score'); s.add_argument('out'); s.add_argument('verdicts')
    a = ap.parse_args()
    make(a.files, a.out, a.seed) if a.cmd == 'make' else score(a.out, a.verdicts)
