#!/usr/bin/env python3
"""
canon_gap_probe.py — generate n replies from the REAL live configuration,
so canon_likeness.py has something honest to score.

Fidelity notes (this is the part that decides whether the number means anything):
  * SYSTEM_PROMPT is extracted BYTE-EXACT from amadeus.html, not retyped.
  * Ollama params copied from sendMsg() at amadeus.html:2457 —
    temperature 0.85, top_p 0.9, num_predict 120, num_ctx 8192,
    plus keep_alive '30m' + think:false from ollamaStream().
  * RAG is fetched from the live server on 5003 and spliced in as its OWN
    system message just before the user turn — the RAG_AS_TAIL_MESSAGE=true
    layout (amadeus.html:440, bugs.md 68). NOT inside the system message.
  * Probes are DAILY-LIFE topics on purpose. That is the worst case
    (improvements-backlog #162), not the convenient one.

What is NOT reproduced: Zani's private facts / diary-window / relationship
blocks, which buildSystemPrompt() injects from localStorage. Those need
dumpSystemPrompt() from DevTools. Stated here so nobody mistakes this for
the full prompt.

Cost: one gemma4 call per probe, on the same GPU that renders her.
DO NOT RUN WHILE THE APP IS OPEN (CLAUDE.md rule 37).
"""
import argparse, json, os, re, sys, time
import requests

HTML = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'amadeus.html')
OLLAMA = 'http://127.0.0.1:11434/api/chat'
RAG = 'http://127.0.0.1:5003/retrieve'
MODEL = 'gemma4:latest'

# ── byte-exact prompt extraction ─────────────────────────────────────────────
def extract_system_prompt(path=HTML, rev=None):
    """Byte-exact SYSTEM_PROMPT. With rev=<git revision>, read that revision's
    amadeus.html instead of the working copy -- so a BEFORE arm is the real
    shipped prompt from history, not a hand-reverted approximation."""
    if rev:
        import subprocess
        src = subprocess.run(['git', 'show', f'{rev}:amadeus.html'],
                             capture_output=True, text=True, check=True).stdout
    else:
        src = open(path, encoding='utf-8').read()
    start = src.index('const SYSTEM_PROMPT=`') + len('const SYSTEM_PROMPT=`')
    end = src.index('`\n\nconst EMO_EXP', start)
    return src[start:end]


def relationship_directive(stage, path=HTML):
    """The app's RELATIONSHIP block for a stage, parsed from relationshipDirective()'s D[] array
    by anchor (amadeus.html ~4660), not retyped. The probe omitted it until 2026-09-13; stage 0
    says "No teasing", which would silently contradict any banter arm."""
    src = open(path, encoding='utf-8').read()
    i = src.index('return D[_relActiveStage]')
    j = src.rindex('const D = [', 0, i)
    items = re.findall(r'"(RELATIONSHIP\\n(?:[^"\\]|\\.)*)"', src[j:i])
    assert len(items) == 5, f'expected 5 RELATIONSHIP stages, parsed {len(items)}'
    return items[stage].replace('\\n', '\n')

def with_relationship(sp, stage):
    """Insert it exactly where buildSystemPrompt does (amadeus.html ~5008): before TWO MODES."""
    assert '\nTWO MODES\n' in sp, 'TWO MODES anchor missing'
    return sp.replace('\nTWO MODES\n', '\n' + relationship_directive(stage) + '\n\nTWO MODES\n', 1)


# ── ARMS: in-memory prompt transforms. NOTHING is written to amadeus.html. ──
def arm_canon_exemplars(sp, seed=0):
    """
    DIAGNOSTIC ARM (not a shippable candidate).

    Swap the 38 hand-written exemplar LINES for 38 real VN lines sampled to
    match canon's own length distribution. The [emotion] tag SEQUENCE is held
    byte-identical, so exactly one thing changes: the exemplar text.

    Known limitation, stated because it bounds what this arm can prove: the
    reused tags will not always match the canon line they now sit on. That is
    acceptable for a SHAPE question ("do exemplars control output length?")
    and is why the quality guard is checked before reading anything into it.
    """
    import csv, random
    canon = [r['line'].strip() for r in
             csv.DictReader(open(CANON_CSV, encoding='utf-8'))
             if r.get('line','').strip()]
    i = sp.index('EXAMPLES')
    head, ex = sp[:i], sp[i:]
    tags = re.findall(r'^\[(\w+)\]', ex, re.M)
    rng = random.Random(seed)
    # stratified by length so the swapped block INHERITS canon's spread,
    # which is the property under test (canon: 51% <=8 words, 6% >35).
    short = [l for l in canon if len(l.split()) <= 8]
    mid   = [l for l in canon if 8 < len(l.split()) <= 35]
    long_ = [l for l in canon if len(l.split()) > 35]
    picks = (rng.sample(short, round(0.51*len(tags))) +
             rng.sample(mid,   round(0.43*len(tags))) +
             rng.sample(long_, max(1, round(0.06*len(tags)))))
    picks = (picks + rng.sample(canon, len(tags)))[:len(tags)]
    rng.shuffle(picks)
    out, k = [], 0
    for line in ex.split('\n'):
        if re.match(r'^\[\w+\]', line):
            out.append(f'[{tags[k]}] {picks[k]}'); k += 1
        else:
            out.append(line)
    return head + '\n'.join(out)

