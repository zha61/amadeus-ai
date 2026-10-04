#!/usr/bin/env python3
"""#221b Stage 2c — does a lower Fish temperature cut s2.1's pitch outliers without making her calm? (PREREG_221b2.md,
ADDENDUM 2c). Free model only; every arm = C (s2.1-pro-free + the Step 0c prosody) with only `temperature` changed.

  part1 [--dry]   C6 (0.6) and C5 (0.5): 3 draws x 16 lines; C7 (0.7): 1 new draw x 16 lines (+ the 32 2b C clips)
  screen1         app CLOSED: pitch, level, peak, loop / bleed / pause screens for every Part 1 clip
  decide1         the pre-registered Part 1 rule -> t2c_part1.json (chosen arm or STOP)
  part2 [--dry]   fresh draws: chosen arm and C7, 2 draws x 16 lines
  screen2         app CLOSED: screens for the Part 2 clips
  make2 / score2 ANSWERS   the blind sheet (seed 2214) and its score -> result_2c.json
  selftest        rules on synthetic data; no audio, no network
"""
import difflib, json, math, os, random, re, shutil, statistics as st, sys
from arms_b2 import HERE, AUDIO, load_lines, request_for, prosody

TEMPS = {'C7': 0.7, 'C6': 0.6, 'C5': 0.5}
CLIPS = os.path.join(HERE, 't2c_clips.json')
SCREENS = os.path.join(HERE, 't2c_screens.json')
PART1 = os.path.join(HERE, 't2c_part1.json')
CAP = {'part1': 0.80, 'part2': 0.45}
HIGH_ST = 4.0                       # a "high" clip: > +4.0 semitones above today's voice (A median of its line)


def req(arm, ln, pros):
    payload, model = request_for('C', ln['emotion'], ln['jp'], pros)
    return {**payload, 'temperature': TEMPS[arm]}, model


def load(path, default):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


# ───────────────────────── rules (pure) ─────────────────────────
def deviations(rows):
    """|semitone - median of the same arm on the same line| for every row. rows: {'arm','id','st'}."""
    med = {}
    for r in rows:
        med.setdefault((r['arm'], r['id']), []).append(r['st'])
    med = {k: st.median(v) for k, v in med.items()}
    return [(r['arm'], abs(r['st'] - med[(r['arm'], r['id'])])) for r in rows]


def stray(rows, arm):
    return st.mean(d for a, d in deviations(rows) if a == arm)


def perm_p(rows, arm, base='C7', n=5000, seed=2214):
    """One-sided: P(stray(base) - stray(arm) >= observed) when arm labels are shuffled WITHIN each line."""
    R = [r for r in rows if r['arm'] in (arm, base)]
    obs = stray(R, base) - stray(R, arm)
    rng, hits = random.Random(seed), 0
    by = {}
    for r in R:
        by.setdefault(r['id'], []).append(r)
    for _ in range(n):
        S = []
        for g in by.values():
            labels = [r['arm'] for r in g]
            rng.shuffle(labels)
            S += [{**r, 'arm': a} for r, a in zip(g, labels)]
        hits += (stray(S, base) - stray(S, arm)) >= obs - 1e-12
    return (hits + 1) / (n + 1)


def decide_part1(rows, flags):
    """rows: {'arm','id','st'}; flags: {arm: {'loop','bleed','pause'} counts}. -> dict incl. 'chosen' (arm or None)."""
    out = {'stray': {a: round(stray(rows, a), 3) for a in TEMPS},
           'high': {a: sum(r['st'] > HIGH_ST for r in rows if r['arm'] == a) for a in TEMPS},
           'n': {a: sum(r['arm'] == a for r in rows) for a in TEMPS}, 'arms': {}}
    for a in ('C6', 'C5'):
        p = perm_p(rows, a)
        f, b = flags[a], flags['C7']
        checks = {'stray<=0.75xC7': out['stray'][a] <= 0.75 * out['stray']['C7'], 'perm_p<=0.05': p <= 0.05,
                  'high<=C7': out['high'][a] <= out['high']['C7'],
                  'screens': f['loop'] < 2 and f['bleed'] <= b['bleed'] + 4 and f['pause'] <= b['pause'] + 4}
        out['arms'][a] = {'perm_p': round(p, 4), 'checks': checks, 'qualifies': all(checks.values())}
    out['chosen'] = next((a for a in ('C6', 'C5') if out['arms'][a]['qualifies']), None)   # 0.6 first: smaller change
    return out


BOX = 'xnhc'          # broken, not her, too high, too calm


