#!/usr/bin/env python3
"""#221b sheets for Zani and their scorers (PREREG_221b.md).

  make1              Stage 1: the 16 shipped A clips (#221) + 2 repeats, seed 2210. right / too calm / too much.
  score1 ANSWERS     "<n> <R|C|M>" per line (R = right, C = too calm, M = too much).
  make2a             Stage 2a: 32 test pairs + 4 flipped repeats + 4 A1-vs-A2 noise = 40 items, seed 2211.
                     Every copy is level-matched to the median A loudness (PREREG). No arm label on the page.
  score2a ANSWERS    "<n> <A|B|=> [xA] [xB] [nA] [nB]"  (x = broken, n = not her; A/B = the side on the sheet)
  selftest           simulated raters + wrong-key mutants; no audio files needed.
Sheets go to the git-ignored dev/voice_test/221b/. Open index.html in a NORMAL browser (the app's preview
pane cannot play the MP3s). The keys (sheet_key_*.json) stay here — do not show them to him.
"""
import argparse, json, os, random, shutil, statistics, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
V221 = os.path.join(os.path.dirname(HERE), 'voice_221')
ROOT = os.path.join(os.path.dirname(HERE), 'voice_test', '221b')
PILOT = ['t1', 't3', 't5', 't7', 'f1', 'f3', 'f5', 'f7']
NOISE = ['t1', 't5', 'f1', 'f5']
esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;')

# ───────────────────────── Stage 1 ─────────────────────────
def build_items1(ids, seed=2210, n_repeat=2):
    rng = random.Random(seed)
    items = [{'id': i, 'repeat_of': None} for i in ids]
    for k in rng.sample(range(len(items)), n_repeat):
        items.append({'id': items[k]['id'], 'repeat_of': k})
    order = list(range(len(items)))
    rng.shuffle(order)
    pos = {o: n for n, o in enumerate(order)}
    out = [dict(items[i]) for i in order]
    for it in out:
        if it['repeat_of'] is not None:
            it['repeat_of'] = pos[it['repeat_of']]
    return out


def parse1(text):
    ans = {}
    for line in text.splitlines():
        t = line.split()
        if len(t) >= 2 and t[0].isdigit() and t[1].upper() in ('R', 'C', 'M'):
            ans[int(t[0])] = t[1].upper()
    return ans


def score1(items, emo, ans):
    missing = [k for k in range(1, len(items) + 1) if k not in ans]
    if missing:
        raise SystemExit(f'STOP: no answer for items {missing}')
    per = {'tsundere': {'R': 0, 'C': 0, 'M': 0}, 'flustered': {'R': 0, 'C': 0, 'M': 0}}
    agree = total = 0
    for k, it in enumerate(items, 1):
        if it['repeat_of'] is None:
            per[emo[it['id']]][ans[k]] += 1
        else:
            total += 1
            agree += ans[k] == ans[it['repeat_of'] + 1]
    return {'per_emotion': per, 'needs_fix': {e: v['C'] >= 4 for e, v in per.items()},
            'repeat_agreement': f'{agree}/{total}'}


# ───────────────────────── Stage 2a ─────────────────────────
def build_items2a(seed=2211, n_repeat=4):
    rng = random.Random(seed)
    items = []
    for i in PILOT:
        for cand, draw in (('M', 1), ('M', 2), ('MV', 1), ('MV', 2)):
            items.append({'id': i, 'cand': cand, 'draw': draw, 'base_draw': draw,
                          'cand_side': 'A' if rng.random() < 0.5 else 'B', 'kind': 'test', 'repeat_of': None})
    for k in rng.sample(range(len(items)), n_repeat):
        o = items[k]
        items.append({**o, 'cand_side': 'B' if o['cand_side'] == 'A' else 'A', 'kind': 'repeat', 'repeat_of': k})
    for i in NOISE:                 # A2 plays the "candidate" role, A1 the base
        items.append({'id': i, 'cand': 'A', 'draw': 2, 'base_draw': 1,
                      'cand_side': 'A' if rng.random() < 0.5 else 'B', 'kind': 'noise', 'repeat_of': None})
    order = list(range(len(items)))
    rng.shuffle(order)
    pos = {o: n for n, o in enumerate(order)}
    out = [dict(items[i]) for i in order]
    for it in out:
        if it['repeat_of'] is not None:
            it['repeat_of'] = pos[it['repeat_of']]
    return out