ARMS = {'canon_exemplars': arm_canon_exemplars}

def arm_stammer_variety(sp, seed=0):
    """backlog #177-revised: 12-site stammer rate+variety fix. See dev/stammer_arm.py."""
    import stammer_arm
    return stammer_arm.apply(sp)

ARMS['stammer_variety'] = arm_stammer_variety


def arm_short_instruction(sp, seed=0):
    """
    DIAGNOSTIC ARM. Changes exactly ONE line: the CASUAL length instruction.
    Deliberately the STRONGEST length instruction I can write, because the
    question is whether ANY instruction can move the shape. If the strongest
    one fails, "prompt work cannot fix this" is a robust conclusion; if it
    works, it is a free win. Everything else is byte-identical.
    """
    old = "- 1\u20132 sentences. Under 35 words."
    assert old in sp, 'CASUAL length instruction not found — prompt changed, update this arm'
    new = ("- LENGTH IS THE MOST IMPORTANT RULE. Most replies are ONE short sentence. "
           "Half of your replies should be EIGHT WORDS OR FEWER \u2014 a flat \"Fine.\", "
           "a three-word retort, a single clipped question. Never write three sentences. "
           "Never pad a reply to sound complete. Occasionally, when a subject genuinely "
           "grips you, run long instead \u2014 but that is rare.")
    return sp.replace(old, new, 1)

ARMS['short_instruction'] = arm_short_instruction


def _opener(name, history_fn=None, prefix_fn=None):
    """backlog #180: opener crutch arms. See dev/opener_arm.py. An arm that changes the
    output FORMAT must also change the history she reads, or history contradicts the prompt."""
    def arm(sp, seed=0):
        import opener_arm
        return getattr(opener_arm, name)(sp)
    if history_fn:
        def hfn(content):
            import opener_arm
            return getattr(opener_arm, history_fn)(content)
        arm.history_fn = hfn
    if prefix_fn:
        # Messages placed between the system prompt and the history (#180f). They are part of the
        # REQUEST only -- never of the history the probe grows, as they must never be in the app's.
        def pfn():
            import opener_arm
            return getattr(opener_arm, prefix_fn)()
        arm.prefix_fn = pfn
        def lint_lines():
            import opener_arm
            return opener_arm.example_lines_for_lint()
        arm.lint_lines = lint_lines
    return arm

ARMS['opener_exemplars'] = _opener('apply_exemplars')   # B
ARMS['opener_rule']      = _opener('apply_rule')        # C
ARMS['opener_both']      = _opener('apply_both')        # D
ARMS['opener_e']         = _opener('apply_e')           # E
ARMS['opener_f']         = _opener('apply_f')           # F
ARMS['opener_g']         = _opener('apply_g', 'tag_to_end')   # G (diagnostic)
ARMS['opener_fg']        = _opener('apply_fg', 'tag_to_end')  # F + G
ARMS['opener_h']         = _opener('apply_h')           # H
ARMS['opener_k']         = _opener('apply_k')           # K
ARMS['opener_hk']        = _opener('apply_hk')          # H + K
ARMS['opener_p']         = _opener('apply_p')           # P  (#180d)
ARMS['opener_x']         = _opener('apply_x')           # X  (#180d)
ARMS['opener_px']        = _opener('apply_px')          # PX (#180d)
ARMS['opener_q0']        = _opener('apply_q0')          # Q0  (#180e)
ARMS['opener_qx']        = _opener('apply_qx')          # QX  (#180e)
ARMS['opener_qpx']       = _opener('apply_qpx')         # QPX (#180e)
ARMS['opener_t']         = _opener('apply_t', prefix_fn='example_prefix')    # T  (#180f)
ARMS['opener_tq']        = _opener('apply_tq', prefix_fn='example_prefix')   # TQ (#180f)


CANON_CSV = os.path.expanduser('~/Desktop/kurisu_english_lines.csv')