def build_items(ids, seed=2214):
    rng = random.Random(seed)
    items = [{'id': i, 'draw': d, 'cand_side': 'A' if rng.random() < 0.5 else 'B', 'kind': 'test', 'repeat_of': None}
             for i in ids for d in (1, 2)]
    for k in rng.sample(range(len(items)), 4):
        o = items[k]
        items.append({**o, 'cand_side': 'B' if o['cand_side'] == 'A' else 'A', 'kind': 'repeat', 'repeat_of': k})
    for i in rng.sample(ids, 4):           # C7 d2 (as "candidate") vs C7 d1
        items.append({'id': i, 'draw': 2, 'cand_side': 'A' if rng.random() < 0.5 else 'B', 'kind': 'noise', 'repeat_of': None})
    order = list(range(len(items)))
    rng.shuffle(order)
    pos = {o: n for n, o in enumerate(order)}
    out = [dict(items[i]) for i in order]
    for it in out:
        if it['repeat_of'] is not None:
            it['repeat_of'] = pos[it['repeat_of']]
    return out


def parse(text):
    ans = {}
    for line in text.splitlines():
        t = line.split()
        if len(t) >= 2 and t[0].isdigit() and t[1].upper() in ('A', 'B', '='):
            f = {x.lower() for x in t[2:]}
            ans[int(t[0])] = {'pick': t[1].upper(), **{b: {s for s in 'AB' if f'{b}{s.lower()}' in f} for b in BOX}}
    return ans


def verdict(it, a, loops=frozenset()):
    """A broken / not-her / looping candidate clip = a loss (as in 2a/2b)."""
    if it['cand_side'] in a['x'] or it['cand_side'] in a['n'] or (it['id'], it['draw']) in loops:
        return 'base'
    if a['pick'] == '=':
        return 'tie'
    return 'cand' if a['pick'] == it['cand_side'] else 'base'


def score2(items, ans, loops=frozenset(), screens_ok=True):
    missing = [k for k in range(1, len(items) + 1) if k not in ans]
    if missing:
        raise SystemExit(f'STOP: no answer for items {missing}')
    w = l = t = 0
    boxes = {b: {'T': set(), 'C7': set()} for b in BOX}
    for k, it in enumerate(items, 1):
        if it['kind'] == 'test' or it['kind'] == 'repeat':
            for b in BOX:
                for s in ans[k][b]:
                    boxes[b]['T' if s == it['cand_side'] else 'C7'].add((it['id'], it['draw']))
        if it['kind'] != 'test':
            continue
        v = verdict(it, ans[k], loops)
        w, l, t = w + (v == 'cand'), l + (v == 'base'), t + (v == 'tie')
    agree = total = 0
    for k, it in enumerate(items, 1):
        if it['kind'] == 'repeat':
            total += 1
            agree += verdict(it, ans[k], loops) == verdict(items[it['repeat_of']], ans[it['repeat_of'] + 1], loops)
    n = {b: {a: len(v) for a, v in boxes[b].items()} for b in BOX}
    checks = {'trusted': agree >= 3, 'losses<=wins+2': l <= w + 2,
              'too_calm_T<=C7+1': n['c']['T'] <= n['c']['C7'] + 1, 'too_high_T<=C7': n['h']['T'] <= n['h']['C7'],
              'not_her_T<=2': n['n']['T'] <= 2, 'screens': screens_ok}
    return {'wins': w, 'losses': l, 'ties': t, 'boxes': {'broken': n['x'], 'not_her': n['n'], 'too_high': n['h'],
            'too_calm': n['c']}, 'consistency': f'{agree}/{total}', 'checks': checks, 'passes': all(checks.values())}


