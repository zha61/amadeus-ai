/*
 * dev/stale_kill_test.js — a spawn frees its port from a STALE AMADEUS server only (backlog #150, bugs.md 100).
 * Run:  node dev/stale_kill_test.js        (~5 s, no model call, no Amadeus port touched)
 *
 * The old `lsof -ti:PORT | xargs kill -9` killed every process with a socket on the port — a CLIENT
 * too, and any other app.  The shipped helper block is EXTRACTED FROM main.js by anchor (exit 2 if
 * one moves) and run against REAL processes on scratch ports (20000+), with AMADEUS_DIR pointed at a
 * scratch folder.  OUTCOME checks: our stale server dies and its port frees; a client, a foreign
 * listener, the same script in another folder and http.server in another folder all SURVIVE, and
 * each foreign one is logged.  Plants 4 mutants; each must be caught.
 */
const fs = require('fs'), path = require('path'), os = require('os'), net = require('net')
const { execSync, spawn } = require('child_process')
const main = fs.readFileSync(path.join(__dirname, '..', 'main.js'), 'utf8')
const cut = (src, a, b) => { const i = src.indexOf(a), j = src.indexOf(b, i + 1); if (i < 0 || j < 0) { console.error('ANCHOR MISSING: ' + a + ' … ' + b); process.exit(2) } return src.slice(i, j) }
const BLOCK = cut(main, '// ── STALE-SERVER KILL (backlog #150', '// ── end STALE-SERVER KILL ──')
const PY = '/opt/homebrew/bin/python3'
const sleep = ms => new Promise(r => setTimeout(r, ms))

const ROOT = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'stale_kill_')))
const AMA = path.join(ROOT, 'Amadeus'), OTHER = path.join(ROOT, 'other')
fs.mkdirSync(AMA); fs.mkdirSync(OTHER)
const LISTENER = 'import socket,sys,time\ns=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\ns.bind(("127.0.0.1",int(sys.argv[1]))); s.listen(); time.sleep(60)\n'
for (const d of [AMA, OTHER]) for (const f of ['kurisu_test_server.py', 'someone_else.py']) fs.writeFileSync(path.join(d, f), LISTENER)

const kids = []
function start(args, cwd) { const p = spawn(PY, args, { cwd, stdio: 'ignore', detached: true }); kids.push(p); return p }
const alive = pid => { try { process.kill(pid, 0); return true } catch (e) { return false } }
const listening = port => { try { return execSync(`lsof -nP -t -iTCP:${port} -sTCP:LISTEN`, { encoding: 'utf8' }).trim() !== '' } catch (e) { return false } }
async function waitFor(fn, ms = 4000) { const t = Date.now(); while (Date.now() - t < ms) { if (fn()) return true; await sleep(50) } return false }
let nextPort = 20000 + Math.floor(Math.random() * 20000)

function load(src) {
  const logs = { log: [], warn: [] }
  const con = { log: m => logs.log.push(m), warn: m => logs.warn.push(m) }
  const api = new Function('execSync', 'path', 'fs', 'process', 'console', 'AMADEUS_DIR', src + '\nreturn { killStaleServer }')(execSync, path, fs, process, con, AMA)
  return { kill: api.killStaleServer, logs }
}
const SCRIPT = { script: 'kurisu_test_server.py' }, HTTP = { module: 'http.server' }

