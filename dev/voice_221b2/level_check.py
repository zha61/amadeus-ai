#!/usr/bin/env python3
"""#221b ship guard — is her voice still at the level and pitch Zani approved? ($0: it reads cached files only.)

Fish's prosody.volume is an undocumented SWITCH (CLAUDE.md 54, bugs.md 99). If Fish changes it, her level jumps by
~12 LU with no error. This compares each NEW greeting file (current GREETING_TTS_VER) with the OLD file of the SAME
greeting at an older version (default v3 = s2-pro, the level the lip sync and BGM ducking are tuned to).

  python3 dev/voice_221b2/level_check.py MANIFEST [--old v3]   MANIFEST = dev/warm_greetings.js --manifest output
  python3 dev/voice_221b2/level_check.py selftest              rules, the key port, and the shipped payload

FAIL (exit 1) if: median level difference new - old is outside +-1.5 LU, or median pitch rise > +4.0 semitones.
Exit 2 = fewer than 8 pairs to judge. The high-pitch count (> +4 st) and per-emotion medians are REPORTED.
"""
import json, math, os, statistics as st, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'data', 'greeting_cache')


def greeting_key(text, emo, ver):
    """Port of amadeus.html greetingCacheKey(): djb2 over UTF-16 code units, base36. Verified in selftest."""
    s = f"{text}|{emo or 'default'}|{ver}"
    units = [int.from_bytes(s.encode('utf-16-le')[i:i + 2], 'little') for i in range(0, len(s.encode('utf-16-le')), 2)]
    h = 5381
    for c in units:
        h = (((h << 5) + h) + c) & 0xFFFFFFFF
    b36 = lambda n: '0' if n == 0 else ''.join(reversed([('0123456789abcdefghijklmnopqrstuvwxyz')[d] for d in _digits(n)]))
    return 'g' + b36(h) + b36(len(units))


def _digits(n):
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(r)
    return out


def decide(pairs):
    """pairs: [{'emo','dlu','dst'}] (new - old). Pure function."""
    if len(pairs) < 8:
        return {'n': len(pairs), 'verdict': 'too few pairs', 'passed': None}
    dlu = st.median(p['dlu'] for p in pairs)
    dst = st.median(p['dst'] for p in pairs if p['dst'] is not None)
    by = {}
    for p in pairs:
        by.setdefault(p['emo'], []).append(p)
    return {'n': len(pairs), 'median_level_diff_lu': round(dlu, 2), 'median_pitch_rise_st': round(dst, 2),
            'high_over_4st': sum(p['dst'] is not None and p['dst'] > 4.0 for p in pairs),
            'per_emotion': {e: {'n': len(v), 'level': round(st.median(x['dlu'] for x in v), 2),
                                'pitch': round(st.median(x['dst'] for x in v if x['dst'] is not None), 2)
                                if any(x['dst'] is not None for x in v) else None} for e, v in by.items()},
            'checks': {'level_within_1.5': abs(dlu) <= 1.5, 'pitch_rise<=4': dst <= 4.0},
            'passed': abs(dlu) <= 1.5 and dst <= 4.0}


def main(manifest, old):
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'voice_221'))
    from common import loudness
    from measure_b2 import median_f0
    m = json.load(open(manifest, encoding='utf-8'))
    pairs = []
    for e in m['entries']:
        new = e['file']
        prev = os.path.join(CACHE, greeting_key(e['text'], e['emo'], old) + '.mp3')
        if not (os.path.exists(new) and os.path.exists(prev)):
            continue
        fn, fo = median_f0(new), median_f0(prev)
        pairs.append({'pool': e['pool'], 'emo': e['emo'], 'dlu': loudness(new) - loudness(prev),
                      'dst': 12 * math.log2(fn / fo) if fn and fo else None})
    r = {'new_ver': m['ver'], 'old_ver': old, **decide(pairs)}
    print(json.dumps(r, indent=1))
    if r['passed'] is None:
        print('level_check: too few pairs to judge (need 8)'); sys.exit(2)
    print('level_check', 'PASSED' if r['passed'] else 'FAILED — stop; do not warm more; revert (PREREG ship plan)')
    sys.exit(0 if r['passed'] else 1)