def parse2a(text):
    ans = {}
    for line in text.splitlines():
        t = line.split()
        if len(t) >= 2 and t[0].isdigit() and t[1].upper() in ('A', 'B', '='):
            flags = {x.lower() for x in t[2:]}
            ans[int(t[0])] = {'pick': t[1].upper(),
                              'broken': {s for s in 'AB' if f'x{s.lower()}' in flags},
                              'nother': {s for s in 'AB' if f'n{s.lower()}' in flags}}
    return ans


def verdict2a(it, a, loops=frozenset()):
    """'cand' | 'base' | 'tie'. A broken / not-her / looping CANDIDATE clip = loss (PREREG)."""
    if it['cand_side'] in a['broken'] or it['cand_side'] in a['nother'] or (it['id'], it['cand'], it['draw']) in loops:
        return 'base'
    if a['pick'] == '=':
        return 'tie'
    return 'cand' if a['pick'] == it['cand_side'] else 'base'


def score2a(items, ans, screens=None):
    missing = [k for k in range(1, len(items) + 1) if k not in ans]
    if missing:
        raise SystemExit(f'STOP: no answer for items {missing}')
    loops = set()
    if screens:
        loops = {(r['id'], r['arm'], r['draw']) for r in screens['rows'] if r['loop_flag']}
    res = {}
    for arm in ('M', 'MV'):
        w = l = t = 0
        net, emo = {}, {'t': [0, 0, 0], 'f': [0, 0, 0]}
        nother = set()
        for k, it in enumerate(items, 1):
            side_of = lambda s: (it['id'], it['cand'], it['draw']) if s == it['cand_side'] else (it['id'], 'A', it['base_draw'])
            for s in ans[k]['nother']:
                if side_of(s)[1] == arm:
                    nother.add(side_of(s))
            if it['kind'] != 'test' or it['cand'] != arm:
                continue
            v = verdict2a(it, ans[k], loops)
            j = {'cand': 0, 'base': 1, 'tie': 2}[v]
            w, l, t = w + (j == 0), l + (j == 1), t + (j == 2)
            emo[it['id'][0]][j] += 1
            net[it['id']] = net.get(it['id'], 0) + (1 if j == 0 else -1 if j == 1 else 0)
        pos_, neg_ = sum(v > 0 for v in net.values()), sum(v < 0 for v in net.values())
        screen_ok = True if screens is None else screens['verdict'][arm]['pass']
        res[arm] = {'wins': w, 'losses': l, 'ties': t, 'lines_net_pos': pos_, 'lines_net_neg': neg_,
                    'not_her_clips': len(nother), 'screens_pass': screen_ok,
                    'tsundere': dict(zip(('wins', 'losses', 'ties'), emo['t'])),
                    'flustered': dict(zip(('wins', 'losses', 'ties'), emo['f']))}
        res[arm]['advances'] = bool(w >= l + 4 and pos_ >= neg_ + 2 and len(nother) <= 2 and screen_ok)
    agree = total = 0
    for k, it in enumerate(items, 1):
        if it['kind'] == 'repeat':
            total += 1
            agree += verdict2a(it, ans[k], loops) == verdict2a(items[it['repeat_of']], ans[it['repeat_of'] + 1], loops)
    trusted = agree >= 3
    noise = [verdict2a(it, ans[k]) for k, it in enumerate(items, 1) if it['kind'] == 'noise']
    adv = [a for a in ('M', 'MV') if res[a]['advances']] if trusted else []
    if len(adv) == 2:
        nets = {a: res[a]['wins'] - res[a]['losses'] for a in adv}
        adv = ['M'] if nets['M'] >= nets['MV'] else ['MV']
    return {'arms': res, 'consistency': f'{agree}/{total}', 'trusted': trusted,
            'noise_non_tie': f'{sum(v != "tie" for v in noise)}/{len(noise)}',
            'advance': adv[0] if adv else None}


# ───────────────────────── HTML ─────────────────────────
CSS = """:root{--bg:#fbfaf8;--fg:#1d1b19;--mute:#6b645d;--card:#fff;--line:#e4dfd8;--acc:#b23a2e}
@media (prefers-color-scheme:dark){:root{--bg:#141212;--fg:#ece8e3;--mute:#a39b92;--card:#1d1a19;--line:#35302c;--acc:#e8665a}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0;padding:16px}
main{max-width:760px;margin:auto}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.ctx{color:var(--mute);font-size:14px}.jp{font-size:15px;margin:4px 0 10px}.row{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:6px 0}
audio{width:260px;max-width:100%}label{white-space:nowrap}.n{font-weight:700;color:var(--acc)}
textarea{width:100%;height:160px;background:var(--card);color:var(--fg);border:1px solid var(--line)}
button{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:8px 14px;font-size:15px;margin-right:8px}
#prog{position:sticky;top:0;background:var(--bg);padding:6px 0;font-weight:600}"""