# ───────────────────────── audio work ─────────────────────────
def synth_part(part, plan):
    from common import Guard, synth, USD_PER_BYTE, MARGIN
    L, pros = load_lines(), prosody()
    clips = load(CLIPS, [])
    have = {(c['part'], c['arm'], c['id'], c['draw']) for c in clips}
    todo = [(a, i, d) for a, i, d in plan if (part, a, i, d) not in have]
    reqs = {k: req(k[0], L[k[1]], pros) for k in todo}
    est = sum(len(p['text'].encode()) for p, _ in reqs.values()) * USD_PER_BYTE * MARGIN
    print(f'{part}: {len(todo)} FREE calls, real $0; guard estimate ${est:.4f} (every call as paid, x{MARGIN}); cap ${CAP[part]:.2f}')
    if est > CAP[part]:
        sys.exit('STOP: estimate over the cap — nothing sent')
    if '--dry' in sys.argv:
        return
    guard = Guard(cap=CAP[part])
    for k in todo:
        payload, model = reqs[k]
        assert model == 's2.1-pro-free' and payload['prosody'] == pros
        path = os.path.join(AUDIO, f't2c_{part}_{k[0]}_{k[1]}_{k[2]}.mp3')
        sha = synth(payload['text'], path, guard=guard, payload_override=payload, model=model)
        if os.path.getsize(path) < 2000:
            sys.exit(f'STOP: {path} is not audio')
        clips.append({'part': part, 'arm': k[0], 'id': k[1], 'draw': k[2], 'temperature': payload['temperature'],
                      'model': model, 'file': os.path.relpath(path, HERE), 'sha256': sha})
        json.dump(clips, open(CLIPS, 'w', encoding='utf-8'), indent=1)
        print(f'  {part} {k[0]} {k[1]} d{k[2]} ok')
    cost = load(os.path.join(HERE, 'cost_b2.json'), {})
    cost[f't2c_{part}'] = guard.report()
    json.dump(cost, open(os.path.join(HERE, 'cost_b2.json'), 'w'), indent=1)


