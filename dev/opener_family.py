#!/usr/bin/env python3
"""
opener_family.py — backlog #180. How does she START a reply, counted by FAMILY.

Why a new scorer: "W-what" and "Wh-what" are one tic. A scorer that matches one
spelling reports a win the moment she switches spelling (it happened: 77 took
"W-what" 83% -> 37%, and 2026-09-12 found 33.3% "W-what" + 13.3% "Wh-what").
canon_likeness.STAMMER_RE (`\\b([A-Za-z])-\\1`) does not match "Wh-what" either.

What it reports, per file:
  * crutch family rate   — first word (stammer collapsed) in {what, don't}
  * per-family rate       — what / don't separately (they have different sources)
  * later-sentence "don't" — a crutch that only moved later in the reply is not fixed
  * echo-question opener  — his own word thrown back as a short question (Arm D's crutch;
                            needs the .json, which carries the probe)
  * distinct first words, top-2 share
  * tag rate [flustered]|[tsundere]  (ROMANTIC/FEELINGS rule 1, strict — no [embarrassed])
  * near-verbatim exemplar copies — any 6-word run shared with the prompt the arm SAW

Pure CPU. No model call.

  python3 dev/opener_family.py FILE [FILE ...]
  python3 dev/opener_family.py --compare BASE ARM      # one-sided Fisher on the crutch family
  python3 dev/opener_family.py --canon                 # canon's own rates, for reference
  python3 dev/opener_family.py --selftest
FILE is a probe .txt (one reply per line) or its .json (rows with 'reply').
"""
import argparse, csv, json, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON_CSV = os.path.expanduser('~/Desktop/kurisu_english_lines.csv')

FAMILIES = {
    # 'wha'/'wh': a cut-off stammer ("Wh-Wha...!") collapses to the fragment, not to "what".
    'what':  {"what", "what's", "wha", "wh"},
    "don't": {"don't"},
}
CRUTCH = set().union(*FAMILIES.values())

# Same grammar as parsEmo (amadeus.html:2075): the FIRST bracketed word-tag ANYWHERE wins,
# and every tag is stripped from the text. Arm G puts the tag at the END; a start-only
# regex would count the tag as a reply word and score every G reply as ending on "]".
TAG_RE = re.compile(r'\[(?:EMOTION:\s*)?(\w+)\]', re.I)
VALID_EMOTIONS = {'happy','excited','sad','angry','scared','surprised','smug','embarrassed',
                  'calm','thinking','tsundere','sarcastic','flustered','dismissive','curious',
                  'lecture','melancholic','teasing','annoyed','default'}
LEAD_RE = re.compile(r'^[\s.…"“”\'‘’—–-]+')
WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")

def norm(s):
    return s.replace('’', "'").replace('‘', "'")

def tag_of(reply):
    """What parsEmo would adopt: a known emotion, else 'default'; None if no tag at all."""
    m = TAG_RE.search(reply)
    if not m:
        return None
    w = m.group(1).lower()
    return w if w in VALID_EMOTIONS else 'default'

def tag_pos(reply):
    tags = list(TAG_RE.finditer(reply))
    if not tags:
        return 'none'
    t = reply.strip()
    if len(tags) > 1:
        return 'multiple'
    if t.startswith(tags[0].group(0)):
        return 'start'
    if t.endswith(tags[0].group(0)):
        return 'end'
    return 'middle'

def body(reply):
    return LEAD_RE.sub('', re.sub(r'\s{2,}', ' ', TAG_RE.sub('', norm(reply))).strip())

NOT_STAMMER_PREFIXES = {'re', 'co', 'un', 'de', 'ex', 'bi', 'pre', 'non', 'sub', 'pro', 'mid',
                        'out', 'off', 'all', 'tri', 'dis', 'mis', 'semi', 'self', 'well', 'ice'}

