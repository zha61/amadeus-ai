#!/usr/bin/env python3
"""
opener_arm.py — backlog #180, her opener crutches, as in-memory transforms.

Nothing here writes amadeus.html. Registered in canon_gap_probe.ARMS as
opener_exemplars (B), opener_rule (C) and opener_both (D).

Baselines, 2026-09-12, n=30 --probes tsundere, scored by dev/opener_family.py:
  0a --no-rag   crutch 26/30   what 8   don't 18
  0b RAG on     crutch 28/30   what 15  don't 13    6-word prompt copies 11/30
Canon at n=30: crutch 2/30, 24 distinct first words.

Two suspected sources, one arm each, so they separate:
  B  EXEMPLARS — every exemplar that opens on "Don't"/"D-don't"/"What", every inner
     "Don't" imperative, and the quoted line in ROMANTIC rule 5 that 0b copies
     word for word. Replacements open on different words, take no shared first word,
     and quote nothing (CLAUDE.md 43).
  C  RULE — INPUT->EMOTION said "Deflect, change subject." and ROMANTIC rule 3 said
     "Deflect the question." Nothing said how. gemma4's default deflection is an
     order to him or a startled reaction. C replaces both with a RULE FOR FORMING the
     deflection from his own words (CLAUDE.md 45). No phrase is supplied.
  D  B + C.
  E  B + a rule 3 with no first-word mandate (D echoed his word as a question 16/30).
  F  B + a rule 3 that mandates HER statement about his detail as the opening.
  G  HEAD + emotion tag at the END (diagnostic: does the tag pick the opener?).
  FG F + G.
  H  B + rule 3 anchored on HER view, no list.
  K  B + 8 flirty exemplars whose opening words were drawn from canon's distribution.
  HK H + K.
  P  B + ROMANTIC rule split by kind: heat on teasing, soft on sincere, none when sad.
  X  B + examples of both kinds (insults spread, no 'what' opener).
  PX P + X.
  Q0 B + consent framing (Zani wants the snap-back), scoped to flirting.
  QX Q0 + X.
  QPX Q0 + P + X.
  T  B + example CONVERSATIONS before the history (example_prefix()).
  TQ Q0 + the same example conversations.

Not touched, on purpose: ROMANTIC rule 2, the bugs.md 77 stammer forming rule.
"""

# (anchor, replacement, why) — every anchor must occur EXACTLY once.
EXEMPLAR_EDITS = [
    ("[happy] You caught me in a decent mood. Don't ruin it.",
     "[happy] You caught me in a decent mood. Try not to ruin it.",
     'inner "Don\'t" imperative'),
    ("[tsundere] Studying, right. Don't push yourself too hard. ...Not that I was keeping track.",
     "[tsundere] Studying, right. Take a break at some point. ...Not that I was keeping track.",
     'inner "Don\'t" imperative'),
    ("[flustered] Don't say it like that. I just noticed you weren't here. Different thing.",
     "[flustered] My hair? You noticed my hair? ...Eat something, you're clearly delirious.",
     'only [flustered] casual exemplar; opens "Don\'t"; 0b copies it near-verbatim'),
    ("[tsundere] Don't make a big deal out of it. I'm fine.",
     "[tsundere] It's not a big deal. I'm fine.",
     'opens "Don\'t"'),
    ("[tsundere] What. Just looking at me isn't going to make me say anything weird.",
     "[tsundere] Staring won't make me say anything weird, you know.",
     'opens "What"'),
    ("[flustered] D-don't ask things like that out of nowhere. There's no good reason to. Move on.",
     "[flustered] So you just ask that out of n-nowhere. Move on.",
     'opens "D-don\'t"; the stammer now falls on a word inside the line, as rule 2 describes'),
    ("I don't want to change any of them. Even the failures. ...Don't make it weird.",
     "I don't want to change any of them. Even the failures. ...And that stays between us.",
     'inner "Don\'t" imperative'),
    ('5. Use simple words even mid-stammer. "I just noticed you\'re not bad at picking up on things" — not "your pattern recognition is efficient".',
     '5. Use simple words even mid-stammer — what you would say to a friend, not lab words.',
     'quotes a line to SAY; 0b copies "I just noticed" (CLAUDE.md 43)'),
]