def screen(part):
    from common import app_running, internal_pauses, loudness
    from step0 import true_peak
    from measure_b2 import median_f0
    if app_running():
        sys.exit('STOP: Amadeus is running — Whisper would share the GPU with her rendering')
    import mlx_whisper
    L = load_lines()
    A = json.load(open(os.path.join(HERE, 'screens_b2.json'), encoding='utf-8'))['rows']
    a_f0 = {i: st.median(r['f0'] for r in A if r['id'] == i and r['arm'] == 'A' and r['f0']) for i in L}
    a_dur = {i: st.median(r['dur'] for r in A if r['id'] == i and r['arm'] == 'A') for i in L}
    norm = lambda s: re.sub(r'[\W_]', '', s)
    rows = load(SCREENS, [])
    done = {r['file'] for r in rows}
    for c in load(CLIPS, []):
        if c['part'] != part or c['file'] in done:
            continue
        ln, path = L[c['id']], os.path.join(HERE, c['file'])
        dur, pauses = internal_pauses(path)
        tr = mlx_whisper.transcribe(path, path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='ja')['text'].strip()
        blocks = [b for b in difflib.SequenceMatcher(None, norm(ln['jp']), norm(tr), autojunk=False).get_matching_blocks() if b.size >= 2]
        lead = blocks[0].b if blocks else len(norm(tr))
        f0 = median_f0(path)
        rows.append({**{k: c[k] for k in ('part', 'arm', 'id', 'draw', 'file')}, 'dur': round(dur, 2),
                     'pause': any(p > 1.2 for p in pauses) or len([p for p in pauses if p > 0.6]) > ln['n_sentences'] - 1,
                     'bleed': bool(re.findall(r'[A-Za-z]{3,}', tr)) or lead >= 4, 'loop': dur > 2 * a_dur[c['id']],
                     'lufs': loudness(path), 'peak_dbtp': true_peak(path), 'f0': f0,
                     'st': None if not f0 else round(12 * math.log2(f0 / a_f0[c['id']]), 2), 'transcript': tr})
        r = rows[-1]
        print(f"{part} {c['arm']} {c['id']:<14} d{c['draw']} st {r['st']} lufs {r['lufs']} "
              f"{'LOOP ' if r['loop'] else ''}{'BLEED ' if r['bleed'] else ''}{'PAUSE ' if r['pause'] else ''}")
        json.dump(rows, open(SCREENS, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def part1_rows():
    """Part 1 data: the new clips + the 32 2b C clips as C7 (same config, temperature 0.7, same estimator)."""
    b2 = json.load(open(os.path.join(HERE, 'screens_b2.json'), encoding='utf-8'))['rows']
    A = {i: st.median(r['f0'] for r in b2 if r['id'] == i and r['arm'] == 'A' and r['f0']) for i in {r['id'] for r in b2}}
    rows = [{'arm': 'C7', 'id': r['id'], 'st': 12 * math.log2(r['f0'] / A[r['id']]), 'loop': r['loop_flag'],
             'bleed': r['bleed_flag'], 'pause': r['pause_flag']} for r in b2 if r['arm'] == 'C' and r['f0']]
    rows += [{k: r[k] for k in ('arm', 'id', 'st', 'loop', 'bleed', 'pause')} for r in load(SCREENS, [])
             if r['part'] == 'part1' and r['st'] is not None]
    flags = {a: {k: sum(bool(r[k]) for r in rows if r['arm'] == a) for k in ('loop', 'bleed', 'pause')} for a in TEMPS}
    return rows, flags


def make2():
    from blind_b import page, level_copy, esc
    L = load_lines()
    pick = json.load(open(PART1))['chosen']
    files = {(c['arm'], c['id'], c['draw']): os.path.join(HERE, c['file']) for c in load(CLIPS, []) if c['part'] == 'part2'}
    target = json.load(open(os.path.join(HERE, 'screens_b2.json'), encoding='utf-8'))['a_median_lufs']
    items = build_items(list(L))
    d = os.path.join(os.path.dirname(HERE), 'voice_test', '221b2', 'sheet2c')
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    cards, gains = [], []
    for k, it in enumerate(items, 1):
        cand = files[(pick if it['kind'] != 'noise' else 'C7', it['id'], it['draw'])]
        base = files[('C7', it['id'], it['draw'] if it['kind'] != 'noise' else 1)]
        left, right = (cand, base) if it['cand_side'] == 'A' else (base, cand)
        for side, src in (('l', left), ('r', right)):
            g, pk = level_copy(src, os.path.join(d, f'item{k:02d}_{side}.mp3'), target)
            gains.append({'item': k, 'side': side, 'gain_db': g, 'peak_dbfs': pk})
        ln = L[it['id']]
        box = lambda s, k: ''.join(f'<label><input type="checkbox" id="{b}{s}{k}"> {t}</label>' for b, t in
                                   (('x', 'broken'), ('n', 'not her'), ('h', 'too high'), ('c', 'too calm')))
        brk = '<p class="ctx"><b>Halfway. Take a short break.</b></p>' if k == 21 else ''
        cards.append(f'{brk}<div class="card"><div><span class="n">{k}.</span> <span class="ctx">She says: “{esc(ln["en"])}”</span></div>'
                     f'<div class="jp">{esc(ln["jp"])}</div>'
                     f'<div class="row"><b>A</b><audio controls preload="none" src="item{k:02d}_l.mp3"></audio>{box("a", k)}</div>'
                     f'<div class="row"><b>B</b><audio controls preload="none" src="item{k:02d}_r.mp3"></audio>{box("b", k)}</div>'
                     '<div class="row">' + ''.join(f'<label><input type="radio" name="p{k}" value="{v}"> {v}</label>' for v in ('A', 'B', '='))
                     + '</div></div>')
    intro = ('<h1>Which one do you want her to sound like here?</h1><p>Use the same headphones as before. Pick <b>A</b>, <b>B</b> '
             'or <b>=</b>. Under a clip, tick <b>broken</b>, <b>not her</b>, <b>too high</b> (pitch higher than her normal voice) '
             'or <b>too calm</b> (not flustered / defensive enough). The volume is evened out on purpose. Some items appear twice. '
             'Your answers save in this page.</p>')
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
        page('Kurisu Voice Sheet 4', intro, cards, len(items), 'kurisu221b2_s2c', 'p', [f'{b}{s}' for b in BOX for s in 'ab']))
    json.dump({'seed': 2214, 'cand_arm': pick, 'target_lufs': target, 'items': items, 'gains': gains},
              open(os.path.join(HERE, 'sheet_key_2c.json'), 'w'), indent=1)
    print(f'wrote {d}/index.html ({len(items)} items); candidate {pick}')


def selftest():
    ids = [f'l{i}' for i in range(16)]
    rng = random.Random(1)
    mk = lambda arm, sd, n, hi=0: [{'arm': arm, 'id': i, 'st': 2.0 + rng.gauss(0, sd) + (5 if k < hi and j == 0 else 0)}
                                   for j, i in enumerate(ids) for k in range(n)]
    ok = {a: {'loop': 0, 'bleed': 0, 'pause': 0} for a in TEMPS}
    # a. C6 halves the spread, C5 does not change it -> C6 chosen
    r = decide_part1(mk('C7', 1.2, 3) + mk('C6', 0.5, 3) + mk('C5', 1.2, 3), ok)
    assert r['chosen'] == 'C6' and not r['arms']['C5']['qualifies'], r
    # b. only C5 tightens -> C5
    r = decide_part1(mk('C7', 1.2, 3) + mk('C6', 1.2, 3) + mk('C5', 0.5, 3), ok)
    assert r['chosen'] == 'C5', r
    # c. nothing tightens -> STOP
    assert decide_part1(mk('C7', 1.0, 3) + mk('C6', 1.0, 3) + mk('C5', 1.0, 3), ok)['chosen'] is None
    # d. tighter but MORE high clips -> not qualified
    r = decide_part1(mk('C7', 0.5, 3) + mk('C6', 0.2, 3, hi=2) + mk('C5', 0.5, 3), ok)
    assert r['high']['C7'] == 0 and r['high']['C6'] == 2 and not r['arms']['C6']['checks']['high<=C7'], r['high']
    # e. tighter but 2 loops -> not qualified
    bad = {**ok, 'C6': {'loop': 2, 'bleed': 0, 'pause': 0}}
    assert not decide_part1(mk('C7', 1.2, 3) + mk('C6', 0.5, 3) + mk('C5', 1.2, 3), bad)['arms']['C6']['qualifies']
    # sheet
    it = build_items(ids)
    assert len(it) == 40 and sum(x['kind'] == 'test' for x in it) == 32
    fmt = lambda picks, extra=None: parse('\n'.join(f'{k} {p}' + ((' ' + extra[k]) if extra and k in extra else '')
                                                   for k, p in enumerate(picks, 1)))
    flip = lambda s: 'B' if s == 'A' else 'A'
    tie = ['='] * 40
    r = score2(it, fmt(tie))
    assert r['passes'] and r['ties'] == 32, r                                  # no difference -> T passes (non-inferior)
    lose = [flip(x['cand_side']) for x in it]
    assert not score2(it, fmt(lose))['passes']                                 # T loses every pair
    tk = [k for k, x in enumerate(it, 1) if x['kind'] == 'test']
    r = score2(it, fmt(tie, {k: 'c' + it[k - 1]['cand_side'].lower() for k in tk[:2]}))
    assert not r['checks']['too_calm_T<=C7+1'], r                              # 2 too-calm on T, 0 on C7
    r = score2(it, fmt(tie, {k: 'h' + flip(it[k - 1]['cand_side']).lower() for k in tk[:3]}))
    assert r['passes'] and r['boxes']['too_high'] == {'T': 0, 'C7': 3}         # too-high on C7 only -> fine
    r = score2(it, fmt(tie, {tk[0]: 'h' + it[tk[0] - 1]['cand_side'].lower()}))
    assert not r['checks']['too_high_T<=C7']
    assert not score2(it, fmt(['A'] * 40))['checks']['trusted']                # always-A rater
    json.dumps(r)
    print('t2c selftest 11/11 OK')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    L_ids = None
    if cmd == 'selftest':
        selftest()
    elif cmd == 'part1':
        ids = list(load_lines())
        synth_part('part1', [(a, i, d) for i in ids for a, n in (('C6', 3), ('C5', 3), ('C7', 1)) for d in range(1, n + 1)])
    elif cmd == 'screen1':
        screen('part1')
    elif cmd == 'decide1':
        rows, flags = part1_rows()
        r = {**decide_part1(rows, flags), 'flags': flags}
        json.dump(r, open(PART1, 'w'), indent=1)
        print(json.dumps(r, indent=1))
        print('Part 1:', f"{r['chosen']} goes to Part 2" if r['chosen'] else 'NO arm qualifies — STOP and ask Zani')
    elif cmd == 'part2':
        pick = json.load(open(PART1)).get('chosen')
        if not pick:
            sys.exit('STOP: no arm qualified in Part 1')
        ids = list(load_lines())
        synth_part('part2', [(a, i, d) for i in ids for a in (pick, 'C7') for d in (1, 2)])
    elif cmd == 'screen2':
        screen('part2')
    elif cmd == 'make2':
        make2()
    elif cmd == 'score2':
        k = json.load(open(os.path.join(HERE, 'sheet_key_2c.json')))
        S = [r for r in load(SCREENS, []) if r['part'] == 'part2']
        pick = k['cand_arm']
        f = {a: {x: sum(bool(r[x]) for r in S if r['arm'] == a) for x in ('loop', 'bleed', 'pause')} for a in (pick, 'C7')}
        ok = f[pick]['loop'] < 2 and f[pick]['bleed'] <= f['C7']['bleed'] + 4 and f[pick]['pause'] <= f['C7']['pause'] + 4
        loops = {(r['id'], r['draw']) for r in S if r['arm'] == pick and r['loop']}
        r = {**score2(k['items'], parse(open(sys.argv[2]).read()), loops, ok), 'cand_arm': pick, 'flags': f}
        print(json.dumps(r, indent=1))
        json.dump(r, open(os.path.join(HERE, 'result_2c.json'), 'w'), indent=1)
    else:
        sys.exit(__doc__)
