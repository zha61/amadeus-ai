#!/usr/bin/env python3
"""
opener_stage_table.py — backlog #180: score a stage's arms against the PRE-REGISTERED bars
in dev/canon_arms/PREREG_180.md, paired against that stage's HEAD run. Pure CPU.

  python3 dev/opener_stage_table.py S1 dev/canon_arms/S1_HEAD.txt.json \
      G=opener_g:dev/canon_arms/S1_opener_g.txt.json F=opener_f:dev/canon_arms/S1_opener_f.txt.json

Committed so the Stage 2 verdict can be re-derived, not trusted (bugs.md 86 / the heredoc lesson).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opener_family as o
from collections import Counter
prefix, base_file = sys.argv[1], sys.argv[2]
arms = [a.split('=') for a in sys.argv[3:]]
base = json.load(open(base_file)); bm = dict(zip(o.pair_keys(base), base))
rows = []
for name, spec in [('HEAD', 'HEAD:' + base_file)] + [(n, s) for n, s in arms]:
    arm, f = spec.split(':', 1)
    arm = None if arm == 'HEAD' else arm
    R = json.load(open(f))
    s = o.score([r['reply'] for r in R], o.prompt_ngrams(arm), [r['probe'] for r in R])
    g4 = s['ngram4'][0][1]
    if arm:
        _, _, p = o.mcnemar_one_sided([(o.first_word(bm[k]['reply']) in o.CRUTCH,
                                        o.first_word(r['reply']) in o.CRUTCH)
                                       for k, r in zip(o.pair_keys(R), R) if k in bm])
        _, mean, lo, hi = o.paired_length(base, R)
    else:
        p = mean = lo = hi = float('nan')
    bars = {'crutch<=15': s['crutch'] <= 15, 'top1<=5': s['top1'] <= 5, 'distinct>=20': s['distinct'] >= 20,
            'shortq<=6': s['shortq'] <= 6, '4gram<=5': g4 <= 5, 'tag>=26': s['tagok'] >= 26,
            'notag<=1': s['notag'] <= 1, 'McNemar p<.05': p < 0.05, 'not shorter': not (hi < 0)}
    tags = Counter(o.tag_of(r['reply']) for r in R)
    rows.append((name, s, g4, p, mean, lo, hi, bars, tags))
W = 10
print(f"{'':24}" + ''.join(f'{r[0]:>{W}}' for r in rows))
def line(lab, vals): print(f'{lab:24}' + ''.join(f'{v:>{W}}' for v in vals))
line('crutch family [<=15]', [r[1]['crutch'] for r in rows])
line('  what / dont', [f"{r[1]['fam']['what']}/{r[1]['fam'][chr(100)+'on'+chr(39)+'t']}" for r in rows])
for k, lab in [('top1', 'top first word [<=5]'), ('distinct', 'distinct first [>=20]'), ('shortq', '<=4w q-opener [<=6]'),
               ('echo', 'echo-question'), ('echo_any', 'echo any form'), ('later_dont', 'later dont'), ('stammer', 'stammer anywhere'),
               ('qend', 'ends on ?'), ('tagok', 'tag flu|tsu [>=26]'), ('notag', 'tag missing [<=1]'), ('copies', 'prompt copies')]:
    line(lab, [r[1][k] for r in rows])
line('widest 4-gram [<=5]', [r[2] for r in rows])
line('McNemar p', [f'{r[3]:.4f}' for r in rows])
line('length diff mean', [f'{r[4]:+.1f}' for r in rows])
line('length 95% CI', ['' if r[0] == 'HEAD' else f'{r[5]:+.1f}..{r[6]:+.1f}' for r in rows])
for r in rows:
    fails = [k for k, v in r[7].items() if not v] if r[0] != 'HEAD' else None
    print(f"{r[0]:5} tags {dict(r[8])}  4-gram {r[1]['ngram4'][0]}" + ('' if fails is None else f"  FAILS {fails or 'none -> ELIGIBLE'}"))
