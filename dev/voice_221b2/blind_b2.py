#!/usr/bin/env python3
"""#221b2 sheets for Zani and their scorers (PREREG_221b2.md).

  make2b            32 test pairs (C vs A, 16 lines x 2 draws) + 4 flipped repeats + 4 A1-vs-A2 noise = 40, seed 2212.
                    Every copy level-matched to the median A loudness. No arm label on the page.
  score2b ANSWERS   "<n> <A|B|=> [xa] [xb] [na] [nb] [ma] [mb]"  (x = broken, n = not her, m = too much)
  make3             Stage 3: the 8 paid clips, NATIVE level (what the app would play). fine / problem + boxes.
  score3 ANSWERS    "<n> <F|P> [x] [n]"
  selftest          simulated raters + wrong-key mutant; no audio needed.
Sheets go to the git-ignored dev/voice_test/221b2/. Open index.html in Google Chrome (the app's preview
pane cannot play MP3s). The keys (sheet_key_*.json) stay here — never show them to him.
"""
import argparse, json, math, os, random, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'voice_221b'))
from blind_b import page, level_copy, esc               # noqa: E402  (same page/JS as the 2a sheet he used)
ROOT = os.path.join(os.path.dirname(HERE), 'voice_test', '221b2')
BOXES = ['xa', 'xb', 'na', 'nb', 'ma', 'mb']


def line_ids():
    return [l['id'] for l in json.load(open(os.path.join(HERE, 'lines_b2.json'), encoding='utf-8'))['lines']]


def roles():
    return {l['id']: (l['role'], l['emotion']) for l in json.load(open(os.path.join(HERE, 'lines_b2.json'), encoding='utf-8'))['lines']}


def build_items(ids, seed=2212, n_repeat=4, n_noise=4):
    rng = random.Random(seed)
    items = [{'id': i, 'cand': 'C', 'draw': d, 'base_draw': d, 'cand_side': 'A' if rng.random() < 0.5 else 'B',
              'kind': 'test', 'repeat_of': None} for i in ids for d in (1, 2)]
    for k in rng.sample(range(len(items)), n_repeat):
        o = items[k]
        items.append({**o, 'cand_side': 'B' if o['cand_side'] == 'A' else 'A', 'kind': 'repeat', 'repeat_of': k})
    for i in rng.sample(ids, n_noise):          # A2 plays the "candidate" role, A1 the base
        items.append({'id': i, 'cand': 'A', 'draw': 2, 'base_draw': 1, 'cand_side': 'A' if rng.random() < 0.5 else 'B',
                      'kind': 'noise', 'repeat_of': None})
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
            ans[int(t[0])] = {'pick': t[1].upper(), **{b: {s for s in 'AB' if f'{b}{s.lower()}' in f} for b in 'xnm'}}
    return ans


def verdict(it, a, loops=frozenset()):
    """'cand' | 'base' | 'tie'. A broken / not-her / looping CANDIDATE clip = loss (as in 2a)."""
    if it['cand_side'] in a['x'] or it['cand_side'] in a['n'] or (it['id'], it['cand'], it['draw']) in loops:
        return 'base'
    if a['pick'] == '=':
        return 'tie'
    return 'cand' if a['pick'] == it['cand_side'] else 'base'


def sign_p(w, l):
    """Exact one-sided sign test on non-tie pairs: P(X >= w), X ~ Bin(w + l, 1/2)."""
    n = w + l
    return sum(math.comb(n, k) for k in range(w, n + 1)) / 2 ** n if n else 1.0


