#!/usr/bin/env python3
"""
canon_likeness.py — score a set of Kurisu replies against the VN corpus.

HEADLINE METRIC: length distribution (Zani's choice, 2026-08-31).
Everything else is printed as a DIAGNOSTIC and is NOT part of the score.

No model calls. No GPU. Pure CPU over a 1,672-line CSV — runs in <1s,
~40 MB peak RSS. Safe to run while the app is up.

Usage
  python3 dev/canon_likeness.py --validate
        Self-validation: split-half canon-vs-canon + negative controls.
        Run this FIRST. A metric that cannot score canon as canon is not a metric.

  python3 dev/canon_likeness.py --score FILE.txt [--label NAME]
        Score one arm. FILE is one reply per line (leading [emotion] tag optional).

  python3 dev/canon_likeness.py --compare A.txt B.txt
        Two arms side by side, with a p-value on the length distributions.
"""
import argparse, csv, json, os, random, re, sys
from collections import Counter

import numpy as np
from scipy import stats

CANON_CSV = os.path.expanduser('~/Desktop/kurisu_english_lines.csv')

# ── text handling ────────────────────────────────────────────────────────────
TAG_RE = re.compile(r'^\s*\[[A-Za-z:_ ]+\]\s*')
SENT_RE = re.compile(r'[.!?]+(?:\s|$)')

def strip_tag(t):
    """Remove a leading [emotion] / [EMOTION:x] tag. It is never spoken."""
    return TAG_RE.sub('', t).strip()

def words(t):
    return strip_tag(t).split()

def wcount(t):
    return len(words(t))

def sentences(t):
    return [s.strip() for s in SENT_RE.split(strip_tag(t)) if s.strip()]

def load_canon(path=CANON_CSV):
    with open(path, encoding='utf-8', newline='') as f:
        return [r['line'].strip() for r in csv.DictReader(f) if r.get('line', '').strip()]

def load_sample(path):
    with open(path, encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip()]

# ── the headline metric: length distribution ─────────────────────────────────
def length_profile(texts, unit='utterance'):
    """Word counts. unit='utterance' = whole line/reply; 'sentence' = per sentence."""
    if unit == 'utterance':
        return np.array([wcount(t) for t in texts], dtype=float)
    out = []
    for t in texts:
        out.extend(len(s.split()) for s in sentences(t))
    return np.array(out, dtype=float)

def describe(x):
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return {}
    return {
        'n': int(x.size),
        'mean': round(float(x.mean()), 1),
        'median': float(np.median(x)),
        'p25': float(np.percentile(x, 25)),
        'p75': float(np.percentile(x, 75)),
        'p90': float(np.percentile(x, 90)),
        'max': float(x.max()),
        'pct_le8': round(100 * float((x <= 8).mean()), 1),
        'pct_gt35': round(100 * float((x > 35).mean()), 1),
    }

def length_score(sample, canon, unit='utterance'):
    """
    Wasserstein-1 distance between the two word-count distributions.
    Units are WORDS: 'her replies sit W words away from canon on average'.
    Lower is closer. 0 = identical distribution.
    KS gives the p-value for 'these came from the same distribution' —
    a HIGH p is the good outcome here, which is the opposite of the usual
    reading, so it is labelled explicitly in the report.
    """
    s = length_profile(sample, unit)
    c = length_profile(canon, unit)
    w = float(stats.wasserstein_distance(s, c))
    ks = stats.ks_2samp(s, c)
    return {
        'unit': unit,
        'wasserstein_words': round(w, 2),
        'ks_stat': round(float(ks.statistic), 3),
        'ks_p': float(ks.pvalue),
        'sample': describe(s),
        'canon': describe(c),
    }

# ── diagnostics (NOT scored) ─────────────────────────────────────────────────
def ngrams(toks, n):
    return [' '.join(toks[i:i + n]) for i in range(len(toks) - n + 1)]

def canon_ngram_sets(canon, ns=(3, 4)):
    out = {}
    for n in ns:
        s = set()
        for line in canon:
            s.update(ngrams([w.lower().strip('.,!?"\'') for w in words(line)], n))
        out[n] = s
    return out

def diag_canon_absent(sample, canon, n=4, min_repeats=3):
    """
    Phrases the sample repeats that appear ZERO times in canon.
    This is the bugs.md 76 mechanism, run automatically instead of by hunch.
    """
    cset = canon_ngram_sets(canon, (n,))[n]
    counts = Counter()
    per_reply = []
    for t in sample:
        toks = [w.lower().strip('.,!?"\'') for w in words(t)]
        gs = ngrams(toks, n)
        absent = [g for g in gs if g not in cset]
        counts.update(set(absent))
        per_reply.append(bool(absent))
    repeated = [(g, c) for g, c in counts.most_common() if c >= min_repeats]
    return {
        'n': n,
        'min_repeats': min_repeats,
        'top_absent_repeated': repeated[:15],
    }