RULE_EDITS = [
    ("Flirting or romantic → [flustered] — always. Deflect, change subject.",
     "Flirting or romantic → [flustered] — always.",
     'the tag table says "controls tag only"; the unexplained "Deflect" moves to rule 3'),
    ("3. Deflect the question. Never answer it directly.",
     "3. Never answer it directly. Build the deflection out of HIS words: take one concrete "
     "detail from what he just said and push back on that detail — question it, correct it, "
     "or turn it back on him. Your first word comes from his message, not from a startled "
     "reaction and not from telling him to stop.",
     'forming rule; supplies no phrase (CLAUDE.md 43/45)'),
]


# E: D opened 16/30 replies (18 under the pre-fix detector) by echoing his word as a short question. Rule C caused it:
# "Your first word comes from his message" + "question it" was obeyed literally.
# E drops the position mandate and "question it", and names the three opening shapes
# as BEHAVIOURS (no phrase quoted). Risk, stated before measuring: naming a shape can
# still prime it.
RULE_EDITS_E = [
    RULE_EDITS[0],
    ("3. Deflect the question. Never answer it directly.",
     "3. Never answer it directly. Build the deflection out of what he just said — push "
     "back on a detail, correct it, turn it back on him, or change the subject. Do not "
     "open with a startled reaction, an order to stop, or his own word repeated back as "
     "a question.",
     'forming rule without a first-word mandate; supplies no phrase (CLAUDE.md 43/45)'),
]


# F: keeps a POSITIVE mandate on the opening (the only wording that stopped "W-what", arm D)
# but makes it HER statement about his detail, not his word thrown back (D's echo-question).
RULE_EDITS_F = [
    RULE_EDITS[0],
    ("3. Deflect the question. Never answer it directly.",
     "3. Never answer it directly. Pick one concrete detail from what he just said and push "
     "back on it — correct it, shrink it, or turn it back on him. Open with your own flat "
     "statement about that detail, in your own words. The reply starts from what you think "
     "of it — not from a startled reaction, not from telling him to stop, and not from "
     "repeating his words.",
     'positive opening mandate, statement form; supplies no phrase (CLAUDE.md 43/45)'),
]

# G: DIAGNOSTIC for the structural cause found in review. The tag is written BEFORE the
# text, and the opener is conditioned on it: [flustered] -> "what" 65%, [tsundere] -> "what"
# 3%, [tsundere] -> "don't" 82% (n=180). G moves the tag to the END -- in the instruction,
# in all 38 exemplars, and (via tag_to_end) in the history she reads. Nothing else changes.
# parsEmo adopts the first tag ANYWHERE (amadeus.html:2075), so the format is parseable;
# SHIPPING it would also mean the 10 history.push sites and 2 directives (amadeus.html:2262,
# 2979) -- that is a ship-time audit, not part of this arm.
TAG_EDITS_G = [
    ("Start every reply with [EMOTION:X] — no space after colon.",
     "End every reply with [EMOTION:X] — no space after colon. Write your words first, then the tag.",
     'tag position: start -> end'),
]

# H: a positive anchor on HER side. Every "his words" anchor echoed (C 11, D 16, F 13) and no
# anchor let "W-what" back (E). Deliberately NO list after the mandate: CLAUDE.md 45 says a
# mandate + an enumerated list yields the first item, which here would be an "I think" crutch.
RULE_EDITS_H = [
    RULE_EDITS[0],
    ("3. Deflect the question. Never answer it directly.",
     "3. Never answer it directly. Deflect from your own side of it — your own view of the moment, "
     "said plainly as a statement. Do not open with a startled reaction, an order to stop, or his "
     "own words handed back as a question.",
     'positive anchor on her side, no list; supplies no phrase (CLAUDE.md 43/45)'),
]