async function checks(src) {
  const r = []; const t = (n, c) => r.push([n, !!c])
  const { kill, logs } = load(src)
  const clear = () => { logs.log.length = 0; logs.warn.length = 0 }

  // 1. our stale server, started by ABSOLUTE path (as main.js spawns it)
  let port = nextPort++, p = start([path.join(AMA, 'kurisu_test_server.py'), String(port)], ROOT)
  await waitFor(() => listening(port)); clear(); kill(port, SCRIPT)
  t('stale server (absolute path): killed, port free', await waitFor(() => !alive(p.pid) || !listening(port)) && !listening(port))
  t('stale server (absolute path): logged as killed, no warning', logs.log.length === 1 && logs.warn.length === 0)

  // 2. our stale server, started by hand with a RELATIVE path from the Amadeus folder
  port = nextPort++; p = start(['kurisu_test_server.py', String(port)], AMA)
  await waitFor(() => listening(port)); clear(); kill(port, SCRIPT)
  t('stale server (relative path, hand-started): killed', await waitFor(() => !listening(port)))

  // 3. a CLIENT with an open connection to our stale server must survive
  port = nextPort++; p = start([path.join(AMA, 'kurisu_test_server.py'), String(port)], ROOT)
  await waitFor(() => listening(port))
  const client = start(['-c', `import socket,time; s=socket.create_connection(("127.0.0.1",${port})); time.sleep(60)`], ROOT)
  await sleep(400); clear(); kill(port, SCRIPT)
  t('client: server killed', await waitFor(() => !listening(port)))
  t('client: the CLIENT is still alive', alive(client.pid))
  t('client: no warning about the client', logs.warn.length === 0)

  // 4. the same script name in ANOTHER folder: not ours
  port = nextPort++; p = start(['kurisu_test_server.py', String(port)], OTHER)
  await waitFor(() => listening(port)); clear(); kill(port, SCRIPT); await sleep(300)
  t('same script, other folder: NOT killed', alive(p.pid) && listening(port))
  t('same script, other folder: logged as a warning', logs.warn.length === 1 && /NOT killed/.test(logs.warn[0]))

  // 5. a foreign program on the port
  port = nextPort++; p = start([path.join(AMA, 'someone_else.py'), String(port)], AMA)
  await waitFor(() => listening(port)); clear(); kill(port, SCRIPT); await sleep(300)
  t('foreign listener: NOT killed, warned', alive(p.pid) && listening(port) && logs.warn.length === 1)

  // 6. http.server: from the Amadeus folder = ours; from another folder = not ours
  port = nextPort++; p = start(['-m', 'http.server', String(port), '--bind', '127.0.0.1'], AMA)
  await waitFor(() => listening(port)); clear(); kill(port, HTTP)
  t('http.server in the Amadeus folder: killed', await waitFor(() => !listening(port)))
  port = nextPort++; p = start(['-m', 'http.server', String(port), '--bind', '127.0.0.1'], OTHER)
  await waitFor(() => listening(port)); clear(); kill(port, HTTP); await sleep(300)
  t('http.server in another folder: NOT killed, warned', alive(p.pid) && listening(port) && logs.warn.length === 1)

  // 7. nobody listening: silent no-op
  port = nextPort++; clear(); let threw = false
  try { kill(port, SCRIPT) } catch (e) { threw = true }
  t('free port: no throw, no log, no warning', !threw && logs.log.length === 0 && logs.warn.length === 0)
  return r
}

function structural() {
  const r = []; const t = (n, c) => r.push([n, !!c])
  t('main.js: no `lsof -ti:` port-kill left', !/execSync\(\s*['"`]lsof -ti:/.test(main) && !/xargs kill/.test(main.replace(/^\s*\/\/.*$/gm, '')))
  t('main.js: fish spawn frees 5002 for kurisu_fish_server.py', /killStaleServer\(5002, \{ script: 'kurisu_fish_server\.py' \}\)/.test(main))
  t('main.js: http spawn frees 8765 for http.server', /killStaleServer\(8765, \{ module: 'http\.server' \}\)/.test(main))
  t('main.js: rag spawn frees 5003 for kurisu_rag_server.py', /killStaleServer\(5003, \{ script: 'kurisu_rag_server\.py' \}\)/.test(main))
  t('main.js: whisper spawn frees 5004 for kurisu_whisper_server.py', /killStaleServer\(5004, \{ script: 'kurisu_whisper_server\.py' \}\)/.test(main))
  t('main.js: no OLLAMA_FLASH_ATTENTION set (#169)', !/OLLAMA_FLASH_ATTENTION\s*[:=]/.test(main))
  return r
}

;(async () => {
  let fail = 0
  try {
    const res = [...structural(), ...await checks(BLOCK)]
    for (const [n, ok] of res) { console.log((ok ? '  PASS  ' : '  FAIL  ') + n); if (!ok) fail++ }
    const mutants = {
      'LISTEN filter removed (clients listed)': BLOCK.replace('-iTCP:${port} -sTCP:LISTEN', '-i:${port}'),
      'identity check always true': BLOCK.replace('if (isOurServer(args, procCwd(pid), port, target))', 'if (true)'),
      'http.server folder check removed': BLOCK.replace('&& AMADEUS_DIRS.includes(cwd)', ''),
      'relative path not resolved against the folder': BLOCK.replace('want.includes(path.resolve(cwd, a))', 'want.includes(a)'),
    }
    let caught = 0
    for (const [name, src] of Object.entries(mutants)) {
      if (src === BLOCK) { console.log('  MUTANT DID NOT APPLY: ' + name); fail++; continue }
      const hit = (await checks(src)).some(([, ok]) => !ok)
      console.log((hit ? '  CAUGHT  ' : '  MISSED  ') + 'mutant: ' + name); hit ? caught++ : fail++
    }
    console.log(`\n${res.length} checks, ${caught}/${Object.keys(mutants).length} mutants caught — ${fail ? 'FAIL' : 'ALL PASS'}`)
  } finally {
    for (const k of kids) { try { process.kill(k.pid, 'SIGKILL') } catch (e) {} }
    try { fs.rmSync(ROOT, { recursive: true, force: true }) } catch (e) {}
  }
  process.exit(fail ? 1 : 0)
})()