def diag_phrase_rate(sample, canon, phrases):
    """Rate of named phrases in the sample, with their canon count beside it."""
    blob = ' || '.join(c.lower() for c in canon)
    out = []
    for p in phrases:
        pl = p.lower()
        hits = sum(1 for t in sample if pl in strip_tag(t).lower())
        out.append({
            'phrase': p,
            'sample_hits': hits,
            'sample_pct': round(100 * hits / max(1, len(sample)), 1),
            'canon_hits': blob.count(pl),
        })
    return out

# ── quality guard (hard veto — a length win that trips this is rejected) ─────
DEFLECT_MARKERS = [
    "it's not like", "not like", "don't misunderstand", "i'm not", "i am not",
    "that's not", "who said", "why would i", "don't get", "it's not that",
    "not that i", "whatever", "shut up", "idiot", "as if", "hmph", "tch",
    "i wasn't", "i didn't say", "don't be", "stop", "no reason",
]
STAMMER_RE = re.compile(r'\b([A-Za-z])-\1', re.I)


def check_guard_independence(prompt_text, markers=DEFLECT_MARKERS):
    """
    A quality guard that scores words the PROMPT itself inserts is circular.

    Found the hard way in bugs.md 77: the "deflects" guard read 90% -> 97%, but 5 of
    its 16 markers ("that's not", "don't", "not that i", "stop", "can't just") appear
    in the replacement text that same fix introduced. Part of the "improvement" was
    the guard matching my own edit. Call this with the prompt before trusting a guard.
    """
    p = prompt_text.lower()
    contaminated = [m for m in markers if m in p]
    return contaminated
TAG_ONLY_RE = re.compile(r'^\s*\[([A-Za-z:_ ]+)\]')

def quality_guard(sample):
    n = max(1, len(sample))
    defl = sum(1 for t in sample
               if any(m in strip_tag(t).lower() for m in DEFLECT_MARKERS))
    stam = sum(1 for t in sample if STAMMER_RE.search(strip_tag(t)))
    tags = []
    for t in sample:
        m = TAG_ONLY_RE.match(t)
        if m:
            tags.append(m.group(1).split(':')[-1].strip().lower())
    tsun = sum(1 for g in tags if g in ('tsundere', 'flustered', 'embarrassed'))
    openers = Counter(
        (words(t)[0].lower().strip('.,!?"\'') if words(t) else '') for t in sample)
    return {
        'deflection_rate': f'{defl}/{len(sample)} ({100*defl/n:.0f}%)',
        'stammer_rate': f'{stam}/{len(sample)} ({100*stam/n:.0f}%)',
        'tsundere_family_tag': f'{tsun}/{len(tags)} tagged'
                               if tags else 'no tags found',
        'distinct_openers': f'{len(openers)}/{len(sample)}',
        'top_openers': openers.most_common(5),
    }

# ── reporting ────────────────────────────────────────────────────────────────
def report(label, sample, canon, phrases=None):
    print(f'\n{"="*72}\n  {label}   (n={len(sample)})\n{"="*72}')
    for unit in ('utterance', 'sentence'):
        r = length_score(sample, canon, unit)
        s, c = r['sample'], r['canon']
        print(f'\n-- LENGTH, per {unit} --  [HEADLINE METRIC]')
        print(f'   Wasserstein  {r["wasserstein_words"]:>6.2f} words from canon   '
              f'(0 = identical; lower is better)')
        print(f'   KS           D={r["ks_stat"]:.3f}  p={r["ks_p"]:.3g}   '
              f'(HIGH p = indistinguishable from canon = GOOD)')
        print(f'   {"":13s}{"n":>6s}{"mean":>7s}{"med":>6s}{"p25":>6s}'
              f'{"p75":>6s}{"p90":>6s}{"max":>6s}{"<=8w":>8s}{">35w":>8s}')
        for nm, d in (('sample', s), ('canon', c)):
            print(f'   {nm:13s}{d["n"]:>6d}{d["mean"]:>7.1f}{d["median"]:>6.0f}'
                  f'{d["p25"]:>6.0f}{d["p75"]:>6.0f}{d["p90"]:>6.0f}{d["max"]:>6.0f}'
                  f'{d["pct_le8"]:>7.1f}%{d["pct_gt35"]:>7.1f}%')

    print('\n-- QUALITY GUARD (hard veto, not scored) --')
    for k, v in quality_guard(sample).items():
        print(f'   {k:22s} {v}')

    print('\n-- DIAGNOSTIC: repeated phrases absent from canon (not scored) --')
    d = diag_canon_absent(sample, canon)
    if d['top_absent_repeated']:
        for g, c in d['top_absent_repeated']:
            print(f'   {c:>3d}x  "{g}"')
    else:
        print('   none repeated 3+ times')

    if phrases:
        print('\n-- DIAGNOSTIC: named phrases (not scored) --')
        print(f'   {"phrase":34s}{"in sample":>12s}{"in canon":>10s}')
        for r in diag_phrase_rate(sample, canon, phrases):
            print(f'   {r["phrase"][:33]:34s}'
                  f'{r["sample_hits"]:>5d} ({r["sample_pct"]:>4.1f}%)'
                  f'{r["canon_hits"]:>10d}')