def selftest():
    # 1. the key port equals the shipped JS function on EVERY real greeting (node runs amadeus.html's own code)
    root = os.path.dirname(os.path.dirname(HERE))
    js = r"""
const fs=require('fs');const html=fs.readFileSync(process.argv[1],'utf8');
const src=html.slice(html.indexOf('function greetingCacheKey'));const body=src.slice(0,src.indexOf('\n}')+2);
function ex(n){const at=html.indexOf('const '+n+'=[');if(at<0)return[];let i=html.indexOf('[',at),d=0,e=-1;
 for(;i<html.length;i++){if(html[i]==='[')d++;else if(html[i]===']'){d--;if(!d){e=i;break}}}
 return eval('('+html.slice(html.indexOf('[',at),e+1)+')')}
const P=['GREETINGS','GREETINGS_MORNING','GREETINGS_AFTERNOON','GREETINGS_EVENING','GREETINGS_NIGHT','GREETINGS_SMALL_HOURS',
'GREETINGS_SHORT_AWAY','GREETINGS_MEDIUM_AWAY','GREETINGS_LONG_AWAY','GREETINGS_BIRTHDAY','GREETINGS_ZANI_BIRTHDAY',
'GREETINGS_ZANI_BIRTHDAY_EVE','GREETINGS_ZANI_BIRTHDAY_AFTER','GREETINGS_INCOMING_CALL'];
const out=[];for(const v of ['v3','v4']){const f=new Function('GREETING_TTS_VER',body+';return greetingCacheKey')(v);
 for(const p of P)for(const [t,e] of ex(p))out.push({t,e,v,k:f(t,e)})}
console.log(JSON.stringify(out))"""
    rows = json.loads(subprocess.run(['node', '-e', js, os.path.join(root, 'amadeus.html')],
                                     capture_output=True, text=True, check=True).stdout)
    assert len(rows) == 176, len(rows)
    bad = [r for r in rows if greeting_key(r['t'], r['e'], r['v']) != r['k']]
    assert not bad, bad[:3]
    v3 = [r for r in rows if r['v'] == 'v3']
    assert all(os.path.exists(os.path.join(CACHE, r['k'] + '.mp3')) for r in v3), 'a v3 greeting file is missing'
    # 2. rules
    mk = lambda dlu, dst, n=10, emo='calm': [{'emo': emo, 'dlu': dlu, 'dst': dst}] * n
    assert decide(mk(-0.4, 2.0))['passed']
    assert not decide(mk(-12.0, 2.0))['passed']                   # the volume switch flipped
    assert not decide(mk(9.0, 2.0))['passed']                     # loud path again
    assert not decide(mk(0.0, 5.0))['passed']                     # pitch way up
    assert decide(mk(0.0, 2.0, n=7))['passed'] is None            # too few to judge
    # 3. the shipped payload equals the Stage 3 request Zani approved (model header, prosody, every other field)
    sys.path.insert(0, HERE)
    from arms_b2 import shipped_request
    P3 = [c for c in json.load(open(os.path.join(HERE, 'clips_b2.json'), encoding='utf-8')) if c['arm'] == 'P']
    V3 = {"format": "mp3", "mp3_bitrate": 128, "latency": "normal", "normalize": True, "chunk_length": 200,
          "temperature": 0.7, "top_p": 0.8, "repetition_penalty": 1.2}
    for c in P3:
        payload, headers = shipped_request(c['text'])
        assert headers['model'] == c['model'] == 's2.1-pro', headers['model']
        assert payload['prosody'] == c['prosody'] == {'volume': -1.0}, payload.get('prosody')
        assert payload['text'] == c['text'] and payload['reference_id'][:8] == c['voice']
        assert {k: v for k, v in payload.items() if k not in ('text', 'prosody', 'reference_id')} == V3
    print(f'level_check selftest OK: key port 176/176, v3 files 88/88, rules 5/5, shipped == Stage 3 request ({len(P3)} clips)')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        selftest()
    elif len(sys.argv) > 1:
        old = sys.argv[sys.argv.index('--old') + 1] if '--old' in sys.argv else 'v3'
        main(sys.argv[1], old)
    else:
        sys.exit(__doc__)