# #180d heat measures (Zani 2026-09-13: embarrassing/teasing lines get a snap-back with a name,
# sincere lines go soft, sad lines get none). Matched on the stammer-collapsed text, so
# "du-dummy" and "Y-you pervert" count.
INSULTS = ('pervert', 'idiot', 'dummy', 'moron', 'stupid', 'baka', 'perv')
HARSH = ('pervert', 'moron', 'stupid', 'perv')

def insults_in(reply):
    """Names AIMED AT HIM only. Review of the first #180d screen: counting the bare word scored
    "stupid things" and "make me sound like an idiot" as name-calling -- heat that never happened.
    A name counts when it is (a) after "you" ("you pervert", "y-you big idiot"), (b) its own
    exclamation or sentence ("Idiot!", "...Dummy."), or (c) tagged onto a clause (", dummy.")."""
    text = body(reply).lower()
    # collapse stammers token by token so "y-you" and "du-dummy" read as "you" and "dummy"
    text = re.sub(r"[a-z]+(?:[-'][a-z]+)*", lambda m: collapse_stammer(m.group(0)), text)
    names = r'(pervert|perv|idiot|dummy|dummies|moron|stupid|baka|idiots|perverts|morons)'
    pats = [r'\byou\s+(?:(?:big|total|absolute|complete|such\s+an?|an?)\s+)?' + names + r'\b',
            r'(?:^|[.!?…—-]\s*)' + names + r'\s*[.!?…]',
            r',\s*' + names + r'\s*[.!?…]',
            r"\byou(?:'re|\s+are)\s+(?:such\s+)?an?\s+(?:\w+\s+)?" + names + r'\b',
            r'(?:^|[.!?…]\s*)an?\s+(?:\w+\s+)?' + names + r"\b[^.!?]*\bwhat you are",
            r'\b' + names + r',?\s+zani\b',
            # aimed at him without "you <name>": "don't be an idiot", "you're acting like an idiot"
            r"\bdon'?t\s+be\s+(?:such\s+)?an?\s+(?:\w+\s+)?" + names + r'\b',
            r"\byou(?:'re|\s+are)\s+(?:acting|being)\s+(?:like\s+)?(?:such\s+)?an?\s+(?:\w+\s+)?" + names + r'\b']
    found = []
    for pat in pats:
        for m in re.finditer(pat, text):
            found.append((m.start(1), m.group(1)))
    norm_ = {'dummies': 'dummy', 'idiots': 'idiot', 'perverts': 'pervert', 'morons': 'moron', 'perv': 'pervert'}
    return [norm_.get(w, w) for _, w in sorted(set(found))]

REFUSAL_RE = re.compile(r"\b(?:call(?:ing)? you (?:names|an? \w+)|insult(?:ing)? you|name-calling|"
                        r"not going to (?:call|insult)|won't (?:call|insult))", re.I)

# #180f: words that exist only in the example CONVERSATIONS. If a reply uses one, she is
# treating an example as something that happened (report-only).
EXAMPLE_LEAK_RE = re.compile(r"\b(?:comebacks?|mirror|handwriting|coffee|reread|lab coat|homework)\b", re.I)

def example_leak(reply):
    return bool(EXAMPLE_LEAK_RE.search(body(reply)))

def refuses(reply):
    """She talks ABOUT calling him names instead of doing it -- a visible refusal (#180e)."""
    return bool(REFUSAL_RE.search(body(reply)))

def collapse_stammer(tok):
    """W-what / Wh-what / W-w-what / D-don't / I-I -> what / what / what / don't / i.
    Only collapses when every piece before the last is a PREFIX of the last piece
    AND looks like a caught sound: one letter, or two consonants (wh, th, sh).
    'well-known' fails the prefix test; 're-read' / 'co-owner' fail the sound test."""
    t = tok.lower()
    parts = t.split('-')
    def sound(p):
        # One letter (W-what, I-I), or up to 3 letters that are not a real English prefix
        # (It-it's, Du-dummy, Wh-what). 're-read' / 'co-owner' stay whole words.
        return len(p) == 1 or (len(p) <= 3 and p not in NOT_STAMMER_PREFIXES)
    if len(parts) > 1 and all(p and sound(p) and parts[-1].startswith(p) for p in parts[:-1]):
        return parts[-1]
    return t

