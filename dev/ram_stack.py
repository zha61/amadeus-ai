#!/usr/bin/env python3
"""ram_stack.py — READ-ONLY memory sampler for the whole Amadeus stack (backlog #172).

Why per-process numbers are not enough (measured 2026-10-04): with gemma4 LOADED (/api/ps),
its llama-server showed RSS 0.29 GB. The weights are mmap'd file pages that Metal uses as GPU
buffers; they are charged to no process. So the budget number is the SYSTEM-WIDE change
(vm_stat wired / file-backed / compressor pages, swap, kern.memorystatus_level) from a state
with no model loaded; per-process RSS and phys_footprint are the breakdown beside it.

Calls ONLY: ps, footprint, vm_stat, sysctl, and GET /api/ps. It never calls a model, never
signals a process, and never writes outside --out.
  NEVER use `memory_pressure` here: run without -S it ALLOCATES memory ("Allocate memory and
  wait forever", its own help text).

Usage: python3 dev/ram_stack.py --out DIR [--ps-every 1] [--fp-every 10] [--max 1800]
                                 [--after-close 120]
Writes DIR/procs.csv (ps, every --ps-every s), DIR/fp.csv and DIR/sys.csv (every --fp-every s).
Stops at --max seconds, --after-close seconds after the Amadeus app exits (once seen),
or when DIR/STOP exists.
"""
import argparse, csv, json, os, re, subprocess, sys, time, urllib.request
from datetime import datetime, timezone

OLLAMA = 'http://127.0.0.1:11434'
MANIFESTS = os.path.expanduser('~/.ollama/models/manifests/registry.ollama.ai/library')
PY_ROLES = (('kurisu_fish_server.py', 'py-fish'), ('http.server', 'py-http'),
            ('kurisu_rag_server.py', 'py-rag'), ('kurisu_whisper_server.py', 'py-whisper'))


def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def run(cmd, timeout=10):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ''


def blob_to_model():
    """sha256 blob prefix -> model name, from the Ollama manifests (read-only)."""
    out = {}
    try:
        for model in os.listdir(MANIFESTS):
            mdir = os.path.join(MANIFESTS, model)
            for tag in os.listdir(mdir):
                with open(os.path.join(mdir, tag)) as f:
                    for layer in json.load(f).get('layers', []):
                        if layer.get('mediaType', '').endswith('.model'):
                            out[layer['digest'].replace('sha256:', '')[:12]] = f'{model}:{tag}'
    except Exception:
        pass
    return out


def discover(blobs):
    """Every stack process, looked up AGAIN each call (pids change when a model reloads)."""
    rows = []
    for line in run(['ps', '-Ao', 'pid=,ppid=,rss=,args=']).splitlines():
        m = re.match(r'\s*(\d+)\s+(\d+)\s+(\d+)\s+(.*)', line)
        if m:
            rows.append((int(m[1]), int(m[2]), int(m[3]), m[4]))
    procs = {}
    mains = [r for r in rows if r[3].split(' ')[0].endswith('/Amadeus.app/Contents/MacOS/Amadeus')]
    tree = {r[0] for r in mains}
    grew = True
    while grew:                                   # all descendants of the app
        grew = False
        for pid, ppid, _, _ in rows:
            if ppid in tree and pid not in tree:
                tree.add(pid); grew = True
    for pid, ppid, rss, args in rows:
        role = None
        if pid in tree:
            role = next((r for key, r in PY_ROLES if key in args), None)
            if role is None:
                helper = re.search(r'Amadeus Helper(?: \((\w+)\))?', args)
                if any(pid == m[0] for m in mains):
                    role = 'electron-main'
                elif helper:
                    role = 'electron-' + (helper[1] or 'helper').lower()
                else:
                    role = 'app-child:' + os.path.basename(args.split(' ')[0])
        elif '/Ollama.app/' in args:
            if 'llama-server' in args:
                b = re.search(r'sha256-([0-9a-f]{12})', args)
                role = 'llama:' + blobs.get(b[1], b[1]) if b else 'llama:?'
            elif args.split(' ')[0].endswith('MacOS/Ollama'):
                role = 'ollama-app'
            else:
                role = 'ollama-serve'
        if role:
            procs[pid] = (role, rss)
    return procs, bool(mains)