def score(items, ans, role, screens=None):
    missing = [k for k in range(1, len(items) + 1) if k not in ans]
    if missing:
        raise SystemExit(f'STOP: no answer for items {missing}')
    loops = {(r['id'], r['arm'], r['draw']) for r in screens['rows'] if r['loop_flag']} if screens else set()
    res = {g: {'wins': 0, 'losses': 0, 'ties': 0} for g in ('target', 'guard', 'tsundere', 'flustered')}
    net, nother, much = {}, {'target': set(), 'guard': set()}, {'C': set(), 'A': set()}
    for k, it in enumerate(items, 1):
        side = lambda s: (it['id'], it['cand'], it['draw']) if s == it['cand_side'] else (it['id'], 'A', it['base_draw'])
        rl, emo = role[it['id']]
        for s in ans[k]['n']:
            if side(s)[1] == 'C':
                nother[rl].add(side(s))
        for s in ans[k]['m']:
            much[side(s)[1]].add(side(s))
        if it['kind'] != 'test':
            continue
        v = verdict(it, ans[k], loops)
        key = {'cand': 'wins', 'base': 'losses', 'tie': 'ties'}[v]
        res[rl][key] += 1
        if emo in ('tsundere', 'flustered'):
            res[emo][key] += 1
        if rl == 'target':
            net[it['id']] = net.get(it['id'], 0) + {'cand': 1, 'base': -1, 'tie': 0}[v]
    agree = total = 0
    for k, it in enumerate(items, 1):
        if it['kind'] == 'repeat':
            total += 1
            agree += verdict(it, ans[k], loops) == verdict(items[it['repeat_of']], ans[it['repeat_of'] + 1], loops)
    noise = [verdict(it, ans[k]) for k, it in enumerate(items, 1) if it['kind'] == 'noise']
    T, G = res['target'], res['guard']
    pos, neg = sum(v > 0 for v in net.values()), sum(v < 0 for v in net.values())
    screen_ok = True if screens is None else screens['verdict']['pass']
    checks = {'trusted': agree >= 3,
              'sign_p<=0.05': sign_p(T['wins'], T['losses']) <= 0.05,
              'lines': pos >= neg + 2,
              'tsundere': res['tsundere']['wins'] >= res['tsundere']['losses'],
              'flustered': res['flustered']['wins'] >= res['flustered']['losses'],
              'not_her_target<=2': len(nother['target']) <= 2,
              'guard_losses<=wins+2': G['losses'] <= G['wins'] + 2,
              'not_her_guard<=2': len(nother['guard']) <= 2,
              'screens': screen_ok}
    return {**res, 'sign_p_target': round(sign_p(T['wins'], T['losses']), 5), 'lines_net_pos': pos,
            'lines_net_neg': neg, 'not_her_target_C': len(nother['target']), 'not_her_guard_C': len(nother['guard']),
            'too_much_C': len(much['C']), 'too_much_A': len(much['A']), 'consistency': f'{agree}/{total}',
            'noise_non_tie': f'{sum(v != "tie" for v in noise)}/{len(noise)}', 'checks': checks,
            'passes': all(checks.values())}


def make2b():
    L = {l['id']: l for l in json.load(open(os.path.join(HERE, 'lines_b2.json'), encoding='utf-8'))['lines']}
    screens = json.load(open(os.path.join(HERE, 'screens_b2.json'), encoding='utf-8'))
    target = screens['a_median_lufs']
    files = {(c['id'], c['arm'], c['draw']): os.path.join(HERE, c['file'])
             for c in json.load(open(os.path.join(HERE, 'clips_b2.json'), encoding='utf-8'))}
    items = build_items(list(L))
    d = os.path.join(ROOT, 'sheet2b')
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    cards, gains = [], []
    for k, it in enumerate(items, 1):
        cand, base = files[(it['id'], it['cand'], it['draw'])], files[(it['id'], 'A', it['base_draw'])]
        left, right = (cand, base) if it['cand_side'] == 'A' else (base, cand)
        for side, src in (('l', left), ('r', right)):
            g, pk = level_copy(src, os.path.join(d, f'item{k:02d}_{side}.mp3'), target)
            gains.append({'item': k, 'side': side, 'gain_db': g, 'peak_dbfs': pk})
        ln = L[it['id']]
        box = lambda s, k: ''.join(f'<label><input type="checkbox" id="{b}{s}{k}"> {t}</label>'
                                   for b, t in (('x', 'broken'), ('n', 'not her'), ('m', 'too much')))
        brk = '<p class="ctx"><b>Halfway. Take a short break.</b></p>' if k == 21 else ''
        cards.append(f'{brk}<div class="card"><div><span class="n">{k}.</span> <span class="ctx">She says: “{esc(ln["en"])}”</span></div>'
                     f'<div class="jp">{esc(ln["jp"])}</div>'
                     f'<div class="row"><b>A</b><audio controls preload="none" src="item{k:02d}_l.mp3"></audio>{box("a", k)}</div>'
                     f'<div class="row"><b>B</b><audio controls preload="none" src="item{k:02d}_r.mp3"></audio>{box("b", k)}</div>'
                     '<div class="row">' + ''.join(f'<label><input type="radio" name="p{k}" value="{v}"> {v}</label>' for v in ('A', 'B', '='))
                     + '</div></div>')
    intro = ('<h1>Which one do you want her to sound like here?</h1><p>Use the same headphones you use with Amadeus. '
             'Each item plays the same Japanese line twice, <b>A</b> and <b>B</b>. Judge the voice. Pick <b>A</b>, <b>B</b>, or '
             '<b>=</b> (no difference). Under a clip, tick <b>broken</b> (English words, glitch, dead air), <b>not her</b> (does '
             'not sound like Kurisu) or <b>too much</b> (over-acted for this line). The volume is evened out on purpose. Some '
             'items appear twice. Your answers save in this page.</p>')
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
        page('Kurisu Voice Sheet 3', intro, cards, len(items), 'kurisu221b2_s2b', 'p', BOXES))
    json.dump({'seed': 2212, 'target_lufs': target, 'items': items, 'gains': gains},
              open(os.path.join(HERE, 'sheet_key_2b.json'), 'w'), indent=1)
    hot = [g for g in gains if g['peak_dbfs'] is not None and g['peak_dbfs'] > -0.3]
    print(f'wrote {d}/index.html ({len(items)} items), target {target} LUFS; clips near clipping: {len(hot)}')


