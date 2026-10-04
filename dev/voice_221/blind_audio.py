#!/usr/bin/env python3
"""#221 Step 5/6 — blind AUDIO A/B sheet for Zani, and its scorer (PREREG_221, dev/blind_ab.py pattern).

  make   : 16 lines x (A vs B, A vs C) + 5 flipped repeats + 4 A vs A' = 41 items, seed 221.
           Clips are COPIED to opaque names (itemNN_l/r.mp3) next to an HTML page in the
           git-ignored dev/voice_test/221/sheet/. The page holds no arm label; the key is
           sheet_key.json here. Do not show him the key.
  score  : ANSWERS.txt, one line per item: "<n> <A|B|=> [xA] [xB]"  (xA/xB = that clip is broken)
  --selftest : simulated raters + a wrong-key mutant (no files needed).
"""
import argparse, json, os, random, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SHEET_DIR = os.path.join(os.path.dirname(HERE), 'voice_test', '221', 'sheet')
KEY = os.path.join(HERE, 'sheet_key.json')


def build_items(lines, seed=221, n_repeat=5):
    """Pure: returns the shuffled item list (no files). cand_side = 'A' or 'B' on the sheet."""
    rng = random.Random(seed)
    items = []
    for ln in lines:
        for cand in ('B', 'C'):
            items.append({'id': ln['id'], 'emotion': ln['emotion'], 'cand': cand,
                          'cand_side': 'A' if rng.random() < 0.5 else 'B', 'kind': 'test', 'repeat_of': None})
    for i in rng.sample(range(len(items)), n_repeat):
        o = items[i]
        items.append({**o, 'cand_side': 'B' if o['cand_side'] == 'A' else 'A', 'kind': 'repeat', 'repeat_of': i})
    for ln in lines:
        if ln['id'] in ('t1', 't2', 'f1', 'f2'):
            items.append({'id': ln['id'], 'emotion': ln['emotion'], 'cand': "A'",
                          'cand_side': 'A' if rng.random() < 0.5 else 'B', 'kind': 'noise', 'repeat_of': None})
    order = list(range(len(items)))
    rng.shuffle(order)
    pos = {o: k for k, o in enumerate(order)}
    out = [dict(items[i]) for i in order]
    for it in out:
        if it['repeat_of'] is not None:
            it['repeat_of'] = pos[it['repeat_of']]      # index in the SHUFFLED list
    return out


def parse_answers(text):
    ans = {}
    for line in text.splitlines():
        tok = line.split()
        if len(tok) >= 2 and tok[0].isdigit() and tok[1].upper() in ('A', 'B', '='):
            ans[int(tok[0])] = {'pick': tok[1].upper(), 'broken': {t[1].upper() for t in tok[2:] if t.lower() in ('xa', 'xb')}}
    return ans


def verdict(item, a):
    """'cand' | 'base' | 'tie' for one answered item. A broken candidate clip = loss (PREREG)."""
    if item['cand_side'] in a['broken']:
        return 'base'
    if a['pick'] == '=':
        return 'tie'
    return 'cand' if a['pick'] == item['cand_side'] else 'base'


def score(items, ans, screens=None):
    from scipy.stats import binomtest
    missing = [k for k in range(1, len(items) + 1) if k not in ans]
    if missing:
        raise SystemExit(f'STOP: no answer for items {missing}')
    res = {}
    for arm in ('B', 'C'):
        per = {'all': [0, 0, 0], 'tsundere': [0, 0, 0], 'flustered': [0, 0, 0]}   # wins, losses, ties
        for k, it in enumerate(items, 1):
            if it['kind'] != 'test' or it['cand'] != arm:
                continue
            v = verdict(it, ans[k])
            j = {'cand': 0, 'base': 1, 'tie': 2}[v]
            per['all'][j] += 1
            per[it['emotion']][j] += 1
        w, l, t = per['all']
        p = binomtest(w, w + l, 0.5, alternative='greater').pvalue if w + l else 1.0
        res[arm] = {'wins': w, 'losses': l, 'ties': t, 'p_one_sided': round(float(p), 4),
                    'by_emotion': {e: dict(zip(('wins', 'losses', 'ties'), per[e])) for e in ('tsundere', 'flustered')}}
    agree = total = 0
    for k, it in enumerate(items, 1):
        if it['kind'] == 'repeat':
            total += 1
            agree += verdict(it, ans[k]) == verdict(items[it['repeat_of']], ans[it['repeat_of'] + 1])
    noise = [verdict(it, ans[k]) for k, it in enumerate(items, 1) if it['kind'] == 'noise']
    broken = [{'item': k, 'clip': ('cand ' + it['cand']) if s == it['cand_side'] else 'A'}
              for k, it in enumerate(items, 1) for s in ans[k]['broken']]
    for arm, r in res.items():
        screen_ok = True if screens is None else screens['verdict'].get(arm, {}).get('pass', False)
        r['passes'] = bool(r['p_one_sided'] <= 0.10 and r['wins'] >= 8 and agree >= 4 and screen_ok)
        r['screens_pass'] = screen_ok
    return {'arms': res, 'consistency': f'{agree}/{total}', 'noise_non_tie': f'{sum(v != "tie" for v in noise)}/{len(noise)}',
            'broken': broken}


