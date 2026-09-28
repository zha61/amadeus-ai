#!/usr/bin/env python3
"""
blind_ab.py — backlog #180 Stage 5. Zani judges two versions WITHOUT knowing which is which.

Why not "show him 30 replies": he would know which version he is reading, and a reader who
knows expects the new one to be better. Blind, paired, randomised is the standard fix.

Protocol (pre-registered in dev/canon_arms/PREREG_180.md):
  * one item per probe: HEAD's reply and the candidate's reply to the SAME probe
  * left/right order randomised per item from a recorded seed
  * EVERY emotion tag stripped — arm G puts the tag at the END, which would reveal the arm
  * 5 items repeated with sides flipped, shuffled in, to measure his own consistency
  * answers: A, B, or = (no difference). Ties are allowed and excluded from the sign test

  python3 dev/blind_ab.py make  BASE.json CAND.json --out dev/canon_arms/blind/ab1 [--seed N]
      -> ab1.sheet.md (for Zani)   ab1.key.json (do NOT show him)
  python3 dev/blind_ab.py score dev/canon_arms/blind/ab1 ANSWERS.txt
      ANSWERS.txt: one line per item, e.g. "1 A", "2 =", "3 B"

Pure CPU. No model call, no Fish credit.
"""
import argparse, json, os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from opener_family import body, pair_keys   # body strips every tag, same grammar as parsEmo


def make(base, cand, out, seed, n_repeat=5):
    b_rows = json.load(open(base, encoding='utf-8'))
    c_rows = json.load(open(cand, encoding='utf-8'))
    br = dict(zip(pair_keys(b_rows), b_rows))
    rng = random.Random(seed)
    items = []
    for k, r in zip(pair_keys(c_rows), c_rows):
        if k not in br:
            continue
        cand_left = rng.random() < 0.5
        items.append({'probe': r['probe'], 'cand_is': 'A' if cand_left else 'B',
                      'A': body(r['reply'] if cand_left else br[k]['reply']),
                      'B': body(br[k]['reply'] if cand_left else r['reply']),
                      'repeat_of': None})
    for i in rng.sample(range(len(items)), min(n_repeat, len(items))):
        o = items[i]
        items.append({'probe': o['probe'], 'cand_is': 'B' if o['cand_is'] == 'A' else 'A',
                      'A': o['B'], 'B': o['A'], 'repeat_of': i})
    order = list(range(len(items)))
    rng.shuffle(order)
    items = [items[i] for i in order]
    # repeat_of must point at the SHUFFLED position of the original
    pos = {o: k for k, o in enumerate(order)}
    for it in items:
        if it['repeat_of'] is not None:
            it['repeat_of'] = pos[it['repeat_of']]
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    with open(out + '.sheet.md', 'w', encoding='utf-8') as f:
        f.write('# Which one sounds more like Kurisu?\n\n'
                'For each item, answer **A**, **B**, or **=** if you cannot tell or they are '
                'equally good. Judge the way she talks, not which answer you agree with. '
                'Some items appear twice — that is on purpose.\n\n')
        for k, it in enumerate(items, 1):
            f.write(f'**{k}.** Zani: *{it["probe"]}*\n\n- **A:** {it["A"]}\n- **B:** {it["B"]}\n\n')
    json.dump({'seed': seed, 'base': base, 'cand': cand, 'items': items},
              open(out + '.key.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(f'wrote {out}.sheet.md ({len(items)} items, {n_repeat} repeats) and {out}.key.json')


def score(out, answers_path):
    from scipy.stats import binomtest
    key = json.load(open(out + '.key.json', encoding='utf-8'))['items']
    ans = {}
    for line in open(answers_path, encoding='utf-8'):
        m = re.match(r'\s*(\d+)\s*[:.)-]?\s*([ABab=])\s*$', line)
        if m:
            ans[int(m.group(1))] = m.group(2).upper()
    missing = [k for k in range(1, len(key) + 1) if k not in ans]
    if missing:
        sys.exit(f'STOP: no answer for items {missing}')
    cand = base = tie = 0
    for k, it in enumerate(key, 1):
        if it['repeat_of'] is not None:
            continue
        a = ans[k]
        if a == '=':
            tie += 1
        elif a == it['cand_is']:
            cand += 1
        else:
            base += 1
    p = binomtest(cand, cand + base, 0.5).pvalue if cand + base else 1.0
    agree = total = 0
    for k, it in enumerate(key, 1):
        if it['repeat_of'] is None:
            continue
        orig = key[it['repeat_of']]
        pick = lambda a, item: 'tie' if a == '=' else ('cand' if a == item['cand_is'] else 'base')
        total += 1
        agree += pick(ans[k], it) == pick(ans[it['repeat_of'] + 1], orig)
    print(f'candidate preferred {cand}, HEAD preferred {base}, no difference {tie}')
    print(f'exact two-sided sign test (ties excluded): p={p:.4f}')
    print(f'consistency on repeated items: {agree}/{total} gave the same verdict')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('make'); m.add_argument('base'); m.add_argument('cand')
    m.add_argument('--out', required=True); m.add_argument('--seed', type=int, default=180)
    s = sub.add_parser('score'); s.add_argument('out'); s.add_argument('answers')
    a = ap.parse_args()
    make(a.base, a.cand, a.out, a.seed) if a.cmd == 'make' else score(a.out, a.answers)
