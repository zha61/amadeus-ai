#!/usr/bin/env python3
"""chroma_kill_test.py — backlog #220: does a SIGTERM during the diary upsert damage ChromaDB?

The risk: `stopServices()` (main.js) calls `ragProcess.kill()` = SIGTERM. kurisu_rag_server.py
installs no handler, so the process dies at once. If Zani quits during the boot `/index-diary`,
the kill can land inside `col.upsert(...)`.

WORKS ONLY ON COPIES. It snapshots data/chroma ONCE (app and RAG server must be CLOSED) into
--work, and every trial runs on a FRESH copy of that snapshot. It refuses any path under the real
data/ folder. No Ollama call: new rows reuse REAL bge-m3 vectors taken from the copy's
`kurisu_en` collection (distinct, deduplicated), so the index sees realistic vectors.

PILOT LESSONS (2026-10-04) that shaped this design:
  - Random uniform vectors are NOT realistic: after a clean reopen ~20% of them were missing from
    a full self-query. With real bge-m3 vectors it is 1-2 of 122, and it CHANGES between reopens
    of the same untouched copy (Chroma 1.5.8 rebuilds the HNSW graph from its log on open). So
    self-retrieval is approximate even with NO kill — it is compared against an UNCUT arm, never
    judged against an absolute bar.
  - A kill leaves `chroma.sqlite3-journal` (a hot rollback journal). Opening the file READ-ONLY
    first cannot roll it back and gives "attempt to write a readonly database". The real next
    boot opens it read-write through Chroma, which rolls it back. So the checks open Chroma FIRST.

Two arms per K (K = new entries per upsert; 1 = a normal boot, 50 = the worst case, a full diary):
  UNCUT: the child upserts and exits normally.
  KILL:  the parent sends SIGTERM at a random delay after the child prints S (just before upsert),
         within [0, 2 x the median uncut upsert time]. The child prints E right after upsert
         returns, so each kill is classed BEFORE-E ("during") or AFTER-E ("after"). A kill on a
         dead child is "missed" and never counts as a pass (CLAUDE.md 52).

PRE-REGISTERED checks, run in a FRESH process after each trial (D = must hold in EVERY trial):
  D1. chromadb.PersistentClient opens the copy (as the server does) and all collections exist.
  D2. PRAGMA integrity_check == ok (read after D1 has rolled back any hot journal).
  D3. Every ORIGINAL diary row is unchanged (same ids, same documents).
  D4. Every stored diary row has a 1024-dim embedding — no document without a vector.
      (The dangerous case: /index-diary skips by TEXT, so a stored-but-vectorless row would
      never be re-added.)
  D5. The batch is atomic: new rows stored after the trial = 0 or K, never in between.
  D6. "Next boot": the server's own skip-by-text + upsert for the same K texts; afterwards the
      count is orig + K, no duplicate documents, and D4 holds.
  R.  Recall, after D6: rows (of all) absent from a full-k query with their own vector.
      FAIL only if the KILL arm's pooled absent rate is higher than the UNCUT arm's with
      one-sided Fisher p < 0.05.
Bound: 0 D-failures in n DURING kills puts the per-kill failure rate below 3/n at 95%.

SELFTEST (--selftest): the checks must CATCH planted damage on copies — a truncated sqlite file
(D1/D2), an original document rewritten (D3), and a partial batch of 20/50 (D5) — and must PASS an
untouched copy. Run it after editing this file.

ADDENDUM 1 (2026-10-04, after the pre-registered run PASSED): most DURING kills landed AFTER the
SQLite commit (the batch was stored; only 6 of 60 rolled back). To test the hardest case — a kill
BEFORE the commit — `--precommit` counts only DURING kills that left 0 new rows (rolled back),
and `--window-scale 0.5` moves the kill window to [0, 0.5 x the uncut upsert time]. Same checks.

Usage: python3 dev/chroma_kill_test.py --work SCRATCH_DIR [--during 30] [--uncut 30] [--ks 1,50]
       python3 dev/chroma_kill_test.py --work SCRATCH_DIR --precommit --window-scale 0.5 --during 30
       python3 dev/chroma_kill_test.py --work SCRATCH_DIR --selftest
Exit 0 = PASS · 3 = a failure (failing copies kept in --work) · 1 = could not run.
"""
import argparse, hashlib, json, math, os, random, shutil, signal, sqlite3, subprocess, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_CHROMA = os.path.join(REPO, 'data', 'chroma')
DIM = 1024