HTML_HEAD = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kurisu Voice Sheet</title><style>
:root{--bg:#fbfaf8;--fg:#1d1b19;--mute:#6b645d;--card:#fff;--line:#e4dfd8;--acc:#b23a2e}
@media (prefers-color-scheme:dark){:root{--bg:#141212;--fg:#ece8e3;--mute:#a39b92;--card:#1d1a19;--line:#35302c;--acc:#e8665a}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0;padding:16px}
main{max-width:760px;margin:auto}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.ctx{color:var(--mute);font-size:14px}.jp{font-size:15px;margin:4px 0 10px}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:6px 0}
audio{width:260px;max-width:100%}label{white-space:nowrap}.n{font-weight:700;color:var(--acc)}
textarea{width:100%;height:160px;background:var(--card);color:var(--fg);border:1px solid var(--line)}
button{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:8px 14px;font-size:15px;margin-right:8px}
#prog{position:sticky;top:0;background:var(--bg);padding:6px 0;font-weight:600}</style></head><body><main>
<h1>Which one do you want her to sound like here?</h1>
<p>Each item plays the same Japanese line twice, <b>A</b> and <b>B</b>. The words are the same. Judge the voice.
Pick <b>A</b>, <b>B</b>, or <b>=</b> (no difference). Tick <b>broken</b> under a clip if it has English words, a glitch,
or dead air. Some items appear twice on purpose. Your answers save in this page, so you can stop and come back.</p>
<div id="prog"></div>
"""

HTML_TAIL = """
<div class="card"><button onclick="out()">Show my answers</button><button onclick="dl()">Download answers.txt</button>
<p class="ctx">Then paste the text in the chat, or send the file.</p><textarea id="ans" readonly></textarea></div>
</main><script>
const N=__N__, KEY='kurisu221_answers';
function get(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
function put(s){try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}
// STATE is the source of truth; storage only keeps a copy (it can be blocked, e.g. a private window).
let STATE={};
function save(){const s={};for(let i=1;i<=N;i++){const p=document.querySelector(`input[name=p${i}]:checked`);
 s[i]={p:p?p.value:null,xa:document.getElementById('xa'+i).checked,xb:document.getElementById('xb'+i).checked}}STATE=s;put(s);prog(s)}
function prog(s){let d=0;for(let i=1;i<=N;i++) if(s[i]&&s[i].p) d++;document.getElementById('prog').textContent=`${d} / ${N} answered`}
function text(){const s=STATE;let t='';for(let i=1;i<=N;i++){const a=s[i]||{};t+=`${i} ${a.p||'?'}${a.xa?' xA':''}${a.xb?' xB':''}\\n`}return t}
function out(){document.getElementById('ans').value=text()}
function dl(){const b=new Blob([text()],{type:'text/plain'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='answers.txt';a.click()}
(function(){const s=get();STATE=s;for(let i=1;i<=N;i++){const a=s[i];if(!a)continue;if(a.p){const r=document.querySelector(`input[name=p${i}][value="${a.p}"]`);if(r)r.checked=true}
 document.getElementById('xa'+i).checked=!!a.xa;document.getElementById('xb'+i).checked=!!a.xb}prog(s)
 document.querySelectorAll('input').forEach(e=>e.addEventListener('change',save))})()
</script></body></html>"""


def make():
    lines = json.load(open(os.path.join(HERE, 'lines.json'), encoding='utf-8'))['lines']
    clips = {(c['id'], c['arm']): c for c in json.load(open(os.path.join(HERE, 'clips.json'), encoding='utf-8'))}
    by_id = {l['id']: l for l in lines}
    items = build_items(lines)
    if os.path.exists(SHEET_DIR):
        shutil.rmtree(SHEET_DIR)
    os.makedirs(SHEET_DIR)
    html = [HTML_HEAD]
    for k, it in enumerate(items, 1):
        cand_file = os.path.join(HERE, clips[(it['id'], it['cand'])]['file'])
        base_file = os.path.join(HERE, clips[(it['id'], 'A')]['file'])
        left, right = (cand_file, base_file) if it['cand_side'] == 'A' else (base_file, cand_file)
        shutil.copyfile(left, os.path.join(SHEET_DIR, f'item{k:02d}_l.mp3'))
        shutil.copyfile(right, os.path.join(SHEET_DIR, f'item{k:02d}_r.mp3'))
        ln = by_id[it['id']]
        esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;')
        html.append(f'<div class="card"><div><span class="n">{k}.</span> <span class="ctx">{esc(ln["context"])}</span></div>'
                    f'<div class="jp">{esc(ln["jp"])}</div>'
                    f'<div class="row"><b>A</b><audio controls preload="none" src="item{k:02d}_l.mp3"></audio>'
                    f'<label><input type="checkbox" id="xa{k}"> broken</label></div>'
                    f'<div class="row"><b>B</b><audio controls preload="none" src="item{k:02d}_r.mp3"></audio>'
                    f'<label><input type="checkbox" id="xb{k}"> broken</label></div>'
                    f'<div class="row">' + ''.join(f'<label><input type="radio" name="p{k}" value="{v}"> {v}</label>' for v in ('A', 'B', '='))
                    + '</div></div>')
    html.append(HTML_TAIL.replace('__N__', str(len(items))))
    open(os.path.join(SHEET_DIR, 'index.html'), 'w', encoding='utf-8').write('\n'.join(html))
    json.dump({'seed': 221, 'items': items}, open(KEY, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'wrote {SHEET_DIR}/index.html ({len(items)} items) and {KEY}')


def selftest():
    lines = [{'id': f'{p}{i}', 'emotion': e} for p, e in (('t', 'tsundere'), ('f', 'flustered')) for i in range(1, 9)]
    items = build_items(lines)
    assert len(items) == 41 and sum(i['kind'] == 'repeat' for i in items) == 5 and sum(i['kind'] == 'noise' for i in items) == 4
    for it in items:
        if it['kind'] == 'repeat':
            o = items[it['repeat_of']]
            assert (o['id'], o['cand']) == (it['id'], it['cand']) and o['cand_side'] != it['cand_side']
    fmt = lambda picks: parse_answers('\n'.join(f'{k} {p}' for k, p in enumerate(picks, 1)))
    # 1. always-A rater: flipped repeats must disagree -> 0/5
    r = score(items, fmt(['A'] * 41))
    assert r['consistency'] == '0/5', r['consistency']
    assert not any(a['passes'] for a in r['arms'].values())
    # 2. true preference for C (and for A over B): C passes, B does not, consistency 5/5
    pick = lambda it: it['cand_side'] if it['cand'] == 'C' else ('B' if it['cand_side'] == 'A' else 'A')
    r = score(items, fmt([pick(it) for it in items]))
    assert r['arms']['C']['wins'] == 16 and r['arms']['C']['passes'], r
    assert r['arms']['B']['losses'] == 16 and not r['arms']['B']['passes']
    assert r['consistency'] == '5/5'
    json.dumps(r)                       # score() output is written as JSON by the real path
    # 3. broken candidate clip counts as a loss even when picked
    a = fmt([pick(it) for it in items])
    k = next(k for k, it in enumerate(items, 1) if it['kind'] == 'test' and it['cand'] == 'C')
    a[k]['broken'] = {items[k - 1]['cand_side']}
    assert score(items, a)['arms']['C']['wins'] == 15
    # 4. MUTANT: the same C-preferring answers scored against a WRONG key must not pass
    wrong = build_items(lines, seed=999)
    r = score(wrong, fmt([pick(it) for it in items]))
    assert not r['arms']['C']['passes'], r['arms']['C']
    # 5. missing answer stops
    try:
        score(items, fmt(['A'] * 40)); raise AssertionError('missing answer not caught')
    except SystemExit:
        pass
    print('blind_audio selftest: 5/5 OK')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['make', 'score', 'selftest'])
    ap.add_argument('answers', nargs='?')
    a = ap.parse_args()
    if a.cmd == 'selftest':
        selftest()
    elif a.cmd == 'make':
        make()
    else:
        items = json.load(open(KEY, encoding='utf-8'))['items']
        screens = json.load(open(os.path.join(HERE, 'screens.json'), encoding='utf-8'))
        r = score(items, parse_answers(open(a.answers, encoding='utf-8').read()), screens)
        print(json.dumps(r, indent=1))
        json.dump(r, open(os.path.join(HERE, 'result.json'), 'w'), indent=1)