def vmstat():
    out = {}
    for line in run(['vm_stat']).splitlines():
        m = re.match(r'(.+?):\s+(\d+)\.', line)
        if m:
            out[m[1].strip('" ')] = int(m[2])
    return out


def sysrow():
    v = vmstat()
    level = run(['sysctl', '-n', 'kern.memorystatus_level']).strip()
    swap = re.search(r'used = ([\d.]+)M', run(['sysctl', '-n', 'vm.swapusage']))
    try:
        with urllib.request.urlopen(OLLAMA + '/api/ps', timeout=2) as r:
            models = '|'.join(m['name'] for m in json.load(r).get('models', []))
    except Exception:
        models = 'ERR'
    return [now(), level, swap[1] if swap else '', v.get('Pages free', ''), v.get('Pages active', ''),
            v.get('Pages inactive', ''), v.get('Pages wired down', ''), v.get('File-backed pages', ''),
            v.get('Anonymous pages', ''), v.get('Pages occupied by compressor', ''),
            v.get('Swapouts', ''), models]


def footprints(procs, tmp):
    """ONE footprint call for all pids (shared memory counted once in the total)."""
    if not procs:
        return [], ''
    cmd = ['footprint', '--noCategories', '-j', tmp]
    for pid in procs:
        cmd += ['-p', str(pid)]
    try:
        os.remove(tmp)
    except FileNotFoundError:
        pass
    run(cmd, timeout=20)
    try:
        with open(tmp) as f:
            d = json.load(f)
    except Exception:
        return [], 'ERR'                           # a pid can exit mid-read: record, continue
    rows = [[p['pid'], procs.get(p['pid'], ('?',))[0], p.get('footprint', ''),
             p.get('auxiliary', {}).get('phys_footprint_peak', '')] for p in d.get('processes', [])]
    return rows, d.get('total footprint', '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--ps-every', type=float, default=1.0)
    ap.add_argument('--fp-every', type=float, default=10.0)
    ap.add_argument('--max', type=float, default=1800)
    ap.add_argument('--after-close', type=float, default=120)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    blobs = blob_to_model()
    files = {n: open(os.path.join(a.out, n), 'a', newline='') for n in ('procs.csv', 'fp.csv', 'sys.csv')}
    w = {n: csv.writer(f) for n, f in files.items()}
    if files['procs.csv'].tell() == 0:
        w['procs.csv'].writerow(['ts', 'pid', 'role', 'rss_kb'])
        w['fp.csv'].writerow(['ts', 'pid', 'role', 'phys_footprint_b', 'phys_footprint_peak_b', 'total_footprint_b'])
        w['sys.csv'].writerow(['ts', 'free_pct', 'swap_used_mb', 'free', 'active', 'inactive', 'wired',
                               'file_backed', 'anonymous', 'compressor', 'swapouts', 'models'])
    print(f'[ram_stack] {now()} start; out={a.out}; blobs={blobs}', flush=True)
    t0, next_fp, seen_app, gone_at = time.time(), 0.0, False, None
    while True:
        t = time.time() - t0
        if t > a.max or os.path.exists(os.path.join(a.out, 'STOP')):
            break
        procs, app_up = discover(blobs)
        seen_app |= app_up
        if seen_app and not app_up:
            gone_at = gone_at or time.time()
            if time.time() - gone_at > a.after_close:
                break
        else:
            gone_at = None
        ts = now()
        for pid, (role, rss) in procs.items():
            w['procs.csv'].writerow([ts, pid, role, rss])
        if t >= next_fp:
            next_fp = t + a.fp_every
            w['sys.csv'].writerow(sysrow())
            rows, total = footprints(procs, os.path.join(a.out, '.fp.json'))
            for r in rows:
                w['fp.csv'].writerow([ts] + r + [total])
            if not rows:
                w['fp.csv'].writerow([ts, '', 'NONE' if not procs else 'ERR', '', '', total])
        for f in files.values():
            f.flush()
        time.sleep(max(0.0, a.ps_every - (time.time() - t0 - t)))
    print(f'[ram_stack] {now()} stop after {time.time() - t0:.0f}s (app seen: {seen_app})', flush=True)


if __name__ == '__main__':
    sys.exit(main())