JS = """<script>
const N=__N__, KEY='__KEY__', RADIO=__RADIO__, BOXES=__BOXES__;
function get(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
function put(s){try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}
// STATE is the source of truth; storage only keeps a copy (it can be blocked, e.g. a private window).
let STATE={};
function save(){const s={};for(let i=1;i<=N;i++){const p=document.querySelector(`input[name=p${i}]:checked`);const a={p:p?p.value:null};
 for(const b of BOXES){a[b]=document.getElementById(b+i).checked}s[i]=a}STATE=s;put(s);prog(s)}
function prog(s){let d=0;for(let i=1;i<=N;i++) if(s[i]&&s[i].p) d++;document.getElementById('prog').textContent=`${d} / ${N} answered`}
function text(){let t='';for(let i=1;i<=N;i++){const a=STATE[i]||{};t+=`${i} ${a.p||'?'}`;for(const b of BOXES) if(a[b]) t+=' '+b;t+='\\n'}return t}
function out(){document.getElementById('ans').value=text()}
function dl(){const b=new Blob([text()],{type:'text/plain'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='answers.txt';a.click()}
(function(){const s=get();STATE=s;for(let i=1;i<=N;i++){const a=s[i];if(!a)continue;if(a.p){const r=document.querySelector(`input[name=p${i}][value="${a.p}"]`);if(r)r.checked=true}
 for(const b of BOXES) document.getElementById(b+i).checked=!!a[b]}prog(s)
 document.querySelectorAll('input').forEach(e=>e.addEventListener('change',save))})()
</script>"""

TAIL = """<div class="card"><button onclick="out()">Show my answers</button><button onclick="dl()">Download answers.txt</button>
<p class="ctx">Then paste the text in the chat, or send the file.</p><textarea id="ans" readonly></textarea></div></main>"""


def page(title, intro, cards, n, key, radio, boxes):
    js = JS.replace('__N__', str(n)).replace('__KEY__', key).replace('__RADIO__', json.dumps(radio)).replace('__BOXES__', json.dumps(boxes))
    return (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{CSS}</style></head><body><main>{intro}<div id="prog"></div>'
            + '\n'.join(cards) + TAIL + js + '</body></html>')


def lines_by_id():
    return {l['id']: l for l in json.load(open(os.path.join(V221, 'lines.json'), encoding='utf-8'))['lines']}


def make1():
    L = lines_by_id()
    clips = {c['id']: c for c in json.load(open(os.path.join(V221, 'clips.json'), encoding='utf-8')) if c['arm'] == 'A'}
    ids = list(L)                                   # t1..t8, f1..f8 (lines.json order)
    items = build_items1(ids)
    d = os.path.join(ROOT, 'stage1')
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    cards = []
    for k, it in enumerate(items, 1):
        shutil.copyfile(os.path.join(V221, clips[it['id']]['file']), os.path.join(d, f'clip{k:02d}.mp3'))
        ln = L[it['id']]
        cards.append(f'<div class="card"><div><span class="n">{k}.</span> <span class="ctx">She says: “{esc(ln["en"])}”</span></div>'
                     f'<div class="jp">{esc(ln["jp"])}</div><div class="row"><audio controls preload="none" src="clip{k:02d}.mp3"></audio></div>'
                     '<div class="row">' + ''.join(f'<label><input type="radio" name="p{k}" value="{v}"> {t}</label>'
                     for v, t in (('R', 'right'), ('C', 'too calm'), ('M', 'too much'))) + '</div></div>')
    intro = ('<h1>Does she sound right here?</h1><p>Each clip is her voice for one reply. The English line is what she means. '
             'For each clip pick <b>right</b>, <b>too calm</b> (not flustered / defensive enough), or <b>too much</b>. '
             'Two clips appear twice on purpose. Your answers save in this page.</p>')
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
        page('Kurisu Voice Check', intro, cards, len(items), 'kurisu221b_s1', 'p', []))
    json.dump({'seed': 2210, 'items': items, 'emotion': {i: L[i]['emotion'] for i in ids}},
              open(os.path.join(HERE, 'sheet_key_1.json'), 'w'), indent=1)
    print(f'wrote {d}/index.html ({len(items)} items)')