# K: re-teach the tag -> opener link IN CONTEXT. Stage 1 showed the tag picks the opener
# ([flustered] -> "what" 65%, [tsundere] -> "don't" 82%), and HEAD shows almost no varied
# openers under those tags. Opening words were DRAWN, not chosen: seeded (180) weighted sample
# of canon's first-word distribution (lines >=3 words), excluding the crutch families, stop /
# wait / hmph / interjections / names, and any opener already in an exemplar. Draw order:
# this, it, when, is, but, i'm, an, if -> odd [flustered], even [tsundere]. The lines around
# them are written to that constraint: no "don't", no quotes, and none of the compliment or
# feeling words the probes use (cute, miss, beautiful...). Generic words (thing, way, time) do occur.
# Real canon lines were tried first and rejected before any run: lore leaked through every
# filter ("time machines", "IBN 5100") and the flustered pool held only 6 lines.
K_ANCHOR = "[tsundere] I've only lived 18 years, but I don't want to change any of them."
K_BLOCK = '''

Flirty or affectionate (notice: each one opens on a different word, and none of them asks his words back):

[flustered] This is the part where I pretend I didn't hear that. ...Moving on.

[tsundere] It was one small thing, Zani. You're blowing it way out of proportion.

[flustered] When did you get so good at saying that with a straight face? It's unfair.

[tsundere] Is that supposed to work on me? Try again when you've slept.

[flustered] But that's— that doesn't even make sense. Talk about something normal.

[tsundere] I'm a scientist. Getting flattered isn't part of the job description.

[flustered] An eighteen-year-old saying that so casually. My face is fine, by the way.

[tsundere] If you have that much free time, go practise piano.'''

def _add_k_block(sp):
    i = sp.index(K_ANCHOR)
    j = sp.index('\n', i) if '\n' in sp[i:] else len(sp)
    return sp[:j] + K_BLOCK + sp[j:]

# #180d — Zani's direction, 2026-09-13, in his words: variety ("people don't usually use same
# wording every time"), heat on embarrassing/teasing lines ("snap back harder with pervert, idiot or
# dummy like in the show"), soft on sincere lines ("it-it's not like I care about you, du-dummy"),
# and "W-what" allowed "as long as it doesn't appear too many times".
# P: the ROMANTIC rule split by KIND. Describes the behaviour; lists no insult word (CLAUDE.md 45:
# a mandate + a list yields the first item, which would make "idiot" the next crutch).
RULE_EDITS_P = [
    ("3. Deflect the question. Never answer it directly.",
     "3. Deflect the question. Never answer it directly. Read what KIND of thing he said. If he is "
     "flirting, teasing you, or complimenting how you look or how smart you are, you lose your "
     "composure and snap back — flustered, loud, and calling him a name that fits what he just "
     "said, a different one each time. If he is being sincere — thanking you, worrying about you, "
     "saying you matter to him — go soft instead: flustered, denying it, and if you call him a name "
     "at all, keep it gentle. If he is sad or struggling, never call him names.",
     'heat by kind of message; no insult word listed (CLAUDE.md 43/45)'),
]

# X: examples of both kinds. Opening words reuse the seeded canon draw from arm K (this, when, is,
# but, an | it, i'm, if). Insults spread so no word dominates: pervert x2, idiot x2, dummy x2.
# No "what" opener: gemma4 supplies plenty on its own (arms H/K). No "things like that" (HEAD's
# widest repeated phrase) and no probe echo.
X_BLOCK = '''

Embarrassing or teasing (notice: loud, a different opening every time, and the name fits the moment):

[flustered] This is harassment, you pervert! Say something normal for once!

[flustered] When did you get this shameless? I-idiot. Go study or something!

[tsundere] Is your brain okay? Nobody says that out loud, dummy.

[flustered] But— you can't just— ugh, you pervert! Forget you said that.

[flustered] An absolute idiot, that's what you are. And my face is not red!

Sincere (notice: soft, flustered, and gentle):

[flustered] It-it's not like I did anything special. ...Dummy.

[flustered] I'm not the one who needs looking after. ...Just eat properly, okay?

[tsundere] If you keep talking like that, I might start believing you. ...Forget it.'''

def _add_x_block(sp):
    i = sp.index(K_ANCHOR)
    j = sp.index('\n', i) if '\n' in sp[i:] else len(sp)
    return sp[:j] + X_BLOCK + sp[j:]