def parse3(text):
    ans = {}
    for line in text.splitlines():
        t = line.split()
        if len(t) >= 2 and t[0].isdigit() and t[1].upper() in ('F', 'P'):
            f = {x.lower() for x in t[2:]}
            ans[int(t[0])] = {'pick': t[1].upper(), 'x': 'x' in f, 'n': 'n' in f}
    return ans


def score3(n, ans):
    missing = [k for k in range(1, n + 1) if k not in ans]
    if missing:
        raise SystemExit(f'STOP: no answer for items {missing}')
    x, nh = sum(a['x'] for a in ans.values()), sum(a['n'] for a in ans.values())
    return {'broken': x, 'not_her': nh, 'problem': sum(a['pick'] == 'P' for a in ans.values()),
            'passes': x == 0 and nh <= 1}


def make3():
    L = {l['id']: l for l in json.load(open(os.path.join(HERE, 'lines_b2.json'), encoding='utf-8'))['lines']}
    P = [c for c in json.load(open(os.path.join(HERE, 'clips_b2.json'), encoding='utf-8')) if c['arm'] == 'P']
    random.Random(2213).shuffle(P)
    d = os.path.join(ROOT, 'sheet3')
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    cards = []
    for k, c in enumerate(P, 1):
        shutil.copyfile(os.path.join(HERE, c['file']), os.path.join(d, f'clip{k:02d}.mp3'))
        ln = L[c['id']]
        cards.append(f'<div class="card"><div><span class="n">{k}.</span> <span class="ctx">She says: “{esc(ln["en"])}”</span></div>'
                     f'<div class="jp">{esc(ln["jp"])}</div><div class="row"><audio controls preload="none" src="clip{k:02d}.mp3"></audio>'
                     f'<label><input type="checkbox" id="x{k}"> broken</label><label><input type="checkbox" id="n{k}"> not her</label></div>'
                     '<div class="row">' + ''.join(f'<label><input type="radio" name="p{k}" value="{v}"> {t}</label>'
                                                   for v, t in (('F', 'fine'), ('P', 'problem'))) + '</div></div>')
    intro = ('<h1>Does she sound right?</h1><p>These clips play at the level the app would use. Pick <b>fine</b> or '
             '<b>problem</b>. Tick <b>broken</b> (English words, glitch, dead air) or <b>not her</b> when it applies.</p>')
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
        page('Kurisu Voice Check 3', intro, cards, len(P), 'kurisu221b2_s3', 'p', ['x', 'n']))
    json.dump({'seed': 2213, 'items': [{'id': c['id'], 'file': c['file']} for c in P]},
              open(os.path.join(HERE, 'sheet_key_3.json'), 'w'), indent=1)
    print(f'wrote {d}/index.html ({len(P)} items)')