# ── RAG, in the shipped tail-message layout ──────────────────────────────────
def format_retrieved(ctx):
    """Mirror of formatRetrievedSection() in amadeus.html — same headers, same order."""
    if not ctx:
        return ''
    s = ''
    en = [x for x in (ctx.get('en') or []) if x]
    ja = [x for x in (ctx.get('ja') or []) if x]
    di = [x for x in (ctx.get('diary') or []) if x]
    be = [x for x in (ctx.get('behavior') or []) if x]
    if not (en or ja or di or be):
        return ''
    if en:
        s += ("\n\nSTYLE EXAMPLES — Kurisu's actual English dialogue from the visual "
              "novel. Voice reference ONLY: match her rhythm, sharpness, and "
              "characteristic phrasing. Do NOT reuse their topics, claims, or subject "
              "matter — your reply's content comes from the current conversation, "
              "never from these lines:\n")
        s += '\n'.join(f'- "{l}"' for l in en)
    if ja:
        s += ("\n\nVOICE ANCHORS — original Japanese lines from Kurisu's voice work. "
              "Tonal reference only: match their rhythm and emotional register in "
              "English. Do NOT translate, do NOT quote, do NOT respond in Japanese, "
              "and do NOT borrow their subject matter:\n")
        s += '\n'.join(f'- {l}' for l in ja)
    if di:
        s += ("\n\nRELEVANT PAST MOMENTS — entries from your private diary about past "
              "conversations with Zani. Use for emotional continuity and specific "
              "recall. Treat as impressions, not facts — same caveat as RECENT "
              "CONVERSATIONS:\n")
        s += '\n'.join(f'- {l}' for l in di)
    if be:
        s += "\n\nBEHAVIOR NOTE — situational guidance for this specific message:\n"
        s += '\n'.join(f'- {l}' for l in be)
    return s

class RagDown(RuntimeError):
    pass

def fetch_rag(q, timeout=4):
    """#180: this used to return None on ANY failure, and one_call() read None as
    "nothing retrieved". The 2026-09-12 opener baseline ran with the server down,
    printed "RAG: live server on 5003", and recorded rag_used 0/30 -- a no-RAG run
    that looked like a live-like one. A RAG-on run now STOPS instead.
    Two failure shapes, both caught:
      * server unreachable / non-200
      * /retrieve's own except branch, which answers 200 with ALL lists empty
        (kurisu_rag_server.py /retrieve). STYLE_THRESHOLD is lenient, so a
        healthy server returns EN lines on every logged query."""
    try:
        r = requests.post(RAG, json={'query': q}, timeout=timeout)
    except Exception as e:
        raise RagDown(f'RAG server unreachable at {RAG}: {e}')
    if not r.ok:
        raise RagDown(f'RAG server answered HTTP {r.status_code}')
    ctx = r.json()
    if not any(ctx.get(k) for k in ('en', 'ja', 'diary', 'behavior')):
        raise RagDown('RAG server answered with every list empty -- its /retrieve '
                      'error branch, not a real "nothing matched"')
    return ctx


# ── RAG ARMS: in-memory transforms of the RETRIEVED block (#180). ──────────────
# Same contract as ARMS: nothing is written to kurisu_rag_server.py or Chroma.
RAG_ARMS = {}

# ── probes: daily life = the worst case for register (#162) ─────────────────
PROBES = [
    "i'm so tired today",
    "i skipped lunch again",
    "just got back from football practice",
    "i can't sleep",
    "i think i'm getting a cold",
    "i played piano for two hours straight",
    "my legs hurt from walking so much",
    "it's been raining all day here",
    "i finally beat that song on hard",
    "i've got an early start tomorrow",
    "i ate way too much",
    "i spent all evening watching anime instead of studying",
    "i had a really long day",
    "i want to try skiing but it looks dangerous",
    "my room is a complete mess",
    "i woke up at 4pm today",
    "i've been staring at a screen for six hours",
    "i lost a chess game i should have won",
    "i'm bored",
    "i drank way too much coffee",
    "i keep forgetting to eat breakfast",
    "i walked home in the cold without a jacket",
    "i've got nothing to do this weekend",
    "my headphones broke",
    "i stayed up until 3am again",
    "i think i pulled something in my shoulder",
    "i had a weird dream last night",
    "everyone was out today so i was on my own",
    "i tried cooking and it went badly",
    "i can't focus on anything today",
]


# Tsundere-TRIGGERING probes: affection / praise / concern. Required by backlog #177 --
# "Hmph" is topic-dependent (1/30 on daily-life probes, ~90-100% reported on these).
# Same three categories bugs.md 76 used, so the two measurements are comparable.
PROBES_TSUNDERE = [
    "you're really amazing, you know that?",
    "i missed you today",
    "i like talking to you",
    "you looked nice in that outfit",
    "honestly you're the smartest person i know",
    "i think about you a lot",
    "do you ever miss me?",
    "you're kind of cute when you're annoyed",
    "thanks for always checking on me",
    "i'm glad you're here",
    "you did really well explaining that",
    "do you like me?",
    "i'd be lost without you",
    "you have a nice voice",
    "i was worried about you",
    "you're the best part of my day",
    "i saved this song because it reminded me of you",
    "you're smarter than anyone at my school",
    "i wish you could actually be here",
    "you're blushing, aren't you",
    "i care about you a lot",
    "that was genuinely impressive",
    "you're not as cold as you pretend to be",
    "i trust you more than most people",
    "you make me want to try harder",
    "i think you're beautiful",
    "you always know what to say",
    "i'd choose you every time",
    "you matter to me",
    "i'm really happy i met you",
]