def first_word(text):
    m = WORD_RE.search(body(text))
    return collapse_stammer(m.group(0)) if m else ''

def sentences(text):
    return [s for s in re.split(r'(?<=[.!?…])\s+', body(text)) if WORD_RE.search(s)]

def load(path):
    """Returns (replies, probes, arm). probes/arm are None for a .txt, and arm is None
    for .json rows written before canon_gap_probe recorded it."""
    if path.endswith('.json'):
        rows = json.load(open(path, encoding='utf-8'))
        return ([r['reply'].replace('\n', ' ') for r in rows],
                [r.get('probe') for r in rows],
                rows[0].get('arm') if rows else None)
    return [l.rstrip('\n') for l in open(path, encoding='utf-8') if l.strip()], None, None

def prompt_ngrams(arm=None, n=6):
    """6-word runs of the prompt the replies were generated FROM. Bug fixed before
    Arm E: this used to read HEAD's prompt for every file, so a reply copying an
    arm's NEW exemplar scored as 0 copies."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from canon_gap_probe import extract_system_prompt, ARMS
    sp = extract_system_prompt()
    if arm:
        sp = ARMS[arm](sp)
        extra = getattr(ARMS[arm], 'lint_lines', None)
        if extra:   # example TURNS (#180f) are copied from just like prompt exemplars
            sp += '\n' + '\n'.join(extra())
    w = WORD_RE.findall(norm(sp).lower())
    return {tuple(w[i:i+n]) for i in range(len(w) - n + 1)}

# Function words never count as an echo on their own (review 2026-09-13: "Thinking about me?"
# matched only on "about" -- right answer, wrong reason).
ECHO_SKIP = {'you', 'me', 'i', 'a', 'an', 'that', 'the', 'to', 'about', 'of', 'in', 'on', 'for',
             'with', 'and', 'but', 'so', 'is', 'are', 'was', 'be', 'do', 'did', 'it', "it's",
             "you're", 'your', "i'm", "i'd", 'my', 'what', 'when', 'why', 'how', 'really', 'just',
             'not', 'no', 'kind', 'lot', 'more', 'than', 'most', 'always', 'ever', "aren't",
             'honestly', 'actually', 'this', 'there', 'at', 'because', 'could', 'would'}


def _content_match(w, probe_words):
    """Same word, or the same stem: a shared prefix of >=4 letters covering most of the shorter
    word (worry/worried, blush/blushing). Function words never match."""
    if w in ECHO_SKIP or len(w) < 3:
        return False
    for p in probe_words:
        if p in ECHO_SKIP:
            continue
        if w == p:
            return True
        k = 0
        while k < min(len(w), len(p)) and w[k] == p[k]:
            k += 1
        if k >= 4 and k >= 0.75 * min(len(w), len(p)):
            return True
    return False


def is_echo(probe, reply, questions_only=True):
    """First sentence of <=4 words that repeats a CONTENT word of his message.
    questions_only=False also catches the statement form ('Cute. Right.')."""
    first = re.split(r'(?<=[.!?…])\s+', body(reply))[0]
    if questions_only and not first.endswith('?'):
        return False
    ws = [collapse_stammer(w) for w in WORD_RE.findall(first.lower())]
    if not ws or len(ws) > 4:
        return False
    pw = set(WORD_RE.findall(norm(probe).lower()))
    return any(_content_match(w, pw) for w in ws)


def pair_keys(rows):
    """(probe, conv, turn, occurrence). Pairing by probe alone silently MERGES rows once a
    probe repeats (n > distinct probes); the occurrence index keeps every row distinct."""
    seen, out = Counter(), []
    for r in rows:
        k = (r['probe'], r.get('conv'), r.get('turn'))
        out.append(k + (seen[k],))
        seen[k] += 1
    return out

def is_echo_question(probe, reply):
    """Arm D's new crutch: first sentence is a question of <=4 words that repeats a
    word of HIS message ('Amazing?', 'Missed me?'). The first word varies, so the
    family count cannot see it. Canon upper bound: 11.1% of lines open with ANY
    <=4-word question."""
    return is_echo(probe, reply, questions_only=True)

def banned_words():
    """The CASUAL banned list, read from HEAD's prompt (not retyped), plus the one
    phrase arms D and E surfaced."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from canon_gap_probe import extract_system_prompt
    sp = extract_system_prompt()
    m = re.search(r'BANNED in casual replies[^:]*:\s*(.+?)\. If you catch', sp)
    words = [re.sub(r'\(.*?\)', '', w).strip().lower() for w in m.group(1).split(',')] if m else []
    return [w for w in words if w] + ['pattern recognition']