def die(msg):
    print('CANNOT RUN: ' + msg, flush=True)
    sys.exit(1)


def stable_id(text):           # byte-identical to kurisu_rag_server.py /index-diary
    return 'd' + hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]


def texts_for(seed, k):
    return [f'#220 kill-test entry {seed}-{i}: the quick brown fox.' for i in range(k)]


def vecs_for(pool, seed, k):
    return random.Random(seed).sample(pool, k)


# ── child modes (each runs in its own process) ───────────────────────────────────────────
def child_upsert(path, pool_json, k, seed, mode):
    """The server's /index-diary step on the copy. mode 'kill' waits to be killed; 'uncut' exits."""
    import chromadb
    pool = json.load(open(pool_json))
    client = chromadb.PersistentClient(path=path)
    col = client.get_or_create_collection('amadeus_diary')
    seen = set((d or '').strip() for d in col.get(include=['documents'])['documents'])
    ids, docs, metas, embs = [], [], [], []
    for i, (t, e) in enumerate(zip(texts_for(seed, k), vecs_for(pool, seed, k))):
        if t in seen:
            continue
        ids.append(stable_id(t)); docs.append(t); metas.append({'date': '2026-10-04', 'index': i}); embs.append(e)
    print('S', flush=True)
    col.upsert(ids=ids, embeddings=embs, documents=docs, metadatas=metas)
    print('E', flush=True)
    if mode == 'kill':
        time.sleep(5)              # stay alive like the server; the parent kills it


def child_verify(path, orig_json, pool_json, k, seed):
    """Prints one JSON line with the D-check failures and the recall counts."""
    fail, out = [], {'new_stored': -1, 'absent': -1, 'rows': -1}
    try:
        import chromadb
        orig = json.load(open(orig_json)); pool = json.load(open(pool_json))
        client = chromadb.PersistentClient(path=path)                                  # D1
        names = sorted(c.name for c in client.list_collections())
        if names != orig['collections']:
            fail.append(f'D1 collections {names}')
        col = client.get_collection('amadeus_diary')
        col.count()                                                                     # forces the open
        con = sqlite3.connect(os.path.join(path, 'chroma.sqlite3'))                    # D2
        ic = con.execute('PRAGMA integrity_check').fetchone()[0]; con.close()
        if ic != 'ok':
            fail.append(f'D2 integrity_check={ic}')
        g = col.get(include=['documents', 'embeddings'])
        now = dict(zip(g['ids'], g['documents']))
        changed = [i for i, d in orig['rows'].items() if now.get(i) != d]               # D3
        if changed:
            fail.append(f'D3 {len(changed)} original rows changed/missing')

        def no_vec(gg):
            return [i for i, e in zip(gg['ids'], gg['embeddings']) if e is None or len(e) != DIM]
        nv = no_vec(g)                                                                  # D4
        if nv:
            fail.append(f'D4 {len(nv)} rows without a vector: {nv[:3]}')
        texts = texts_for(seed, k)
        new_stored = sum(stable_id(t) in now for t in texts)                            # D5
        out['new_stored'] = new_stored
        if new_stored not in (0, k):
            fail.append(f'D5 partial batch: {new_stored}/{k} stored')
        seen = set((d or '').strip() for d in now.values())                            # D6
        ids, docs, embs = [], [], []
        for t, e in zip(texts, vecs_for(pool, seed, k)):
            if t not in seen:
                ids.append(stable_id(t)); docs.append(t); embs.append(e)
        if ids:
            col.upsert(ids=ids, embeddings=embs, documents=docs,
                       metadatas=[{'date': '2026-10-04', 'index': 0}] * len(ids))
        a = col.get(include=['documents', 'embeddings'])
        if len(a['ids']) != len(orig['rows']) + k:
            fail.append(f'D6 count {len(a["ids"])} != {len(orig["rows"]) + k}')
        if len(set(a['documents'])) != len(a['documents']):
            fail.append('D6 duplicate documents')
        nv = no_vec(a)
        if nv:
            fail.append(f'D6 {len(nv)} rows without a vector after re-index')
        absent = 0                                                                      # R
        for i, e in zip(a['ids'], a['embeddings']):
            r = col.query(query_embeddings=[list(e)], n_results=len(a['ids']))
            absent += i not in r['ids'][0]
        out.update(absent=absent, rows=len(a['ids']))
    except Exception as e:
        fail.append(f'exception: {type(e).__name__}: {e}')
    print(json.dumps({'ok': not fail, 'fail': fail, **out}))


