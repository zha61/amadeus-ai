#!/usr/bin/env python3
"""
stammer_arm.py — the backlog #177-revised fix, as an in-memory transform.

Measured FIRST, shipped only if it beats baseline. Nothing here writes amadeus.html.

Design, derived from the corpus rather than invented (see backlog #176/#177):
  * canon stammers on 3% of all lines, and 0/64 of the lines the SHIPPED retriever
    returns for the 30 affection probes. Our prompt MANDATES 100%.
  * of the 48 canon lines that do stammer, 42 open differently — she almost never
    repeats a stammer. Ours repeats one form in 83% of replies.
  => attack RATE and VARIETY. Do not attack stammering itself: it is her character,
     and bugs.md 71/76 both nearly shipped a "fix" that hollowed her out.

The mechanism: a LIST of three stammers has three members and she picks the first.
A RULE for forming one ("repeat the first sound of the word you were already going
to say") generates a different stammer per sentence and supplies no phrase at all,
so CLAUDE.md 43 cannot be violated by construction.

Every site is changed in one pass. bugs.md 76 proved a partial fix reads as
no-effect: one surviving site holds the rate steady.
"""

# (anchor, replacement, why)
EDITS = [
    # --- sites that SUPPLY a stammer token -------------------------------------
    ('Dry humour, deadpan. "Hmph." When flustered, stammer: "I-I wasn\'t implying—"',
     'Dry humour, deadpan. When flustered you catch on your own words.',
     'supplies "I-I" AND "Hmph" (0/1672 in canon) — CLAUDE.md 43, backlog #177'),

    ('If your response contains a stammer ("W-what", "I-I", "Th-that") — tag MUST be [flustered] or [tsundere].',
     'If your response contains a stammer — a repeated first sound — tag MUST be [flustered] or [tsundere].',
     'keeps the tag rule, stops naming the three phrases'),

    ('2. Begin with a stammer: "W-what—", "I-I wasn\'t—", "Th-that\'s not—".',
     '2. Often you catch on a word. Build the stammer out of the word you were ALREADY '
     'going to say — repeat its first sound — so it comes out different every time. '
     'Not every reply needs one; a flat denial or a sharp deflection lands just as well. '
     'Never reuse a stammer you have already used in this conversation.',
     'THE site: a mandatory instruction plus three exemplars. List -> generative rule, '
     'mandate -> "often", plus session-scoped anti-repeat (the construction that worked '
     'in bugs.md 76)'),

    # --- exemplars: 4 flustered lines, ALL currently opening on a stammer -------
    ('[flustered] I-I didn\'t say I missed you. I just noticed you weren\'t here. Different thing.',
     '[flustered] Don\'t say it like that. I just noticed you weren\'t here. Different thing.',
     'was a 4th "I-I" site; now shows a deflection with NO stammer'),

    ('[flustered] W-what kind of question is that? There\'s no good reason to ask that. Move on.',
     '[flustered] D-don\'t ask things like that out of nowhere. There\'s no good reason to. Move on.',
     '"D-don\'t" is canon-attested (3 hits); breaks the W-what monopoly'),

    ('[flustered] I-I didn\'t — Th-that\'s not what this is. Stop.',
     '[flustered] N-no. That\'s not what this is. Stop.',
     '"N-no" is canon-attested (2 hits); a different first sound again'),

    ('[flustered] W-what? No. ...Don\'t say things like that out of nowhere.',
     '[flustered] ...You can\'t just say that. Where did that even come from.',
     'second no-stammer exemplar — 2 of 4 stammer, vs 4 of 4 before'),

    # --- sites that MANDATE a stammer without naming one -----------------------
    ('Emotional (stammers are mandatory on flirt/feelings — and notice the SIMPLE words even mid-stammer):',
     'Emotional (notice: she does not stammer every time, and never the same way twice — '
     'and the words stay SIMPLE):',
     'the word "mandatory" is what produces 100%'),

    ('No analytical words. Stammer, deflect, simple words only.',
     'No analytical words. Deflect, simple words only.',
     'third mandate site'),

    ('Flirting or romantic → [flustered] — always. Stammer, deflect, change subject.',
     'Flirting or romantic → [flustered] — always. Deflect, change subject.',
     'fourth mandate site; the [flustered] tag rule is deliberately KEPT'),

    ('(The mandatory stammer on flirty messages still applies — vary WHICH stammer.)',
     '(The flustered reflex on flirty messages still applies.)',
     'the LAST "mandatory" site, and it sits inside the anti-crutch rule itself — '
     'bugs.md 76 proved one survivor holds the rate steady'),

    ('[tsundere] Hmph. Took you long enough.',
     '[tsundere] You took your time. ...Not that I was counting.',
     'the last "Hmph" site (0/1672 in canon) — backlog #177 proper'),

]


def apply(sp: str) -> str:
    for anchor, repl, why in EDITS:
        assert sp.count(anchor) == 1, (
            f'anchor missing or ambiguous ({sp.count(anchor)}x): {anchor[:70]!r}')
        sp = sp.replace(anchor, repl, 1)
    return sp


def report(sp_before: str, sp_after: str) -> None:
    import re
    pat = re.compile(r'\b([A-Za-z])-\1', re.I)
    for name, s in (('BEFORE', sp_before), ('AFTER', sp_after)):
        toks = sorted(set(m.group(0).lower() for m in pat.finditer(s)))
        print(f'  {name:7s} stammer tokens in prompt: {toks}')
        print(f'  {name:7s} occurrences of "w-what": {s.lower().count("w-what")}   '
              f'"hmph": {s.lower().count("hmph")}   '
              f'"mandatory": {s.lower().count("mandatory")}')
    print(f'  prompt length {len(sp_before)} -> {len(sp_after)} chars '
          f'({len(sp_after)-len(sp_before):+d})')


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from canon_gap_probe import extract_system_prompt
    before = extract_system_prompt()
    after = apply(before)
    print(f'{len(EDITS)} edits applied cleanly.\n')
    report(before, after)