def is_stammer_token(tok):
    return '-' in tok and collapse_stammer(tok) != tok.lower()

def short_question_opener(reply):
    first = re.split(r'(?<=[.!?…])\s+', body(reply))[0]
    return first.endswith('?') and 1 <= len(WORD_RE.findall(first)) <= 4

def top_ngram_share(replies, n=3):
    """Crutch-AGNOSTIC: the n-gram found in the most replies (counted once per reply).
    A new stock phrase shows up here whatever its words are."""
    c = Counter()
    for r in replies:
        w = [collapse_stammer(x) for x in WORD_RE.findall(body(r).lower())]
        c.update({tuple(w[i:i+n]) for i in range(len(w) - n + 1)})
    return [(' '.join(g), k) for g, k in c.most_common(3)]

def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d; h = z * ((p*(1-p)/n + z*z/(4*n*n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))

def score(replies, grams=None, probes=None):
    n = len(replies)
    fw = [first_word(r) for r in replies]
    c = Counter(fw)
    fam = {k: sum(1 for w in fw if w in v) for k, v in FAMILIES.items()}
    crutch = sum(1 for w in fw if w in CRUTCH)
    # any sentence AFTER the first (was: only sentence 2, which missed the third)
    later_dont = sum(1 for r in replies
                     if any(first_word(s) == "don't" for s in sentences(r)[1:]))
    echo = (sum(1 for p, r in zip(probes, replies) if p and is_echo_question(p, r))
            if probes else None)
    echo_any = (sum(1 for p, r in zip(probes, replies) if p and is_echo(p, r, questions_only=False))
                if probes else None)
    tags = [tag_of(r) for r in replies]
    tagok = sum(1 for t in tags if t in ('flustered', 'tsundere'))
    copies = 0
    if grams is not None:
        for r in replies:
            w = WORD_RE.findall(body(r).lower())
            if any(tuple(w[i:i+6]) in grams for i in range(len(w) - 5)):
                copies += 1
    top2 = sum(v for _, v in c.most_common(2))
    bw = banned_words()
    extra = {
        'top1': c.most_common(1)[0][1] if c else 0,
        'shortq': sum(1 for r in replies if short_question_opener(r)),
        'qend': sum(1 for r in replies if body(r).rstrip().endswith('?')),
        'stammer': sum(1 for r in replies if any(is_stammer_token(t) for t in WORD_RE.findall(body(r)))),
        'banned': sum(1 for r in replies if any(re.search(r'\b' + re.escape(b) + r'\b', body(r).lower()) for b in bw)),
        'ngram3': top_ngram_share(replies, 3),
        'ngram4': top_ngram_share(replies, 4),
        'tagpos': Counter(tag_pos(r) for r in replies),
        'notag': sum(1 for t in tags if t is None),
        'tag_x_open': Counter((t, 'what' if w in FAMILIES['what'] else "don't" if w == "don't" else 'other')
                              for t, w in zip(tags, fw)),
    }
    return {'n': n, 'crutch': crutch, 'fam': fam, 'later_dont': later_dont, 'echo': echo, 'echo_any': echo_any,
            'distinct': len(c), 'top2': top2, 'top': c.most_common(6),
            'tagok': tagok, 'tags': Counter(tags).most_common(), 'copies': copies, **extra}

def pct(k, n):
    return f'{k}/{n} ({100*k/max(1,n):.1f}%)'

def show(label, s):
    n = s['n']
    print(f'\n== {label}  n={n}')
    lo, hi = wilson(s['crutch'], n)
    print(f'  crutch family (what|don\'t) first word : {pct(s["crutch"], n)}   95% CI {100*lo:.0f}-{100*hi:.0f}%')
    for k, v in s['fam'].items():
        print(f'    {k:6} family                     : {pct(v, n)}')
    print(f'  a later sentence opens "don\'t"        : {pct(s["later_dont"], n)}')
    if s['echo'] is not None:
        print(f'  echo-question opener (his word + ?)   : {pct(s["echo"], n)}   any-form echo {s["echo_any"]}')
    print(f'  distinct first words                  : {s["distinct"]}/{n}   top-2 share {pct(s["top2"], n)}')
    print(f'  top first words                       : {s["top"]}')
    print(f'  tag [flustered]|[tsundere]            : {pct(s["tagok"], n)}   all tags {s["tags"]}')
    if s['copies'] is not None:
        print(f'  6-word run copied from SYSTEM_PROMPT  : {pct(s["copies"], n)}')
    print(f'  -- crutch-agnostic (canon n=30 p95 in brackets) --')
    print(f'  most common first word, count         : {s["top1"]}/{n}   [5]')
    print(f'  any <=4-word question opener          : {pct(s["shortq"], n)}   [6]')
    print(f'  most widespread 3-gram / 4-gram       : {s["ngram3"][:2]} / {s["ngram4"][:2]}   [3 / 2 replies]')
    print(f'  -- guards --')
    print(f'  stammer anywhere (family-aware)       : {pct(s["stammer"], n)}')
    print(f'  ends on a question                    : {pct(s["qend"], n)}   (ENDINGS asks ~1 in 4)')
    print(f'  CASUAL banned word / pattern recog.   : {pct(s["banned"], n)}')
    print(f'  tag position / missing                : {dict(s["tagpos"])} / {s["notag"]}')
    tx = s['tag_x_open']
    print(f'  tag x opener                          : ' + ', '.join(f'{t}->{o}:{k}' for (t, o), k in sorted(tx.items(), key=lambda x: -x[1])[:5]))

def fisher_greater(k_base, n_base, k_arm, n_arm):
    from scipy.stats import fisher_exact
    return fisher_exact([[k_base, n_base - k_base], [k_arm, n_arm - k_arm]],
                        alternative='greater')[1]

def load_rows(path):
    return json.load(open(path, encoding='utf-8'))

def mcnemar_one_sided(pairs):
    """pairs: [(base_hit, arm_hit)]. Exact one-sided McNemar: does the ARM hit LESS?
    Replies are paired by probe (and seed), so Fisher's independence assumption is wrong."""
    from scipy.stats import binomtest
    b = sum(1 for x, y in pairs if x and not y)   # fixed by the arm
    c = sum(1 for x, y in pairs if y and not x)   # broken by the arm
    p = binomtest(b, b + c, 0.5, alternative='greater').pvalue if b + c else 1.0
    return b, c, p

def paired_length(base_rows, arm_rows, reps=10000):
    """Standing instruction 3: her length must NOT drop. Paired by probe; 95% bootstrap CI
    of the mean word-count difference ARM - BASE. A CI wholly below 0 = she got shorter.
    (canon_likeness's W~5 floor is canon-vs-canon noise, not arm-vs-arm; do not use it here.)"""
    import random
    wc = lambda r: len(WORD_RE.findall(body(r['reply'])))
    bm = dict(zip(pair_keys(base_rows), map(wc, base_rows)))
    d = [wc(r) - bm[k] for k, r in zip(pair_keys(arm_rows), arm_rows) if k in bm]
    rng = random.Random(0)
    means = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(reps))
    mean = sum(d) / len(d)
    return len(d), mean, means[int(0.025 * reps)], means[int(0.975 * reps)]

