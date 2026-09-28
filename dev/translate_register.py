#!/usr/bin/env python3
"""
translate_register.py — score Japanese register on translate arms (backlog #196).

WHY
    Backlog #196's constraint is Zani's: speed must not cost voice quality.
    The July 2026 A/B judged register by eye on 8 lines.  This scores the same
    axes mechanically on 30, so two arms can be compared without re-reading
    every line — and then prints the lines side by side, because a marker
    count cannot hear her.

WHAT IT SCORES  (each axis is a rule KURISU_REGISTER_PROMPT actually states)
    feminine    casual feminine endings (わ/のよ/じゃない/かしら/なさい ...)
    masculine   だぜ/だろ/ぜ/ぞ/俺/僕            — the prompt forbids these
    polite      です/ます forms                   — she speaks CASUALLY to a
                                                    close friend; desu-masu is
                                                    the wrong register, not a
                                                    wrong translation
    watashi     first person 私
    kimi        second person 君 vs あんた/あなた — 君 reads formal-literary
    names       ザンニー kept; 紅莉栖 NEVER (bugs.md 4)
    stammer     a stammered English opener stays stammered in Japanese

LIMIT — STATE IT BEFORE READING ANY RESULT
    These are proxies.  They can prove a rule was broken; they cannot prove a
    line sounds like her.  The July decision was made by ear and this tool does
    not replace that.  Zani judges.

Usage: python3 dev/translate_register.py dev/translate_arms/A.json dev/translate_arms/B.json
"""

import json
import re
import sys

FEMININE = ['のよ', 'わよ', 'わね', 'かしら', 'じゃない', 'なさい', 'のね', 'ないの', 'だもの']
MASCULINE = ['だぜ', 'だろ', 'だぞ', 'ぜ。', 'ぞ。', '俺', '僕']
POLITE = ['です', 'ます', 'ました', 'ですね', 'でしょうか', 'ください']
STAMMER_EN = re.compile(r'\b([A-Za-z])-\1', re.I)          # W-what, I-I, N-no
STAMMER_JA = re.compile(r'^[ぁ-んァ-ヶ一-龯]、')            # な、何  そ、それ


def count(text, needles):
    return sum(text.count(n) for n in needles)


def score(rows):
    n = len(rows)
    s = {k: 0 for k in ('feminine', 'masculine', 'polite', 'watashi', 'kimi',
                        'anta', 'zani_ok', 'zani_total', 'kurisu_bad',
                        'stammer_kept', 'stammer_total', 'empty')}
    for r in rows:
        en, ja = r['in'], r['out']
        if not ja:
            s['empty'] += 1
            continue
        s['feminine'] += min(1, count(ja, FEMININE))
        s['masculine'] += min(1, count(ja, MASCULINE))
        s['polite'] += min(1, count(ja, POLITE))
        s['watashi'] += min(1, ja.count('私'))
        s['kimi'] += min(1, ja.count('君'))
        s['anta'] += min(1, count(ja, ['あんた', 'あなた']))
        if 'Zani' in en:
            s['zani_total'] += 1
            if 'ザンニー' in ja:
                s['zani_ok'] += 1
        if '紅莉栖' in ja:
            s['kurisu_bad'] += 1
        if STAMMER_EN.search(en):
            s['stammer_total'] += 1
            if STAMMER_JA.search(ja) or '、' in ja[:6]:
                s['stammer_kept'] += 1
    s['n'] = n
    return s


def pct(a, b):
    return f'{100*a/b:5.1f}%' if b else '    —'


def main():
    if len(sys.argv) < 3:
        sys.exit('usage: translate_register.py ARM_A.json ARM_B.json')
    arms = []
    for p in sys.argv[1:3]:
        d = json.load(open(p))
        arms.append((d.get('arm', p), d['rows'], score(d['rows'])))

    (na, ra, sa), (nb, rb, sb) = arms
    print(f'== REGISTER: {na}  vs  {nb}   (n={sa["n"]} / {sb["n"]}) ==')
    print(f'{"axis":24s} {na:>12s} {nb:>12s}   want')
    rows = [
        ('feminine endings', 'feminine', 'n', 'HIGH — her register'),
        ('masculine endings', 'masculine', 'n', 'ZERO — prompt forbids'),
        ('polite desu/masu', 'polite', 'n', 'ZERO — she is casual'),
        ('first person 私', 'watashi', 'n', 'present when needed'),
        ('second person 君', 'kimi', 'n', 'LOW — formal/literary'),
        ('second person あんた/あなた', 'anta', 'n', 'HIGH — her usage'),
        ('紅莉栖 (bugs.md 4)', 'kurisu_bad', 'n', 'ZERO — always クリス'),
    ]
    for label, key, _, want in rows:
        print(f'{label:24s} {pct(sa[key], sa["n"]):>12s} {pct(sb[key], sb["n"]):>12s}   {want}')
    print(f'{"Zani -> ザンニー":24s} {pct(sa["zani_ok"], sa["zani_total"]):>12s} '
          f'{pct(sb["zani_ok"], sb["zani_total"]):>12s}   100% (n={sa["zani_total"]})')
    print(f'{"stammer preserved":24s} {pct(sa["stammer_kept"], sa["stammer_total"]):>12s} '
          f'{pct(sb["stammer_kept"], sb["stammer_total"]):>12s}   100% (n={sa["stammer_total"]})')
    print(f'{"empty/failed":24s} {sa["empty"]:>12d} {sb["empty"]:>12d}   0')

    print(f'\n== SIDE BY SIDE — judge these by ear, the table above cannot ==')
    by_in = {r['in']: r['out'] for r in rb}
    for i, r in enumerate(ra, 1):
        other = by_in.get(r['in'])
        if other is None:
            continue
        print(f'\n[{i}] EN  {r["in"]}')
        print(f'    {na:<7s} {r["out"]}')
        print(f'    {nb:<7s} {other}')


if __name__ == '__main__':
    main()