def lufs(path):
    err = subprocess.run(['ffmpeg', '-i', path, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float([l for l in err.splitlines() if 'I:' in l and 'LUFS' in l][-1].split()[1])


def level_copy(src, dst, target):
    """Gain-only copy to `target` LUFS, re-encoded at 128k (every clip, A included, so the codec path is equal)."""
    gain = target - lufs(src)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', f'volume={gain:.2f}dB', '-b:a', '128k', dst], check=True)
    peak = subprocess.run(['ffmpeg', '-i', dst, '-af', 'astats=measure_overall=Peak_level:measure_perchannel=none',
                           '-f', 'null', '-'], capture_output=True, text=True).stderr
    pk = [float(l.split()[-1]) for l in peak.splitlines() if 'Peak level dB' in l]
    return round(gain, 2), (pk[-1] if pk else None)


def make2a():
    L = lines_by_id()
    screens = json.load(open(os.path.join(HERE, 'screens_b.json'), encoding='utf-8'))
    target = screens['summary']['A']['median_lufs']
    files = {(c['id'], c['arm'], c['draw']): os.path.join(HERE, c['file'])
             for c in json.load(open(os.path.join(HERE, 'clips_b.json'), encoding='utf-8'))}
    items = build_items2a()
    d = os.path.join(ROOT, 'sheet2a')
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    cards, gains = [], []
    for k, it in enumerate(items, 1):
        cand = files[(it['id'], it['cand'], it['draw'])]
        base = files[(it['id'], 'A', it['base_draw'])]
        left, right = (cand, base) if it['cand_side'] == 'A' else (base, cand)
        for side, src in (('l', left), ('r', right)):
            g, pk = level_copy(src, os.path.join(d, f'item{k:02d}_{side}.mp3'), target)
            gains.append({'item': k, 'side': side, 'gain_db': g, 'peak_dbfs': pk})
        ln = L[it['id']]
        box = lambda s, k: (f'<label><input type="checkbox" id="x{s}{k}"> broken</label>'
                            f'<label><input type="checkbox" id="n{s}{k}"> not her</label>')
        cards.append(f'<div class="card"><div><span class="n">{k}.</span> <span class="ctx">She says: “{esc(ln["en"])}”</span></div>'
                     f'<div class="jp">{esc(ln["jp"])}</div>'
                     f'<div class="row"><b>A</b><audio controls preload="none" src="item{k:02d}_l.mp3"></audio>{box("a", k)}</div>'
                     f'<div class="row"><b>B</b><audio controls preload="none" src="item{k:02d}_r.mp3"></audio>{box("b", k)}</div>'
                     '<div class="row">' + ''.join(f'<label><input type="radio" name="p{k}" value="{v}"> {v}</label>' for v in ('A', 'B', '='))
                     + '</div></div>')
    intro = ('<h1>Which one do you want her to sound like here?</h1><p>Each item plays the same Japanese line twice, <b>A</b> and '
             '<b>B</b>. Judge the voice. Pick <b>A</b>, <b>B</b>, or <b>=</b> (no difference). Under a clip, tick <b>broken</b> '
             '(English words, glitch, dead air) or <b>not her</b> (does not sound like Kurisu). The volume is evened out on '
             'purpose. Some items appear twice. Your answers save in this page.</p>')
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
        page('Kurisu Voice Sheet 2', intro, cards, len(items), 'kurisu221b_s2a', 'p', ['xa', 'xb', 'na', 'nb']))
    json.dump({'seed': 2211, 'target_lufs': target, 'items': items, 'gains': gains},
              open(os.path.join(HERE, 'sheet_key_2a.json'), 'w'), indent=1)
    hot = [g for g in gains if g['peak_dbfs'] is not None and g['peak_dbfs'] > -0.3]
    print(f'wrote {d}/index.html ({len(items)} items), target {target} LUFS; clips near clipping: {len(hot)}')


# ───────────────────────── selftest ─────────────────────────
def selftest():
    # Stage 1
    ids = [f't{i}' for i in range(1, 9)] + [f'f{i}' for i in range(1, 9)]
    emo = {i: 'tsundere' if i[0] == 't' else 'flustered' for i in ids}
    it1 = build_items1(ids)
    assert len(it1) == 18 and sum(i['repeat_of'] is not None for i in it1) == 2
    ans = parse1('\n'.join(f'{k} {"C" if it["id"][0] == "t" else "R"}' for k, it in enumerate(it1, 1)))
    r = score1(it1, emo, ans)
    assert r['needs_fix'] == {'tsundere': True, 'flustered': False} and r['repeat_agreement'] == '2/2', r
    try:
        score1(it1, emo, {k: v for k, v in ans.items() if k != 3}); raise AssertionError('missing not caught')
    except SystemExit:
        pass
    # Stage 2a
    it = build_items2a()
    assert len(it) == 40 and sum(i['kind'] == 'test' for i in it) == 32 and sum(i['kind'] == 'noise' for i in it) == 4
    for x in it:
        if x['kind'] == 'repeat':
            o = it[x['repeat_of']]
            assert (o['id'], o['cand'], o['draw']) == (x['id'], x['cand'], x['draw']) and o['cand_side'] != x['cand_side']
    fmt = lambda picks, extra=None: parse2a('\n'.join(f'{k} {p}' + ((' ' + extra[k]) if extra and k in extra else '')
                                                      for k, p in enumerate(picks, 1)))
    flip = lambda s: 'B' if s == 'A' else 'A'
    # a. always-A rater -> repeats disagree -> untrusted, nothing advances
    r = score2a(it, fmt(['A'] * 40))
    assert r['consistency'] == '0/4' and not r['trusted'] and r['advance'] is None, r
    # b. true preference for M, against MV -> M advances, MV does not
    pick = [x['cand_side'] if x['cand'] == 'M' else flip(x['cand_side']) for x in it]
    r = score2a(it, fmt(pick))
    assert r['arms']['M']['wins'] == 16 and r['arms']['M']['advances'] and not r['arms']['MV']['advances'] and r['advance'] == 'M', r
    assert r['consistency'] == '4/4' and r['arms']['M']['lines_net_pos'] == 8
    # c. "not her" on 3 M clips blocks M even if every pair is won — and those pairs become losses
    ks = [k for k, x in enumerate(it, 1) if x['kind'] == 'test' and x['cand'] == 'M'][:3]
    r = score2a(it, fmt(pick, {k: 'n' + it[k - 1]['cand_side'].lower() for k in ks}))
    assert r['arms']['M']['not_her_clips'] == 3 and not r['arms']['M']['advances'] and r['arms']['M']['losses'] == 3, r['arms']['M']
    # d. a looping candidate clip is a loss even when picked
    k0 = ks[0]; x0 = it[k0 - 1]
    scr = {'rows': [{'id': x0['id'], 'arm': 'M', 'draw': x0['draw'], 'loop_flag': True}],
           'verdict': {'M': {'pass': True}, 'MV': {'pass': True}}}
    assert score2a(it, fmt(pick), scr)['arms']['M']['losses'] >= 1
    # e. MUTANT: the M-preferring answers scored against a WRONG key must not advance M
    r = score2a(build_items2a(seed=999), fmt(pick))
    assert not r['arms']['M']['advances'], r['arms']['M']
    # f. both arms win -> the higher net advances; equal -> M
    both = [x['cand_side'] for x in it]
    r = score2a(it, fmt(both))
    assert r['arms']['M']['advances'] and r['arms']['MV']['advances'] and r['advance'] == 'M'
    json.dumps(r)
    print('blind_b selftest: Stage 1 3/3, Stage 2a 6/6 OK')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['make1', 'score1', 'make2a', 'score2a', 'selftest'])
    ap.add_argument('answers', nargs='?')
    a = ap.parse_args()
    if a.cmd == 'selftest':
        selftest()
    elif a.cmd == 'make1':
        make1()
    elif a.cmd == 'make2a':
        make2a()
    elif a.cmd == 'score1':
        k = json.load(open(os.path.join(HERE, 'sheet_key_1.json')))
        r = score1(k['items'], k['emotion'], parse1(open(a.answers).read()))
        print(json.dumps(r, indent=1)); json.dump(r, open(os.path.join(HERE, 'result_1.json'), 'w'), indent=1)
    else:
        k = json.load(open(os.path.join(HERE, 'sheet_key_2a.json')))
        scr = json.load(open(os.path.join(HERE, 'screens_b.json'), encoding='utf-8'))
        r = score2a(k['items'], parse2a(open(a.answers).read()), scr)
        print(json.dumps(r, indent=1)); json.dump(r, open(os.path.join(HERE, 'result_2a.json'), 'w'), indent=1)
