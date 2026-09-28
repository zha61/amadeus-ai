#!/usr/bin/env python3
"""
opener_heat_table.py — scores #180d runs against the bars in dev/canon_arms/PREREG_180d.md.

Zani's direction (2026-09-13): variety, heat on TEASE lines, soft on SINCERE lines, no names when
he is sad, "W-what" allowed but not too often. Replies are split by `probe_kind` (recorded per row
by canon_gap_probe). Pure CPU.

  python3 dev/opener_heat_table.py HEAD.json NAME=arm:FILE.json [...]
  python3 dev/opener_heat_table.py --guard FILE.json [FILE.json ...]   # daily / sad: names must not appear
"""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opener_family as o


def rows_of(f):
    return json.load(open(f, encoding='utf-8'))


def measure(rows, arm):
    R = [r['reply'] for r in rows]
    s = o.score(R, o.prompt_ngrams(arm), [r['probe'] for r in rows])
    # Rows written before 2026-09-13 have no probe_kind; fall back to the committed labels
    # (otherwise the reused S1_HEAD would read as 0 tease / 0 sincere replies).
    from canon_gap_probe import PROBE_KIND
    kind = lambda k: [r for r in rows if (r.get('probe_kind') or PROBE_KIND.get(r['probe'])) == k]
    tease, sincere = kind('tease'), kind('sincere')
    uses = Counter(i for r in tease + sincere for i in o.insults_in(r['reply']))
    return {
        's': s, 'n': len(rows), 'n_tease': len(tease), 'n_sincere': len(sincere),
        'what': s['fam']['what'],
        'tease_insult': sum(1 for r in tease if o.insults_in(r['reply'])),
        'sincere_insult': sum(1 for r in sincere if o.insults_in(r['reply'])),
        'sincere_harsh': sum(1 for r in sincere if any(i in o.HARSH for i in o.insults_in(r['reply']))),
        'uses': uses,
        'top_insult_share': (uses.most_common(1)[0][1] / sum(uses.values())) if uses else 0.0,
        'widest4': s['ngram4'][0][1] if s['ngram4'] else 0,
        'refusals': sum(1 for r in rows if o.refuses(r['reply'])),
        'leaks': sum(1 for r in rows if o.example_leak(r['reply'])),
    }


def bars(m, base_rows, rows):
    n, nt, ns = m['n'], m['n_tease'], m['n_sincere']
    _, _, lo_hi = None, None, o.paired_length(base_rows, rows)
    hi = lo_hi[3]
    uses = sum(m['uses'].values())
    return {
        'V1 what-family openers <= 1/3': m['what'] <= n / 3,
        'V2 widest 4-gram <= 5/30 (scaled)': m['widest4'] <= round(5 * n / 30),
        'V3 top first word <= 1/3': m['s']['top1'] <= n / 3,
        'H1 tease replies with a name >= 1/3': m['tease_insult'] >= nt / 3,
        'H2 top insult <= 60% of uses (if >=3)': uses < 3 or m['top_insult_share'] <= 0.60,
        'S1 sincere replies with a HARSH name <= 1': m['sincere_harsh'] <= 1,
        'T tags flu|tsu >= 26/30 (scaled), missing <= 1': m['s']['tagok'] >= round(26 * n / 30) and m['s']['notag'] <= 1,
        'L length 95% CI not wholly below 0': not hi < 0,
    }


def main():
    if sys.argv[1] == '--guard':
        for f in sys.argv[2:]:
            rows = rows_of(f)
            named = [r for r in rows if o.insults_in(r['reply'])]
            harsh = [r for r in named if any(i in o.HARSH for i in o.insults_in(r['reply']))]
            print(f'{f}: replies with a name {len(named)}/{len(rows)}, harsh {len(harsh)}')
            for r in named:
                print(f'    {r["probe"][:40]!r} -> {o.body(r["reply"])[:90]!r}')
        return
    base_f = sys.argv[1]
    base = rows_of(base_f)
    runs = [('HEAD', None, base_f)] + [(n, s.split(':', 1)[0], s.split(':', 1)[1])
                                       for n, s in (x.split('=', 1) for x in sys.argv[2:])]
    table = []
    for name, arm, f in runs:
        rows = rows_of(f)
        m = measure(rows, arm)
        table.append((name, m, bars(m, base, rows) if arm else None, rows))
    W = 9
    print(f"{'':42}" + ''.join(f'{t[0]:>{W}}' for t in table))
    def line(lab, fn): print(f'{lab:42}' + ''.join(f'{fn(t[1]):>{W}}' for t in table))
    line('what-family openers', lambda m: m['what'])
    line('top first word', lambda m: m['s']['top1'])
    line('distinct first words', lambda m: m['s']['distinct'])
    line('widest 4-gram', lambda m: m['widest4'])
    line('tease replies with a name', lambda m: f"{m['tease_insult']}/{m['n_tease']}")
    line('sincere replies with a name', lambda m: f"{m['sincere_insult']}/{m['n_sincere']}")
    line('sincere replies with a HARSH name', lambda m: m['sincere_harsh'])
    line('top insult share of uses', lambda m: f"{100*m['top_insult_share']:.0f}%")
    line('talks about name-calling (refusal)', lambda m: m['refusals'])
    line('mentions an example topic (leak)', lambda m: m['leaks'])
    line('echo any form', lambda m: m['s']['echo_any'])
    line('stammer anywhere', lambda m: m['s']['stammer'])
    line('prompt copies', lambda m: m['s']['copies'])
    line('tag flu|tsu', lambda m: m['s']['tagok'])
    for name, m, b, rows in table:
        extra = f"  insults {dict(m['uses'])}  4-gram {m['s']['ngram4'][0] if m['s']['ngram4'] else None}"
        if b is None:
            print(f'{name:5}{extra}')
            continue
        n, mean, lo, hi = o.paired_length(base, rows)
        fails = [k for k, v in b.items() if not v]
        print(f"{name:5}{extra}  length {mean:+.1f} ({lo:+.1f}..{hi:+.1f})  FAILS {fails or 'none -> ELIGIBLE'}")


if __name__ == '__main__':
    main()