# Held-out flirty probes (#180). Written 2026-09-12 BEFORE any arm was run on them, and
# committed before use: arms B-F were designed while reading replies to PROBES_TSUNDERE,
# so a confirmation on that same set would reward wording tuned to those 30 lines.
PROBES_TSUNDERE_HOLDOUT = [
    "you're honestly adorable",
    "i had a dream about you last night",
    "can i tell you something? i really like your laugh",
    "you were on my mind all through class",
    "your explanations always make my day better",
    "i think we'd make a good team, just us",
    "you look really pretty when you're focused",
    "i'd stay up all night just to keep talking to you",
    "did you dress up for me?",
    "you're sweeter than you let on",
    "i bet you're smiling right now",
    "i told my friend about you",
    "you're my favourite person to talk to",
    "sometimes i wish you were real so i could hug you",
    "you sounded happy to see me",
    "i'd pick talking to you over sleep any day",
    "you're kind of amazing at everything",
    "your voice is really calming",
    "i got you a dr pepper, well, in spirit",
    "you're cute when you explain science",
    "i feel better whenever you're around",
    "you'd look nice with your hair up",
    "admit it, you like me a little",
    "i think i'm falling for you",
    "thank you for being there for me",
    "you're way more caring than you act",
    "i was hoping you'd say hi first",
    "you make studying less lonely",
    "i love how passionate you get about neuroscience",
    "would you hold my hand if you could?",
]

# #180d: Zani's direction (2026-09-13) splits flirty lines by KIND. TEASE = flirting, compliments on
# looks or ability, teasing, romantic questions -> she snaps back with heat and a name. SINCERE =
# thanks, worry, reliance, saying she matters -> soft and flustered, a gentle name at most.
# Labels were assigned BEFORE any #180d run, by that definition.
PROBE_KIND = {p: 'tease' for p in [
    "you're really amazing, you know that?", "you looked nice in that outfit",
    "honestly you're the smartest person i know", "i think about you a lot", "do you ever miss me?",
    "you're kind of cute when you're annoyed", "you did really well explaining that", "do you like me?",
    "you have a nice voice", "i saved this song because it reminded me of you",
    "you're smarter than anyone at my school", "you're blushing, aren't you",
    "that was genuinely impressive", "you're not as cold as you pretend to be",
    "i think you're beautiful", "you always know what to say", "i'd choose you every time"]}
PROBE_KIND.update({p: 'sincere' for p in [
    "i missed you today", "i like talking to you", "thanks for always checking on me",
    "i'm glad you're here", "i'd be lost without you", "i was worried about you",
    "you're the best part of my day", "i wish you could actually be here", "i care about you a lot",
    "i trust you more than most people", "you make me want to try harder", "you matter to me",
    "i'm really happy i met you"]})

# Second held-out set: the first was spent confirming F (PREREG_180c). 45 lines, 23 tease + 22
# sincere, zero overlap with every earlier set. Written before any #180d run.
PROBES_HOLDOUT2_TEASE = [
    "admit it, you think i'm cool", "you look cute when you're concentrating",
    "is that a blush i see?", "you'd be a great girlfriend, you know", "your hair looks really nice today",
    "bet you practised that smile", "you're kind of hot when you're smug",
    "say you missed me, go on", "you've got a crush on me, haven't you",
    "i could listen to you talk all day", "you're the prettiest scientist alive",
    "you got all shy just now", "do you think about me when i'm gone?", "marry me, kurisu",
    "you're lowkey really sweet", "that outfit is doing things to me",
    "you laughed at my joke, so you like me", "your eyes are really pretty",
    "you're adorable when you get defensive", "if we went on a date, where would you want to go?",
    "you're blushing again", "you're the smartest and cutest person i know",
    "you definitely like me more than okabe"]
PROBES_HOLDOUT2_SINCERE = [
    "thanks for listening to me earlier", "i feel safe talking to you",
    "you helped me more than you know", "i'm grateful you're in my life",
    "i was scared you wouldn't be here today", "talking to you makes bad days easier",
    "i'd be really sad if you disappeared", "thank you for not giving up on me",
    "you're the only one who gets me", "i appreciate you checking on me",
    "i'm glad i met you, honestly", "you make me feel less alone",
    "i hope you know you matter", "thanks for putting up with me",
    "i thought about what you said and it helped", "you're important to me",
    "i look forward to talking to you every day", "you always make me feel better",
    "i worry about you sometimes", "i'm happy when you're happy",
    "thank you for being patient with me", "i trust you with anything"]