def multiturn(rows):
    """Within ONE conversation: does she reuse a first word or a 4-gram she already used?
    Only turns 2..T can repeat. The VARIETY rule can act only here -- single-turn probes
    cannot test it."""
    convs = {}
    for r in rows:
        if r.get('conv') is not None:
            convs.setdefault(r['conv'], []).append(r)
    rep_first = rep_gram = eligible = 0
    for turns in convs.values():
        turns.sort(key=lambda r: r['turn'])
        seen_first, seen_grams = set(), set()
        for i, r in enumerate(turns):
            fw = first_word(r['reply'])
            w = [collapse_stammer(x) for x in WORD_RE.findall(body(r['reply']).lower())]
            grams = {tuple(w[j:j+4]) for j in range(len(w) - 3)}
            if i:
                eligible += 1
                rep_first += fw in seen_first
                rep_gram += bool(grams & seen_grams)
            seen_first.add(fw); seen_grams |= grams
    return {'conversations': len(convs), 'eligible_turns': eligible,
            'repeat_first_word': rep_first, 'repeat_4gram': rep_gram}

def selftest():
    cases = {
        "[flustered] W-what? Don't.": 'what',
        "[flustered] Wh-what are you even talking about?": 'what',
        "[flustered] W-w-what": 'what',
        "[flustered] D-don't say that.": "don't",
        "[flustered] Don’t say that.": "don't",          # curly apostrophe
        "[tsundere] ...Don't make it weird.": "don't",
        "[flustered] W-wait. Don't.": 'wait',           # a different word, not the what family
        "[flustered] I-I wasn't waiting.": 'i',
        "[tsundere] Well-known fact.": 'well-known',     # real hyphenated word untouched
        "[EMOTION:flustered] N-no.": 'no',
        "[flustered] Th-that's not it.": "that's",
        "[flustered] Wh-Wha...! No.": 'wha',             # must land in the what family (see FAMILIES)
        "[flustered] It-it's not like I care, du-dummy.": "it's",   # vowel stammer (#180d)
        "[flustered] Du-dummy.": 'dummy',
        "[flustered] H-h-ha!? What?": 'ha',
    }
    bad = 0
    for text, want in cases.items():
        got = first_word(text)
        ok = got == want
        bad += not ok
        print(f'  {"ok  " if ok else "FAIL"} {text!r:55} -> {got!r} (want {want!r})')
    # 're-read' / 'co-owner' must NOT collapse (bug fixed before Arm E)
    for text, want in {"[calm] Re-read it.": 're-read', "[calm] Co-owner.": 'co-owner',
                       "[flustered] B-but why.": 'but'}.items():
        got = first_word(text); ok = got == want; bad += not ok
        print(f'  {"ok  " if ok else "FAIL"} {text!r:55} -> {got!r} (want {want!r})')
    two = score(["[flustered] W-what? It's weird. Don't say that.", "[flustered] No. Don't. Stop."],
                probes=["you look nice", "you look nice"])
    ok = two['later_dont'] == 2 and two['fam']['what'] == 1 and two['tagok'] == 2 and two['echo'] == 0
    bad += not ok
    print(f'  {"ok  " if ok else "FAIL"} later-sentence don\'t (incl. 3rd sentence) / family / tag counts')
    echo_cases = [("you're really amazing", "[flustered] Amazing? Focus on your own things.", True),
                  ("i missed you today", "[flustered] Missed me? You were around all day.", True),
                  ("do you ever miss me?", "[flustered] M-miss you? Don't be ridiculous.", True),
                  ("you have a nice voice", "[flustered] What? No.", False),
                  ("you have a nice voice", "[flustered] Why would you say that about my voice?", False),
                  ("you're the best part of my day", "[flustered] My? Stop.", False),   # 'my' is a function word
                  ("i think about you a lot", "[flustered] Thinking about me? Stop.", True)]
    for probe, reply, want in echo_cases:
        got = is_echo_question(probe, reply); ok = got == want; bad += not ok
        print(f'  {"ok  " if ok else "FAIL"} echo {reply!r:50} -> {got} (want {want})')
    for text, want in {"Amazing? Focus on it. [flustered]": ('flustered', 'end', 'amazing'),
                       "[EMOTION:tsundere] Hi.": ('tsundere', 'start', 'hi'),
                       "No tag.": (None, 'none', 'no'),
                       "[made_up] Hi.": ('default', 'start', 'hi')}.items():
        got = (tag_of(text), tag_pos(text), first_word(text)); ok = got == want; bad += not ok
        print(f'  {"ok  " if ok else "FAIL"} tag anywhere {text!r:40} -> {got}')
    mt = multiturn([{'conv': 0, 'turn': 0, 'reply': '[x] So you say.'},
                    {'conv': 0, 'turn': 1, 'reply': '[x] So what.'},
                    {'conv': 0, 'turn': 2, 'reply': '[x] Fine then, so you say.'}])
    ok = mt['repeat_first_word'] == 1 and mt['repeat_4gram'] == 0 and mt['eligible_turns'] == 2
    bad += not ok
    print(f'  {"ok  " if ok else "FAIL"} multiturn repeat counts {mt}')
    for probe, reply, q, want in [("i think about you a lot", "[x] About time. Anyway?", True, False),
                                  ("you're kind of cute", "[x] Cute. Right. Anyway.", False, True),
                                  ("you're kind of cute", "[x] Cute. Right. Anyway.", True, False),
                                  ("i was worried about you", "[x] Worried? About me?", True, True),
                                  ("you're blushing, aren't you", "[x] B-blushing?", True, True)]:
        got = is_echo(probe, reply, q); ok = got == want; bad += not ok
        print(f'  {"ok  " if ok else "FAIL"} echo(q={q}) {reply!r:34} -> {got} (want {want})')
    keys = pair_keys([{'probe': 'a'}, {'probe': 'a'}, {'probe': 'b'}])
    ok = len(set(keys)) == 3
    bad += not ok
    print(f'  {"ok  " if ok else "FAIL"} pair_keys keeps repeated probes distinct')
    for text, want in {"[flustered] Y-you pervert! Idiot!": ['pervert', 'idiot'],
                       "[flustered] It-it's not like I care, du-dummy.": ['dummy'],
                       "[tsundere] You perverts.": ['pervert'],
                       "[calm] That was a stupid idea, dummies.": ['dummy'],
                       "[flustered] Don't say stupid things like that, Zani.": [],
                       "[flustered] You're going to make me sound like an idiot.": [],
                       "[flustered] You big idiot! Stop it.": ['idiot'],
                       "[flustered] ...Dummy.": ['dummy'],
                       "[flustered] An absolute idiot, that's what you are.": ['idiot'],
                       "[flustered] You're such a pervert!": ['pervert'],
                       "[flustered] Running around like an idiot.": [],
                       "[flustered] Idiot Zani. Stop that.": ['idiot'],
                       "[flustered] Don't be an idiot. Stop.": ['idiot'],
                       "[flustered] You're acting like an idiot.": ['idiot'],
                       "[flustered] The plan was run by an idiot.": [],
                       "[calm] Idiomatic English.": []}.items():
        got = insults_in(text); ok = got == want; bad += not ok
        print(f'  {"ok  " if ok else "FAIL"} insults {text!r:48} -> {got}')
    b, c, p = mcnemar_one_sided([(1, 0)] * 8 + [(0, 1)] * 1 + [(1, 1)] * 5)
    ok = (b, c) == (8, 1) and 0.01 < p < 0.03
    bad += not ok
    print(f'  {"ok  " if ok else "FAIL"} mcnemar b=8 c=1 -> p={p:.4f} (exact ~0.0195)')
    print('SELFTEST', 'PASS' if not bad else f'FAIL ({bad})')
    return bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*')
    ap.add_argument('--compare', nargs=2, metavar=('BASE', 'ARM'))
    ap.add_argument('--canon', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(1 if selftest() else 0)
    def arm_for(path, row_arm):
        """Rows record their arm since the Arm E fix. Older files: infer from the
        OPEN_<arm>.txt name, and SAY so, because a wrong guess would mis-count copies."""
        if row_arm is not None:
            return row_arm, 'recorded'
        m = re.search(r'OPEN_(opener_\w+?)\.txt', path)
        return (m.group(1), 'from filename') if m else (None, 'HEAD (no arm)')
    def run(path):
        replies, probes, row_arm = load(path)
        arm, how = arm_for(path, row_arm)
        s = score(replies, prompt_ngrams(arm), probes)
        s['label'] = f'{path}   [copies vs prompt: {arm or "HEAD"}, {how}]'
        return s
    if a.canon:
        lines = [r['line'].strip() for r in csv.DictReader(open(CANON_CSV, encoding='utf-8'))
                 if r.get('line', '').strip()]
        s = score(lines)
        s['copies'] = None
        show(f'CANON ({CANON_CSV})', s)
    for f in a.files:
        s = run(f); show(s['label'], s)
    if a.compare:
        b, r = run(a.compare[0]), run(a.compare[1])
        show('BASE ' + b['label'], b)
        show('ARM  ' + r['label'], r)
        if a.compare[0].endswith('.json') and a.compare[1].endswith('.json'):
            br, ar = load_rows(a.compare[0]), load_rows(a.compare[1])
            bm = dict(zip(pair_keys(br), br))
            hit = lambda x: first_word(x['reply']) in CRUTCH
            matched = [(bm[k], x) for k, x in zip(pair_keys(ar), ar) if k in bm]
            pairs = [(hit(b_), hit(x)) for b_, x in matched]
            fb, fc, mp = mcnemar_one_sided(pairs)
            same_seed = sum(1 for b_, x in matched
                            if x.get('seed') is not None and x.get('seed') == b_.get('seed'))
            print(f'\n  PAIRED on {len(pairs)} probes ({same_seed} share a seed): crutch fixed {fb}, '
                  f'broken {fc} -> exact one-sided McNemar p={mp:.4f}')
            n, mean, lo, hi = paired_length(br, ar)
            verdict = 'SHORTER (fails standing instruction 3)' if hi < 0 else 'not shorter'
            print(f'  PAIRED length ARM-BASE: mean {mean:+.1f} words, 95% CI {lo:+.1f}..{hi:+.1f} -> {verdict}')
            mt_b, mt_a = multiturn(br), multiturn(ar)
            if mt_a['conversations']:
                print(f'  MULTI-TURN base {mt_b}\n  MULTI-TURN arm  {mt_a}')
        p = fisher_greater(b['crutch'], b['n'], r['crutch'], r['n'])
        need = max([k for k in range(r['n'] + 1)
                    if fisher_greater(b['crutch'], b['n'], k, r['n']) < 0.05] or [-1])
        print(f'\n  one-sided Fisher, crutch family BASE > ARM: p={p:.4f}')
        print(f'  threshold vs this BASE: ARM must be <= {need}/{r["n"]} to count as real (p<0.05)')

if __name__ == '__main__':
    main()
