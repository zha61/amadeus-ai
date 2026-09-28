#!/usr/bin/env python3
"""
prompt_lint.py — catch CLAUDE.md 43/45 violations in SYSTEM_PROMPT BEFORE shipping.

Written after bugs.md 77, where I removed a crutch the prompt supplied ("W-what",
4 sites) and introduced a new one in the replacement ("Don't", 2 sites -> 13%->33%).
That mistake was mechanical and therefore preventable. This is the check that would
have caught it, and it would also have caught "Hmph" and "Don't get the wrong idea".

Pure CPU, <1s, no GPU, no model call. Run it before every prompt edit.

  python3 dev/prompt_lint.py            # lint the live prompt
  python3 dev/prompt_lint.py --strict   # exit 1 on any ERROR (for npm run check)
"""
import argparse, csv, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CANON_CSV = os.path.expanduser('~/Desktop/kurisu_english_lines.csv')


def load_canon():
    with open(CANON_CSV, encoding='utf-8', newline='') as f:
        return [r['line'].strip() for r in csv.DictReader(f) if r.get('line', '').strip()]


STAMMER_PREFIX = re.compile(r'^([A-Za-z]|[b-df-hj-np-tv-xz]{2})-(?=\1)', re.I)
# Tag at the START or the END of a line (arm G moves it to the end). #180 review:
# matching only a start tag made the exemplar check find 0 lines under G and
# report "clean" -- a blind gate, which CLAUDE.md 52 forbids.
EXEMPLAR_RE = re.compile(r'^\[\w+\]\s+\S|\S\s+\[\w+\]\s*$')
TAG_EDGE_RE = re.compile(r'^\[\w+\]\s*|\s*\[\w+\]\s*$')

def exemplar_lines(sp):
    """Exactly ONE tag, at the start or the end, and not a rule-table line ("A → [x] or [y]")."""
    return [l for l in sp.split('\n')
            if EXEMPLAR_RE.search(l) and len(re.findall(r'\[\w+\]', l)) == 1 and '→' not in l]

def opener(t, n=1):
    """First n words, lowercased. A stammer prefix is STRIPPED first: "D-don't" and
    "don't" are the same opener for crutch purposes. Without this the lint misses
    exactly the mistake it was written for -- bugs.md 77 supplied "Don't" twice, once
    plain and once stammered, and each looked unique."""
    w = TAG_EDGE_RE.sub('', t).strip().split()
    w = [STAMMER_PREFIX.sub('', x) for x in w]
    return ' '.join(w[:n]).lower().strip('.,!?—"\'') if w else ''


def lint(sp, canon):
    blob = ' || '.join(c.lower() for c in canon)
    n_canon = len(canon)
    errors, warns = [], []

    # ── 1. every phrase the prompt QUOTES (rule 43) ─────────────────────────
    quoted = set()
    for m in re.finditer(r'"([^"\n]{3,60})"', sp):
        q = m.group(1).strip()
        if len(q.split()) <= 6 and not q.endswith(':'):
            quoted.add(q)
    # A phrase quoted as something to SAY is a direct rule-43 risk. A phrase quoted
    # to FORBID it is a weaker (but real) one -- rule 43 says naming still supplies it,
    # and that is exactly how "Don't get the wrong idea" survived at 37% (bugs.md 76).
    # Different severity, so they are reported separately rather than lumped together.
    NEG = ('not ', 'never', 'banned', 'avoid', 'instead of', 'no emoji', 'no ai-speak',
           'don\'t', 'rather than', 'swap it', ' — not', 'wrong ')
    for q in sorted(quoted):
        if blob.count(q.lower()):
            continue
        line = next((l for l in sp.split('\n') if f'"{q}"' in l), '')
        negative = any(k in line.lower() for k in NEG)
        msg = (f'{"names a FORBIDDEN phrase" if negative else "QUOTES a phrase to SAY"}, '
               f'absent from canon: "{q}" (0/{n_canon}) — CLAUDE.md 43')
        (warns if negative else errors).append(msg)

    # ── 2. exemplar openers repeated (rule 45 / the "Don't" mistake) ────────
    ex = exemplar_lines(sp)
    for width in (1, 2):
        c = Counter(opener(l, width) for l in ex)
        for op, k in c.most_common():
            if not op or k < 2:
                continue
            canon_rate = 100 * sum(1 for t in canon if opener(t, width) == op) / n_canon
            ex_rate = 100 * k / len(ex)
            if ex_rate > canon_rate * 3 and ex_rate >= 5:
                (errors if k >= 3 else warns).append(
                    f'{width}-word opener {op!r} used by {k}/{len(ex)} exemplars '
                    f'({ex_rate:.0f}%) vs {canon_rate:.1f}% of canon — '
                    f'{ex_rate/max(canon_rate,0.06):.0f}x over-supplied')

    # ── 3. mandates that force a single behaviour every turn (rule 45) ──────
    for kw in ('mandatory', 'always begin', 'begin with a', 'must begin'):
        for line in sp.split('\n'):
            if kw in line.lower():
                warns.append(f'MANDATE {kw!r}: {line.strip()[:80]}  '
                             f'— a mandate + a list yields the first item ~83% (bugs.md 77)')
    return errors, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--arm', default=None,
                    help='lint the prompt AFTER a canon_gap_probe arm (in memory)')
    a = ap.parse_args()
    from canon_gap_probe import extract_system_prompt, ARMS
    canon = load_canon()
    sp = extract_system_prompt()
    if a.arm:
        sp = ARMS[a.arm](sp)
        print(f'ARM: {a.arm} applied in memory')
    errors, warns = lint(sp, canon)

    print(f'prompt_lint — SYSTEM_PROMPT {len(sp)} chars vs {len(canon)} canon lines\n')
    for e in errors:
        print(f'  ERROR  {e}')
    for w in warns:
        print(f'  warn   {w}')
    if not errors and not warns:
        print('  clean.')
    print(f'\n  {len(errors)} error(s), {len(warns)} warning(s)')
    if a.strict and errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