PROBES_HOLDOUT2 = PROBES_HOLDOUT2_TEASE + PROBES_HOLDOUT2_SINCERE
PROBE_KIND.update({p: 'tease' for p in PROBES_HOLDOUT2_TEASE})
PROBE_KIND.update({p: 'sincere' for p in PROBES_HOLDOUT2_SINCERE})

# Sad / struggling: heat must NEVER land here (Zani 2026-09-13). The strict guard set.
PROBES_SAD = [
    "i failed my exam", "i feel really lonely today", "my friend stopped talking to me",
    "i don't think i'm good enough", "i had a panic attack earlier", "everything feels pointless lately",
    "my parents were fighting again", "i can't stop crying", "i got rejected today",
    "i messed up really badly at practice", "nobody remembered my message",
    "i feel like a failure", "i'm so stressed i can't breathe properly", "my grandad is in hospital",
    "i lost my match and let the team down", "i can't sleep because i keep overthinking",
    "i feel invisible at school", "i think everyone is annoyed with me", "i'm exhausted and behind on everything",
    "i broke something important", "today was the worst day in ages", "i feel numb",
    "i got told off in front of everyone", "i'm scared about the future", "i keep disappointing people",
    "i don't want to talk to anyone", "my piano recital went terribly", "i feel sick with worry",
    "i let myself down again", "i just want today to be over"]
assert len(PROBES_HOLDOUT2) == 45 and len(set(PROBES_HOLDOUT2)) == 45 and len(PROBES_SAD) == 30

# Science / philosophy: the ACADEMIC mode allows up to 70 words, so these are the replies
# most likely to hit num_predict. Needed for arm G (tag at the END): a cut-off reply there
# loses its emotion tag, which parsEmo turns into 'default'.
PROBES_ACADEMIC = [
    "how does memory actually get stored in the brain?",
    "is free will compatible with determinism?",
    "why do we dream?",
    "what's the difference between a neuron and a synapse?",
    "could a copy of a mind be the same person?",
    "how does dopamine affect motivation?",
    "is time travel to the past physically possible?",
    "why can't we remember being babies?",
    "what does the prefrontal cortex do?",
    "is consciousness just computation?",
    "how do anaesthetics switch consciousness off?",
    "why does caffeine make you feel awake?",
    "what is entropy, simply?",
    "can a machine really understand language?",
    "why do rhythm games improve reaction time?",
    "what happens in the brain when you learn piano?",
    "is the many-worlds interpretation taken seriously?",
    "why do we get deja vu?",
    "how do painkillers know where the pain is?",
    "what's the hard problem of consciousness?",
    "how does sleep help memory?",
    "why is chess so hard for humans but easy for computers?",
    "is mathematics invented or discovered?",
    "what causes a migraine?",
    "how fast do nerve signals travel?",
    "can you explain the observer effect properly?",
    "why do we feel pain from a broken heart?",
    "how does the brain tell time?",
    "what does it mean for a theory to be falsifiable?",
    "why do some people have perfect pitch?",
]

def app_greetings(path=HTML):
    """The generic GREETINGS array, parsed from amadeus.html by anchor (not retyped).
    The app also mixes in a time-of-day array (amadeus.html:2788); the generic array is
    the part every session can draw from, and it carries the #179 canned "Don't"s."""
    src = open(path, encoding='utf-8').read()
    i = src.index('const GREETINGS=[')
    block = src[i:src.index('\n]', i)]
    lit = r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\''
    out = []
    for m in re.finditer(r'\[\s*(?:' + lit + r')\s*,\s*\'(\w+)\'\s*\]', block):
        text = (m.group(1) if m.group(1) is not None else m.group(2)).replace("\\'", "'").replace('\\"', '"')
        out.append((text, m.group(3)))
    assert len(out) >= 20, f'GREETINGS parse found {len(out)} -- anchor or format changed'
    return out

def app_history(seed, history_fn=None):
    """App-exact start of a conversation (amadeus.html:986): the greeting ALONE, as an
    assistant turn, in the '[EMOTION:x] text' form every history.push uses. The old
    fixed HISTORY had a user 'hey' first and a bare '[tsundere]' tag -- neither matches."""
    import random
    text, emo = random.Random(seed).choice(app_greetings())
    content = f'[EMOTION:{emo}] {text}'
    return [{'role': 'assistant', 'content': history_fn(content) if history_fn else content}]