# ── self-validation ──────────────────────────────────────────────────────────
def validate(canon):
    print('\n' + '#' * 72)
    print('#  SELF-VALIDATION — does the metric score canon as canon?')
    print('#' * 72)
    rng = random.Random(0)

    # 1. split-half: canon vs canon. Expect W ~ 0 and a HIGH KS p.
    ws, ps = [], []
    for seed in range(20):
        r = random.Random(seed)
        idx = list(range(len(canon)))
        r.shuffle(idx)
        a = [canon[i] for i in idx[:len(idx) // 2]]
        b = [canon[i] for i in idx[len(idx) // 2:]]
        s = length_score(a, b)
        ws.append(s['wasserstein_words'])
        ps.append(s['ks_p'])
    print(f'\n1. CANON vs CANON, split-half x20 (the positive control)')
    print(f'   Wasserstein  median {np.median(ws):.2f}  max {max(ws):.2f} words')
    print(f'   KS p         median {np.median(ps):.3f}  '
          f'({sum(1 for p in ps if p > 0.05)}/20 indistinguishable at p>0.05)')
    print('   PASS if W is near 0 and most splits are indistinguishable.')

    # 1b. n=30 subsample vs canon — the sample size we will actually use.
    ws30, ps30 = [], []
    for seed in range(200):
        r = random.Random(1000 + seed)
        sub = r.sample(canon, 30)
        s = length_score(sub, canon)
        ws30.append(s['wasserstein_words'])
        ps30.append(s['ks_p'])
    print(f'\n1b. REAL CANON, n=30 subsample vs full canon x200')
    print(f'   Wasserstein  median {np.median(ws30):.2f}  '
          f'p95 {np.percentile(ws30,95):.2f} words')
    print(f'   KS p         {sum(1 for p in ps30 if p>0.05)}/200 pass at p>0.05')
    print(f'   >>> NOISE FLOOR at n=30: W up to ~{np.percentile(ws30,95):.1f} words '
          f'is INDISTINGUISHABLE FROM CANON.')
    print('       Do not call a difference real below that.')

    # 2. negative controls
    print('\n2. NEGATIVE CONTROLS (the metric must reject these)')
    controls = {
        'assistant-speak (long, helpful)': [
            "That's a great question! Let me walk you through the reasoning step by "
            "step so that it's completely clear how each part connects to the next.",
            "I understand how you feel. It's completely normal to experience that, and "
            "there are several strategies that many people find genuinely helpful here.",
            "Certainly! Here are a few considerations that might be worth thinking "
            "about before you make a final decision on which approach to take.",
        ] * 10,
        'degenerate truncation (all 3 words)': ['Yes. No. Fine.'] * 30,
        'our own EXAMPLES block': None,  # filled by caller
    }
    for name, texts in controls.items():
        if texts is None:
            continue
        s = length_score(texts, canon)
        verdict = 'REJECTED (good)' if s['ks_p'] < 0.05 else '!! NOT REJECTED !!'
        print(f'   {name:36s} W={s["wasserstein_words"]:>6.2f}  '
              f'p={s["ks_p"]:.2g}  {verdict}')

    print('\n3. KNOWN LIMIT, stated up front')
    print('   A canon "line" is one LP transcript utterance; a reply is one turn.')
    print('   Canon is 1.79 sentences/line, our CASUAL rule asks for 1-2, so the')
    print('   units are close but NOT proven identical. That is why per-sentence')
    print('   is reported alongside per-utterance — if the two disagree, the unit')
    print('   mismatch is the reason, and the per-sentence number is the safer one.')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--validate', action='store_true')
    ap.add_argument('--score', metavar='FILE')
    ap.add_argument('--label', default=None)
    ap.add_argument('--compare', nargs=2, metavar=('A', 'B'))
    ap.add_argument('--phrases', default=None,
                    help='comma-separated phrases for the named-phrase diagnostic')
    a = ap.parse_args()

    canon = load_canon()
    print(f'canon: {len(canon)} lines from {CANON_CSV}')
    phrases = [p.strip() for p in a.phrases.split(',')] if a.phrases else None

    if a.validate:
        validate(canon)
    if a.score:
        report(a.label or os.path.basename(a.score), load_sample(a.score),
               canon, phrases)
    if a.compare:
        for f in a.compare:
            report(os.path.basename(f), load_sample(f), canon, phrases)
        sa = length_profile(load_sample(a.compare[0]))
        sb = length_profile(load_sample(a.compare[1]))
        ks = stats.ks_2samp(sa, sb)
        print(f'\n{"="*72}\n  ARM A vs ARM B (are they different from each other?)')
        print(f'  KS D={ks.statistic:.3f}  p={ks.pvalue:.4g}   '
              f'{"DIFFERENT" if ks.pvalue<0.05 else "no detectable difference"}')

if __name__ == '__main__':
    main()