# ── parent ───────────────────────────────────────────────────────────────────────────────
def py(args, **kw):
    return [sys.executable, os.path.abspath(__file__)] + [str(a) for a in args]


def prepare(work):
    real = os.path.realpath(os.path.join(REPO, 'data'))
    if os.path.realpath(work).startswith(real):
        die(f'{work} is inside the real data/ folder')
    for name, pat in (('the Amadeus app', ['-x', 'Amadeus']), ('a RAG server', ['-f', 'kurisu_rag_server.py'])):
        if subprocess.run(['pgrep'] + pat, capture_output=True).returncode == 0:
            die(f'{name} is running — the snapshot must not be taken while ChromaDB may be written')
    os.makedirs(work, exist_ok=True)
    snap = os.path.join(work, 'snapshot')
    shutil.rmtree(snap, ignore_errors=True)
    shutil.copytree(REAL_CHROMA, snap, ignore=shutil.ignore_patterns('*.bak-*'))
    code = ('import chromadb,json,sys\n'
            'import numpy as np\n'
            'c=chromadb.PersistentClient(path=sys.argv[1])\n'
            'g=c.get_collection("amadeus_diary").get(include=["documents","embeddings"])\n'
            'D=np.array(g["embeddings"],dtype=float)\n'
            'pool=[]\n'
            'for e in np.array(c.get_collection("kurisu_en").get(include=["embeddings"])["embeddings"],dtype=float):\n'
            '  S=np.vstack([D]+pool) if pool else D\n'
            '  if np.min(np.sum((S-e)**2,axis=1))>1e-6: pool.append(e[None,:])\n'
            '  if len(pool)==200: break\n'
            'json.dump({"collections":sorted(x.name for x in c.list_collections()),'
            '"rows":dict(zip(g["ids"],g["documents"]))},open(sys.argv[2],"w"))\n'
            'json.dump([p[0].tolist() for p in pool],open(sys.argv[3],"w"))\n')
    oj, pj = os.path.join(work, 'orig.json'), os.path.join(work, 'pool.json')
    r = subprocess.run([sys.executable, '-c', code, snap, oj, pj], capture_output=True, text=True)
    if r.returncode != 0:
        die('cannot read the snapshot copy: ' + r.stderr[-400:])
    if len(json.load(open(pj))) < 200:
        die('fewer than 200 distinct real vectors in kurisu_en')
    return snap, oj, pj


def verify(cp, oj, pj, k, seed):
    v = subprocess.run(py(['--child-verify', cp, oj, pj, k, seed]), capture_output=True, text=True, timeout=600)
    try:
        return json.loads(v.stdout.strip().splitlines()[-1])
    except Exception:
        return {'ok': False, 'fail': ['verify crashed: ' + v.stderr[-300:]], 'absent': -1, 'rows': -1}