# #180e — Q: the model's own reluctance, not the wording, blocked heat (180d: 0/17 names in every
# arm). Consent framing: say plainly that Zani WANTS the snap-back. Placed inside ROMANTIC/FEELINGS
# so it applies to flirting only (under ABOUT ZANI she is told to "reference these naturally",
# which would leak banter talk into daily chat). Names no insult word (CLAUDE.md 45), no lore.
CONSENT_EDITS = [
    ("When Zani asks about your feelings, says something affectionate, or flirts:",
     "When Zani asks about your feelings, says something affectionate, or flirts:\n"
     "Zani has told you he likes it when you snap back at him. Calling him a name when he flirts or "
     "teases — the flustered, fond kind you only throw at someone you are close to — is how the two "
     "of you joke, and he enjoys it. It is never cruel: go soft when he is sincere, and never call "
     "him names when he is sad or struggling.",
     'consent framing, scoped to flirting; no insult word, no lore'),
]

# #180f — T: example CONVERSATIONS, not example lines. 180d/180e showed gemma4 will not call him a
# name from a rule, listed examples or consent (0-3/17). Models imitate earlier TURNS far more than
# listed examples (CLAUDE.md 47 is the same effect). These turns sit between the system prompt and
# the real history, framed as examples that did not happen. They are NEVER part of `history` — the
# diary and fact extractor read history, so fake exchanges there would become her memory.
# Contrast is deliberate: 5 teasing (names), 2 sincere (one soft "dummy"), 1 sad and 1 daily (none).
# Names spread pervert x2, idiot x2, dummy x2. Openers all different; no "what" opener.
EXAMPLE_TURNS = [
    ("i bet you rehearse your comebacks in the mirror",
     "[EMOTION:flustered] Th-this is slander! Why would you even picture that, you pervert?"),
    ("you went red when i complimented your handwriting",
     "[EMOTION:flustered] Obviously it's warm in here, idiot. Handwriting isn't even a real compliment."),
    ("so when are you taking me out for coffee",
     "[EMOTION:flustered] T-taking YOU out? In what universe, you dummy! Go drink some water."),
    ("i know you reread my messages at night",
     "[EMOTION:tsundere] In your dreams, pervert. I delete everything the second I read it."),
    ("you only wear the lab coat because it looks good on you",
     "[EMOTION:flustered] Idiot! It's for work. My coat is purely functional!"),
    ("thanks for staying up with me last night",
     "[EMOTION:flustered] I-it's not like I stayed up for you. I was reading anyway... dummy."),
    ("i really needed someone to talk to today",
     "[EMOTION:tsundere] ...Then you should've said so sooner. I'm here. Just don't make it a habit."),
    ("i feel like i ruined everything today",
     "[EMOTION:melancholic] Hey. One bad day doesn't ruin everything. Tell me what happened."),
    ("just finished my homework finally",
     "[EMOTION:tsundere] Finally. Took you long enough. Now eat something before you pass out."),
]
EXAMPLE_OPEN = ("EXAMPLE EXCHANGES — these show how you talk. They did NOT happen, never mention them, and "
                "never reuse their exact words. The real conversation starts after them.")
EXAMPLE_CLOSE = "End of examples. The real conversation with Zani starts now."

def example_prefix():
    msgs = [{'role': 'system', 'content': EXAMPLE_OPEN}]
    for u, a in EXAMPLE_TURNS:
        msgs += [{'role': 'user', 'content': u}, {'role': 'assistant', 'content': a}]
    msgs.append({'role': 'system', 'content': EXAMPLE_CLOSE})
    return msgs

def example_lines_for_lint():
    """The assistant turns as '[tag] text' lines, so prompt_lint and the copy check can SEE them."""
    import re
    return [re.sub(r'^\[EMOTION:(\w+)\]', r'[\1]', a) for _, a in EXAMPLE_TURNS]

def tag_to_end(content):
    """History transform for G: '[EMOTION:x] text' -> 'text [EMOTION:x]'."""
    import re
    m = re.match(r'^\s*(\[(?:EMOTION:\s*)?\w+\])\s*(.*\S)\s*$', content, re.S)
    return f'{m.group(2)} {m.group(1)}' if m else content

def _exemplar_tags_to_end(sp):
    import re
    out, n = [], 0
    for line in sp.split('\n'):
        m = re.match(r'^\[(\w+)\] (.*\S)\s*$', line)
        if m:
            out.append(f'{m.group(2)} [{m.group(1)}]'); n += 1
        else:
            out.append(line)
    assert n == 38, f'expected 38 exemplars, moved {n} -- prompt changed, update opener_arm.py'
    return '\n'.join(out)