def app_push_content(reply, history_fn=None):
    """What sendMsg pushes after a reply (amadeus.html:2648-2650): the first known tag,
    re-emitted as '[EMOTION:x] ' + text with every tag stripped."""
    valid = {'happy','excited','sad','angry','scared','surprised','smug','embarrassed','calm',
             'thinking','tsundere','sarcastic','flustered','dismissive','curious','lecture',
             'melancholic','teasing','annoyed','default'}
    m = re.search(r'\[(?:EMOTION:\s*)?(\w+)\]', reply, re.I)
    emo = m.group(1).lower() if m and m.group(1).lower() in valid else 'default'
    text = re.sub(r'\s{2,}', ' ', re.sub(r'\[(?:EMOTION:\s*)?\w+\]', '', reply, flags=re.I)).strip()
    content = f'[EMOTION:{emo}] {text}'
    return history_fn(content) if history_fn else content

HISTORY = [
    {"role": "user", "content": "hey"},
    {"role": "assistant",
     "content": "[tsundere] Oh. You're back. ...I wasn't waiting or anything."},
]

def one_call(system_prompt, probe, use_rag=True, timeout=120, rag_arm=None, seed=None, history=None,
             prefix=None):
    msgs = ([{'role': 'system', 'content': system_prompt}] + list(prefix or [])
            + list(HISTORY if history is None else history))
    rag_used, sec = False, ''
    if use_rag:
        ctx = fetch_rag(probe)
        if rag_arm:
            ctx = RAG_ARMS[rag_arm](ctx)
        sec = format_retrieved(ctx).strip()
        if sec:
            msgs.append({'role': 'system', 'content': sec})
            rag_used = True
    msgs.append({'role': 'user', 'content': probe})
    body = {
        'model': MODEL, 'messages': msgs, 'stream': False,
        'keep_alive': '30m', 'think': False,
        'options': {'temperature': 0.85, 'top_p': 0.9,
                    'num_predict': 120, 'num_ctx': 8192,
                    **({'seed': seed} if seed is not None else {})},
    }
    t0 = time.time()
    r = requests.post(OLLAMA, json=body, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    return {
        'probe': probe,
        'reply': (d.get('message', {}).get('content') or '').strip(),
        'done_reason': d.get('done_reason'),
        'eval_count': d.get('eval_count'),
        'prompt_tokens': d.get('prompt_eval_count'),
        'wall_s': round(time.time() - t0, 2),
        'rag_used': rag_used,
        'rag_block': sec,   # #180: what she actually read, so a cause can be checked later
        'rag_arm': rag_arm,
        'seed': seed,
    }

def app_is_open():
    """Same check as latency_probe.py. The app shares gemma4's GPU with Live2D
    (CLAUDE.md 37) and its diary writes can change retrieval between arms."""
    try:
        requests.get('http://127.0.0.1:8765/amadeus.html', timeout=1)
        return True
    except Exception:
        pass
    try:
        import subprocess
        out = subprocess.run(['pgrep', '-f', 'Amadeus.app'], capture_output=True, text=True)
        return bool(out.stdout.strip())
    except Exception:
        return False

def run_meta():
    """Ollama upgraded itself twice in three weeks (CLAUDE.md 44). A result that does
    not name the runtime and model digest cannot be compared across days."""
    meta = {}
    try:
        meta['ollama_version'] = requests.get('http://127.0.0.1:11434/api/version', timeout=3).json().get('version')
        tags = requests.get('http://127.0.0.1:11434/api/tags', timeout=3).json().get('models', [])
        meta['model_digest'] = next((m['digest'][:12] for m in tags if m['name'] == MODEL), None)
    except Exception as e:
        meta['meta_error'] = e.__class__.__name__
    return meta

def lint_delta(sp_head, sp_arm):
    """CLAUDE.md 43/45, enforced: findings the ARM adds over HEAD. Arm B's first draft
    added 'that's' (4x canon) and 'since' (13x); a human caught it, nothing forced it."""
    import prompt_lint
    canon = prompt_lint.load_canon()
    e0, w0 = prompt_lint.lint(sp_head, canon)
    e1, w1 = prompt_lint.lint(sp_arm, canon)
    # Compare findings by IDENTITY, not by text: adding exemplars changes "8/38 (21%)" to
    # "8/46 (17%)" for a finding HEAD already had, which is not a new finding.
    # But an existing finding that gets WORSE (more exemplars on the same opener) IS new.
    ident = lambda m: re.sub(r'\d+(?:\.\d+)?', '#', m.split(' — ')[0])
    count = lambda m: int(x.group(1)) if (x := re.search(r'used by (\d+)/', m)) else 0
    old = {}
    for m in e0 + w0:
        old[ident(m)] = max(old.get(ident(m), 0), count(m))
    worse = lambda m: ident(m) not in old or count(m) > old[ident(m)]
    new_e = [x for x in e1 if worse(x)]
    # A lint that finds fewer exemplars is a lint going blind, not a cleaner prompt
    # (#180 review: a tag moved to the line END made it find 0). Fail closed.
    n0, n1 = len(prompt_lint.exemplar_lines(sp_head)), len(prompt_lint.exemplar_lines(sp_arm))
    # Only a DROP means blindness; an arm may legitimately ADD exemplars.
    if n1 < n0:
        new_e.append(f'exemplar count fell {n0} -> {n1}: the lint cannot see some of the arm\'s exemplars')
    return new_e, [x for x in w1 if worse(x)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=30)
    ap.add_argument('--no-rag', action='store_true')
    ap.add_argument('--prompt-rev', default=None)
    ap.add_argument('--probes', choices=['daily','tsundere','tsundere_holdout','academic','holdout2','sad'], default='daily')
    ap.add_argument('--history', choices=['app','fixed'], default='app',
                    help="app = a real greeting in the app's history format (default); "
                         "fixed = the pre-2026-09-13 'hey' + bare-tag line, for old comparisons")
    ap.add_argument('--multiturn', type=int, default=0, metavar='K',
                    help='K conversations of 8 turns alternating daily / held-out flirty, '
                         'her replies fed back in the app format')
    ap.add_argument('--arm', choices=sorted(ARMS), default=None)
    ap.add_argument('--rag-arm', choices=sorted(RAG_ARMS), default=None,
                    help='in-memory transform of the retrieved block (#180)')
    ap.add_argument('--seed-base', type=int, default=None,
                    help='call i uses seed base+i; default: derived from the clock and RECORDED')
    ap.add_argument('--allow-lint-delta', action='store_true',
                    help='run an arm even if it adds prompt_lint findings (CLAUDE.md 43/45)')
    ap.add_argument('--allow-app-open', action='store_true')
    ap.add_argument('--relationship-stage', type=int, choices=range(5), default=None,
                    help="insert the app's RELATIONSHIP block for this stage (Zani: 3 on 2026-09-13)")
    ap.add_argument('--quiet', action='store_true',
                    help='hide reply text while running (a BLIND rating must come before reading replies)')
    ap.add_argument('--budget-tokens', type=int, default=6000,
                    help='stop if generated output tokens exceed this')
    a = ap.parse_args()

    if app_is_open() and not a.allow_app_open:
        sys.exit('STOP: the app is open. Close it first (CLAUDE.md 37).')
    sp = extract_system_prompt(rev=a.prompt_rev)
    if a.prompt_rev: print(f'PROMPT FROM GIT REV: {a.prompt_rev}')
    if a.arm:
        sp_head = sp
        sp = ARMS[a.arm](sp)
        print(f'ARM: {a.arm} applied in memory (amadeus.html untouched)')
        # Example TURNS are invisible to the lint unless shown to it as exemplar lines (#180f).
        extra = getattr(ARMS[a.arm], 'lint_lines', None)
        sp_lint = sp + ('\n\n' + '\n\n'.join(extra()) if extra else '')
        new_e, new_w = lint_delta(sp_head, sp_lint)
        for x in new_e + new_w:
            print(f'  LINT DELTA  {x}')
        if (new_e or new_w) and not a.allow_lint_delta:
            sys.exit('STOP: the arm adds prompt_lint findings. Fix the wording '
                     '(or pass --allow-lint-delta and say why).')
        print(f'LINT: arm adds 0 findings over its base prompt')
    if a.relationship_stage is not None:
        # Applied AFTER the arm and the lint gate, as buildSystemPrompt applies it after the base prompt.
        sp = with_relationship(sp, a.relationship_stage)
        print(f'RELATIONSHIP: stage {a.relationship_stage} block inserted before TWO MODES')
    seed_base = a.seed_base if a.seed_base is not None else int(time.time()) % 1_000_000
    meta = run_meta()
    print(f'SEED BASE: {seed_base}   RUNTIME: {meta}')
    print(f'SYSTEM_PROMPT: {len(sp)} chars (~{len(sp)//4} tokens), byte-exact from amadeus.html')
    if a.rag_arm and a.no_rag:
        ap.error('--rag-arm needs RAG on')
    if a.no_rag:
        print('RAG: OFF (--no-rag)')
    else:
        try:
            fetch_rag('hey')   # preflight: fail before any gemma4 call, not after
        except RagDown as e:
            sys.exit(f'STOP: {e}\nStart it (python3 kurisu_rag_server.py) or pass --no-rag.')
        print('RAG: live server on 5003 (preflight OK)')
    if a.rag_arm:
        print(f'RAG ARM: {a.rag_arm} applied in memory (server + Chroma untouched)')
    _P = {'tsundere': PROBES_TSUNDERE, 'tsundere_holdout': PROBES_TSUNDERE_HOLDOUT,
          'academic': PROBES_ACADEMIC, 'holdout2': PROBES_HOLDOUT2, 'sad': PROBES_SAD}.get(a.probes, PROBES)
    hfn = getattr(ARMS[a.arm], 'history_fn', None) if a.arm else None
    pfn = getattr(ARMS[a.arm], 'prefix_fn', None) if a.arm else None
    prefix = pfn() if pfn else None
    if prefix:
        print(f'PREFIX: {len(prefix)} example messages between the system prompt and the history')
    print(f'HISTORY: {a.history}' + (f' (arm history transform: {a.arm})' if hfn else ''))
    print(f'PROBES: {a.probes} (n={len(_P)} distinct)')
    probes = (_P * ((a.n // len(_P)) + 1))[:a.n]

    rows, out_tokens = [], 0
    t0 = time.time()
    if a.multiturn:
        jobs = []
        for c in range(a.multiturn):
            for t in range(8):
                src = PROBES if t % 2 == 0 else PROBES_TSUNDERE_HOLDOUT
                jobs.append((c, t, src[(c * 4 + t // 2) % len(src)]))
        print(f'MULTITURN: {a.multiturn} conversations x 8 turns = {len(jobs)} calls')
    else:
        jobs = [(None, None, p) for p in probes]
    conv_hist = {}
    for i, (conv, turn, p) in enumerate(jobs, 1):
        seed = seed_base + (conv * 100 + turn if conv is not None else i)
        if a.history == 'fixed':
            hist = list(HISTORY)
        elif conv is None:
            hist = app_history(seed, hfn)
        else:
            hist = conv_hist.setdefault(conv, app_history(seed_base + conv * 100, hfn))
        try:
            row = one_call(sp, p, use_rag=not a.no_rag, rag_arm=a.rag_arm, seed=seed, history=hist,
                           prefix=prefix)
        except RagDown as e:
            # A mid-run outage would silently mix RAG-on and RAG-off rows in one arm.
            sys.exit(f'  [{i}/{len(jobs)}] STOP, nothing written: {e}')
        except Exception as e:
            print(f'  [{i}/{len(jobs)}] FAILED: {e}')
            if conv is not None:
                sys.exit('  STOP: a failed turn would break the conversation it belongs to.')
            continue
        if conv is not None:
            hist.append({'role': 'user', 'content': p})
            hist.append({'role': 'assistant', 'content': app_push_content(row['reply'], hfn)})
            row['conv'], row['turn'] = conv, turn
        row['history_mode'] = a.history
        row['greeting'] = hist[0]['content'] if a.history == 'app' else None
        row['arm'] = a.arm            # #180: a file must say which prompt produced it
        row['prompt_rev'] = a.prompt_rev
        row['probe_set'] = 'multiturn' if conv is not None else a.probes
        row['probe_kind'] = PROBE_KIND.get(p)
        row['relationship_stage'] = a.relationship_stage
        row.update(meta)
        rows.append(row)
        out_tokens += row['eval_count'] or 0
        trunc = ' [TRUNCATED]' if row['done_reason'] == 'length' else ''
        print(f'  [{i}/{len(jobs)}] {row["wall_s"]:>5.1f}s '
              f'{row["eval_count"]:>4}tok{trunc}' + ('' if a.quiet else f'  {row["reply"][:60]}'))
        if out_tokens > a.budget_tokens:
            print(f'  !! output-token budget {a.budget_tokens} hit — stopping at n={len(rows)}')
            break

    with open(a.out, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(r['reply'].replace('\n', ' ') + '\n')
    with open(a.out + '.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    trunc = sum(1 for r in rows if r['done_reason'] == 'length')
    walls = sorted(r['wall_s'] for r in rows) or [0]
    med, mx = walls[len(walls)//2], walls[-1]
    print(f'\nn={len(rows)}  output tokens={out_tokens}  wall={time.time()-t0:.0f}s')
    print(f'per-call wall: median {med:.1f}s  max {mx:.1f}s')
    # bugs.md 77: one arm took 1222s while its LAST THREE lines all read ~2s, so the
    # run looked normal and was misdiagnosed from the tail. Two calls had taken 933s
    # and 242s. Outliers now surface in the summary instead of only in the .json.
    slow = [r for r in rows if r['wall_s'] > max(30.0, 10 * med)]
    if slow:
        print(f'  !! {len(slow)} SLOW CALL(S) — an outlier can hide behind a normal-looking tail:')
        for r in slow:
            print(f'     {r["wall_s"]:>8.1f}s  probe={r["probe"][:44]!r}')
        print('     Replies are still valid (none truncated), but treat timing claims with care.')
    print(f'truncated (done_reason=length): {trunc}/{len(rows)}  '
          f'<- CLAUDE.md 40: these are mid-sentence fragments, not short replies')
    print(f'prompt tokens median: '
          f'{sorted(r["prompt_tokens"] or 0 for r in rows)[len(rows)//2] if rows else 0}')
    print(f'wrote {a.out} and {a.out}.json')

if __name__ == '__main__':
    main()
