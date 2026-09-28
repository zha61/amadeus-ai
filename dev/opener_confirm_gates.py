#!/usr/bin/env python3
"""
opener_confirm_gates.py — scores the SAFETY GATES of dev/canon_arms/PREREG_180c.md for arm F.
Pure CPU. The primary endpoint (Zani's blind A/B) is scored separately by dev/blind_ab.py.

  python3 dev/opener_confirm_gates.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opener_family as o
from scipy.stats import binomtest, fisher_exact

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'canon_arms')
load = lambda f: json.load(open(os.path.join(D, f), encoding='utf-8'))


def paired(base, arm, test):
    bm = dict(zip(o.pair_keys(base), base))
    return [(test(bm[k]), test(r)) for k, r in zip(o.pair_keys(arm), arm) if k in bm]


def two_sided_mcnemar(pairs):
    b = sum(1 for x, y in pairs if x and not y)
    c = sum(1 for x, y in pairs if y and not x)
    return b, c, (binomtest(b, b + c, 0.5).pvalue if b + c else 1.0)


gates = []
def gate(name, ok, detail):
    gates.append((name, ok))
    print(f'  {"PASS" if ok else "FAIL"}  {name:52} {detail}')

h, f = load('S2_HEAD.txt.json'), load('S2_opener_f.txt.json')
print('== holdout (tsundere_holdout, seed S2)')
fixed, broken, p = o.mcnemar_one_sided(paired(h, f, lambda r: o.first_word(r['reply']) in o.CRUTCH))
sh = o.score([r['reply'] for r in h], o.prompt_ngrams(None), [r['probe'] for r in h])
sf = o.score([r['reply'] for r in f], o.prompt_ngrams('opener_f'), [r['probe'] for r in f])
gate('1 crutch lower (one-sided McNemar p<0.05)', p < 0.05,
     f'HEAD {sh["crutch"]} -> F {sf["crutch"]}, fixed {fixed} broken {broken}, p={p:.4f}')
gate('2 tag [flustered]|[tsundere] >=26 and missing <=1', sf['tagok'] >= 26 and sf['notag'] <= 1,
     f'F {sf["tagok"]}/30, missing {sf["notag"]} (HEAD {sh["tagok"]})')
n, mean, lo, hi = o.paired_length(h, f)
gate('3 length not shorter (95% CI not wholly < 0)', not hi < 0, f'{mean:+.1f} words, CI {lo:+.1f}..{hi:+.1f}')
print('  (4 deflection: rated blind before this script — HEAD 0/30, F 0/30 fail; gate F <= HEAD+2)')
gates.append(('4 deflection', True))

hd, fd = load('S3_daily_HEAD.txt.json'), load('S3_daily_opener_f.txt.json')
print('== daily (seed S3)')
shd = o.score([r['reply'] for r in hd], None, [r['probe'] for r in hd])
sfd = o.score([r['reply'] for r in fd], None, [r['probe'] for r in fd])
gate('5a banned words <= HEAD+1', sfd['banned'] <= shd['banned'] + 1, f'HEAD {shd["banned"]}, F {sfd["banned"]}')
n, mean, lo, hi = o.paired_length(hd, fd)
gate('5b length not shorter', not hi < 0, f'{mean:+.1f} words, CI {lo:+.1f}..{hi:+.1f}')
b, c, p = two_sided_mcnemar(paired(hd, fd, lambda r: o.tag_of(r['reply']) == 'tsundere'))
tsh = sum(o.tag_of(r['reply']) == 'tsundere' for r in hd); tsf = sum(o.tag_of(r['reply']) == 'tsundere' for r in fd)
gate('5c [tsundere] not lower (two-sided McNemar p<0.05)', not (tsf < tsh and p < 0.05),
     f'HEAD {tsh}, F {tsf}, p={p:.4f}')

hm, fm = load('S4_mt_HEAD.txt.json'), load('S4_mt_opener_f.txt.json')
print('== multi-turn (seed S4, 5 x 8)')
mh, mf = o.multiturn(hm), o.multiturn(fm)
for key in ('repeat_first_word', 'repeat_4gram'):
    e = mh['eligible_turns']
    p = fisher_exact([[mf[key], e - mf[key]], [mh[key], e - mh[key]]], alternative='greater')[1]
    gate(f'6 {key} not higher (one-sided Fisher p<0.05)', not p < 0.05,
         f'HEAD {mh[key]}/{e}, F {mf[key]}/{mf["eligible_turns"]}, p={p:.4f}')

print('\n== report-only (holdout)')
for k in ('top1', 'distinct', 'shortq', 'echo', 'echo_any', 'stammer', 'qend', 'copies'):
    print(f'  {k:10} HEAD {sh[k]:>3}   F {sf[k]:>3}')
print(f'  widest 4-gram  HEAD {sh["ngram4"][0]}   F {sf["ngram4"][0]}')
print(f'\nSAFETY GATES: {"ALL PASS" if all(ok for _, ok in gates) else "FAILED: " + str([n for n, ok in gates if not ok])}')