def selftest():
    ids = [f't{i}' for i in (2, 4, 6, 8)] + [f'f{i}' for i in (2, 4, 6, 8)] + \
          [f'g_{e}{n}' for e in ('teasing', 'sarcastic', 'dismissive', 'curious') for n in (1, 2)]
    role = {i: ('guard', i[2:-1]) if i.startswith('g_') else ('target', 'tsundere' if i[0] == 't' else 'flustered') for i in ids}
    it = build_items(ids)
    assert len(it) == 40 and sum(x['kind'] == 'test' for x in it) == 32 and sum(x['kind'] == 'noise' for x in it) == 4
    for x in it:
        if x['kind'] == 'repeat':
            o = it[x['repeat_of']]
            assert (o['id'], o['draw']) == (x['id'], x['draw']) and o['cand_side'] != x['cand_side']
    fmt = lambda picks, extra=None: parse('\n'.join(f'{k} {p}' + ((' ' + extra[k]) if extra and k in extra else '')
                                                   for k, p in enumerate(picks, 1)))
    flip = lambda s: 'B' if s == 'A' else 'A'
    prefer_c = [x['cand_side'] if x['cand'] == 'C' else 'A' for x in it]
    r = score(it, fmt(prefer_c), role)
    assert r['passes'] and r['target']['wins'] == 16 and r['sign_p_target'] < 0.001, r
    # a. always-A rater: repeats disagree -> untrusted
    assert not score(it, fmt(['A'] * 40), role)['checks']['trusted']
    # b. prefers C on targets but C loses every guard pair -> guard fails
    g_lose = [flip(x['cand_side']) if role[x['id']][0] == 'guard' and x['cand'] == 'C' else p for x, p in zip(it, prefer_c)]
    r = score(it, fmt(g_lose), role)
    assert not r['passes'] and not r['checks']['guard_losses<=wins+2'], r['checks']
    # c. "not her" on 3 target C clips -> fails, and those pairs are losses
    ks = [k for k, x in enumerate(it, 1) if x['kind'] == 'test' and role[x['id']][0] == 'target'][:3]
    r = score(it, fmt(prefer_c, {k: 'n' + it[k - 1]['cand_side'].lower() for k in ks}), role)
    assert r['not_her_target_C'] == 3 and not r['passes'] and r['target']['losses'] == 3, r
    # d. 10-6 on targets is NOT enough (the 2a bar would have passed it); 12-4 is
    tk = [k for k, x in enumerate(it, 1) if x['kind'] == 'test' and role[x['id']][0] == 'target']
    for n_lose, ok in ((6, False), (4, True)):
        lose = set(tk[:n_lose])
        picks = [flip(x['cand_side']) if k in lose else p for k, (x, p) in enumerate(zip(it, prefer_c), 1)]
        rep = {x['repeat_of'] + 1: k for k, x in enumerate(it, 1) if x['kind'] == 'repeat'}
        for src, k in rep.items():                     # keep the rater consistent on repeats
            picks[k - 1] = it[k - 1]['cand_side'] if picks[src - 1] == it[src - 1]['cand_side'] else flip(it[k - 1]['cand_side'])
        assert score(it, fmt(picks), role)['checks']['sign_p<=0.05'] is ok, n_lose
    # e. MUTANT: C-preferring answers scored against a WRONG key must not pass
    assert not score(build_items(ids, seed=999), fmt(prefer_c), role)['passes']
    # f. a looping C clip is a loss even when picked
    k0 = tk[0]; x0 = it[k0 - 1]
    scr = {'rows': [{'id': x0['id'], 'arm': 'C', 'draw': x0['draw'], 'loop_flag': True}], 'verdict': {'pass': True}}
    assert score(it, fmt(prefer_c), role, scr)['target']['losses'] == 1
    # g. screens fail -> no pass
    assert not score(it, fmt(prefer_c), role, {'rows': [], 'verdict': {'pass': False}})['passes']
    # h. too much is reported, never a gate
    r = score(it, fmt(prefer_c, {k: 'm' + it[k - 1]['cand_side'].lower() for k in tk[:5]}), role)
    assert r['too_much_C'] == 5 and r['passes']
    # Stage 3
    assert score3(8, parse3('\n'.join(f'{k} F' for k in range(1, 9))))['passes']
    assert not score3(8, parse3('\n'.join(f'{k} F' + (' x' if k == 3 else '') for k in range(1, 9))))['passes']
    assert not score3(8, parse3('\n'.join(f'{k} F' + (' n' if k < 3 else '') for k in range(1, 9))))['passes']
    json.dumps(r)
    print('blind_b2 selftest: 2b 9/9, Stage 3 3/3 OK')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['make2b', 'score2b', 'make3', 'score3', 'selftest'])
    ap.add_argument('answers', nargs='?')
    a = ap.parse_args()
    if a.cmd == 'selftest':
        selftest()
    elif a.cmd == 'make2b':
        make2b()
    elif a.cmd == 'make3':
        make3()
    elif a.cmd == 'score2b':
        k = json.load(open(os.path.join(HERE, 'sheet_key_2b.json')))
        scr = json.load(open(os.path.join(HERE, 'screens_b2.json'), encoding='utf-8'))
        r = score(k['items'], parse(open(a.answers).read()), roles(), scr)
        print(json.dumps(r, indent=1)); json.dump(r, open(os.path.join(HERE, 'result_2b.json'), 'w'), indent=1)
    else:
        k = json.load(open(os.path.join(HERE, 'sheet_key_3.json')))
        r = score3(len(k['items']), parse3(open(a.answers).read()))
        print(json.dumps(r, indent=1)); json.dump(r, open(os.path.join(HERE, 'result_3.json'), 'w'), indent=1)