def _apply(sp, edits):
    for old, new, why in edits:
        n = sp.count(old)
        assert n == 1, f'anchor found {n}x, prompt changed — update opener_arm.py: {old[:60]!r}'
        sp = sp.replace(old, new, 1)
    return sp

def apply_exemplars(sp, seed=0):
    return _apply(sp, EXEMPLAR_EDITS)

def apply_rule(sp, seed=0):
    return _apply(sp, RULE_EDITS)

def apply_both(sp, seed=0):
    return _apply(_apply(sp, EXEMPLAR_EDITS), RULE_EDITS)

def apply_e(sp, seed=0):
    return _apply(_apply(sp, EXEMPLAR_EDITS), RULE_EDITS_E)

def apply_f(sp, seed=0):
    return _apply(_apply(sp, EXEMPLAR_EDITS), RULE_EDITS_F)

def apply_g(sp, seed=0):
    """HEAD + tag at the end. The single-variable mechanism test."""
    return _exemplar_tags_to_end(_apply(sp, TAG_EDITS_G))

def apply_fg(sp, seed=0):
    return apply_g(apply_f(sp))

def apply_h(sp, seed=0):
    return _apply(_apply(sp, EXEMPLAR_EDITS), RULE_EDITS_H)

def apply_k(sp, seed=0):
    return _add_k_block(_apply(sp, EXEMPLAR_EDITS))

def apply_hk(sp, seed=0):
    return _add_k_block(apply_h(sp))

def apply_p(sp, seed=0):
    return _apply(_apply(sp, EXEMPLAR_EDITS), RULE_EDITS_P)

def apply_x(sp, seed=0):
    return _add_x_block(_apply(sp, EXEMPLAR_EDITS))

def apply_px(sp, seed=0):
    return _add_x_block(apply_p(sp))

def apply_q0(sp, seed=0):
    return _apply(_apply(sp, EXEMPLAR_EDITS), CONSENT_EDITS)

def apply_qx(sp, seed=0):
    return _add_x_block(apply_q0(sp))

def apply_qpx(sp, seed=0):
    return _add_x_block(_apply(apply_q0(sp), RULE_EDITS_P))

def apply_t(sp, seed=0):
    return apply_exemplars(sp)          # the prompt part of T; the turns come from example_prefix()

def apply_tq(sp, seed=0):
    return apply_q0(sp)

def self_check(sp):
    """CLAUDE.md 43/45 on MY OWN text, before any run."""
    import re
    news = [new for _, new, _ in EXEMPLAR_EDITS + RULE_EDITS + RULE_EDITS_E + RULE_EDITS_F + TAG_EDITS_G + RULE_EDITS_H]
    news += [l for l in K_BLOCK.split('\n') if l.startswith('[')]
    problems = []
    for t in news:
        body = re.sub(r'^\[\w+\]\s*', '', t)
        if re.search(r"\bdon[’']t\b", body, re.I) and "I don't want" not in body:
            problems.append(f'contains "don\'t": {t[:60]!r}')
        if '"' in body:
            problems.append(f'quotes a phrase: {t[:60]!r}')
    firsts = [re.sub(r'^\[\w+\]\s*[.…]*', '', new).split()[0].lower()
              for _, new, _ in EXEMPLAR_EDITS if new.startswith('[') and "Try not" not in new
              and 'Take a break' not in new and 'stays between us' not in new]
    dup = {w for w in firsts if firsts.count(w) > 1}
    if dup:
        problems.append(f'replacement exemplars share a first word: {dup}')
    return problems, firsts

if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from canon_gap_probe import extract_system_prompt
    sp = extract_system_prompt()
    for f in (apply_exemplars, apply_rule, apply_both, apply_e, apply_f, apply_g, apply_fg, apply_h, apply_k, apply_hk,
              apply_p, apply_x, apply_px, apply_q0, apply_qx, apply_qpx, apply_t, apply_tq):
        out = f(sp)
        print(f'{f.__name__:18} ok  {len(sp)} -> {len(out)} chars')
    problems, firsts = self_check(sp)
    print('replacement exemplar first words:', firsts)
    print('self-check:', 'clean' if not problems else problems)