def run_trial(snap, work, oj, pj, k, seed, mode, window):
    cp = os.path.join(work, f'{mode}_k{k}_{seed}')
    shutil.rmtree(cp, ignore_errors=True); shutil.copytree(snap, cp)
    p = subprocess.Popen(py(['--child-upsert', cp, pj, k, seed, mode]),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.stdout.readline().strip() != 'S':
        p.kill(); p.wait()
        return 'error', {'ok': False, 'fail': ['child never reached upsert: ' + p.stderr.read()[-300:]]}, cp, None
    t0 = time.perf_counter()
    if mode == 'kill':
        time.sleep(random.Random(seed).uniform(0, window))
        alive = p.poll() is None
        p.send_signal(signal.SIGTERM)          # what Node's ChildProcess.kill() sends by default
        out, _ = p.communicate(timeout=30)
        phase = 'missed' if not alive else ('after' if 'E' in out.split() else 'during')
        dt = None
    else:
        e = p.stdout.readline().strip(); dt = time.perf_counter() - t0
        p.communicate(timeout=60)
        phase = 'uncut' if (e == 'E' and p.returncode == 0) else 'error'
    return phase, verify(cp, oj, pj, k, seed), cp, dt


def selftest(snap, work, oj, pj):
    orig = json.load(open(oj)); k, seed = 50, 4242; bad = 0
    pool = json.load(open(pj))

    def fresh(name):
        cp = os.path.join(work, 'self_' + name); shutil.rmtree(cp, ignore_errors=True); shutil.copytree(snap, cp)
        return cp

    def plant(cp, code):
        r = subprocess.run([sys.executable, '-c', 'import chromadb,json,sys\n' + code, cp, pj],
                           capture_output=True, text=True)
        if r.returncode != 0:
            die('could not plant a mutant: ' + r.stderr[-300:])

    cases = []
    cp = fresh('clean'); cases.append(('untouched copy', cp, True, None))
    cp = fresh('trunc'); db = os.path.join(cp, 'chroma.sqlite3')
    with open(db, 'r+b') as f:
        f.truncate(os.path.getsize(db) // 2)
    cases.append(('truncated sqlite', cp, False, ('D1', 'D2', 'exception')))
    cp = fresh('d3'); first = next(iter(orig['rows']))
    plant(cp, f'c=chromadb.PersistentClient(path=sys.argv[1]).get_collection("amadeus_diary")\n'
              f'e=c.get(ids=[{first!r}],include=["embeddings"])["embeddings"][0]\n'
              f'c.update(ids=[{first!r}],documents=["changed"],embeddings=[list(map(float,e))])\n')
    cases.append(('original document rewritten', cp, False, ('D3',)))
    cp = fresh('d5'); texts = texts_for(seed, k)[:20]; ids = [stable_id(t) for t in texts]
    plant(cp, f'c=chromadb.PersistentClient(path=sys.argv[1]).get_collection("amadeus_diary")\n'
              f'import random\npool=json.load(open(sys.argv[2]))\n'
              f'v=random.Random({seed}).sample(pool,{k})[:20]\n'
              f'c.upsert(ids={ids!r},documents={texts!r},embeddings=v)\n')
    cases.append(('partial batch 20/50', cp, False, ('D5',)))
    for name, cp, want_ok, tags in cases:
        res = verify(cp, oj, pj, k if name != 'untouched copy' else 0, seed)
        good = res['ok'] if want_ok else (not res['ok'] and any(f.startswith(tags) for f in res['fail']))
        bad += not good
        print(f'  {"ok " if good else "BAD"} {name}: ok={res["ok"]} {res["fail"][:2]}', flush=True)
        shutil.rmtree(cp, ignore_errors=True)
    shutil.rmtree(snap, ignore_errors=True)
    print(f'[#220] SELFTEST: {len(cases) - bad}/{len(cases)} behaved correctly', flush=True)
    return 0 if bad == 0 else 3


def fisher_one_sided(a, b, c, d):
    """P(kill absent >= a) under H0; table [[a, b], [c, d]] = kill absent/present, uncut absent/present."""
    n1, n2, m = a + b, c + d, a + c
    def h(x):
        return math.comb(n1, x) * math.comb(n2, m - x) / math.comb(n1 + n2, m)
    return sum(h(x) for x in range(a, min(n1, m) + 1))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--child-upsert':
        return child_upsert(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
    if len(sys.argv) > 1 and sys.argv[1] == '--child-verify':
        return child_verify(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]))
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--during', type=int, default=30)
    ap.add_argument('--uncut', type=int, default=30)
    ap.add_argument('--max-kills', type=int, default=300)
    ap.add_argument('--ks', default='1,50')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--window-scale', type=float, default=2.0)
    ap.add_argument('--precommit', action='store_true')
    a = ap.parse_args()
    snap, oj, pj = prepare(a.work)
    if a.selftest:
        sys.exit(selftest(snap, a.work, oj, pj))
    orig = json.load(open(oj))
    print(f'[#220] snapshot: {len(orig["rows"])} diary rows, collections {orig["collections"]}', flush=True)
    log = open(os.path.join(a.work, 'trials.jsonl'), 'a')
    failed = False

    def record(k, seed, phase, res, cp):
        nonlocal failed
        log.write(json.dumps({'k': k, 'seed': seed, 'phase': phase, **res}) + '\n'); log.flush()
        if phase in ('during', 'after', 'uncut') and res['ok']:
            shutil.rmtree(cp, ignore_errors=True)
        elif phase == 'missed':
            shutil.rmtree(cp, ignore_errors=True)
        else:
            failed = True
            print(f'  FAIL k={k} seed={seed} {phase}: {res["fail"]} (copy kept: {cp})', flush=True)

    for k in [int(x) for x in a.ks.split(',')]:
        ut, ua, ur = [], 0, 0
        for n in range(a.uncut):                                       # UNCUT arm
            seed = k * 1_000_000 + n
            phase, res, cp, dt = run_trial(snap, a.work, oj, pj, k, seed, 'uncut', 0)
            record(k, seed, phase, res, cp)
            if dt is not None:
                ut.append(dt)
            ua += max(res.get('absent', 0), 0); ur += max(res.get('rows', 0), 0)
        window = a.window_scale * sorted(ut)[len(ut) // 2] if ut else 0.03
        print(f'[#220] K={k} UNCUT: n={a.uncut}, upsert median {window / a.window_scale * 1000:.1f} ms, '
              f'recall absent {ua}/{ur}', flush=True)
        cnt = {'during': 0, 'after': 0, 'missed': 0, 'error': 0}; dfail = {'during': 0, 'after': 0}; pre = 0
        ka, kr, seed = 0, 0, k * 1_000_000 + 500_000
        def target():
            return pre if a.precommit else cnt['during']
        while target() < a.during and sum(cnt.values()) < a.max_kills:   # KILL arm
            seed += 1
            phase, res, cp, _ = run_trial(snap, a.work, oj, pj, k, seed, 'kill', window)
            cnt[phase] += 1
            pre += phase == 'during' and res.get('new_stored') == 0
            if phase in dfail and not res['ok']:
                dfail[phase] += 1
            if phase in dfail:
                ka += max(res.get('absent', 0), 0); kr += max(res.get('rows', 0), 0)
            record(k, seed, phase, res, cp)
        p = fisher_one_sided(ka, kr - ka, ua, ur - ua) if kr and ur else 1.0
        rfail = p < 0.05 and kr and ur and ka / kr > ua / ur
        failed |= bool(rfail)
        print(f'[#220] K={k} KILL: during={cnt["during"]} after={cnt["after"]} missed={cnt["missed"]} '
              f'error={cnt["error"]} (rolled back before commit: {pre}) | D-failures during={dfail["during"]} after={dfail["after"]} | '
              f'recall absent {ka}/{kr} vs uncut {ua}/{ur}, one-sided p={p:.3f}'
              f'{" -> R FAIL" if rfail else ""}', flush=True)
        what = 'PRE-COMMIT' if a.precommit else 'DURING'
        if target() < a.during:
            failed = True
            print(f'[#220] K={k}: only {target()} {what} kills — NOT ENOUGH for the bound', flush=True)
        else:
            print(f'[#220] K={k}: 95% upper bound on the per-kill D-failure rate ({what}): '
                  f'{3 / target() * 100:.0f}% (rule of three, if 0 failures)', flush=True)
    shutil.rmtree(snap, ignore_errors=True)
    print('[#220] RESULT: ' + ('FAIL — see above' if failed else 'PASS'), flush=True)
    sys.exit(3 if failed else 0)


if __name__ == '__main__':
    main()
