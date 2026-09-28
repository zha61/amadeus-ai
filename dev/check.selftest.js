#!/usr/bin/env node
/**
 * dev/check.selftest.js — does `npm run check` still have teeth?
 * Run: `npm run check:selftest`
 *
 * WHY THIS EXISTS:
 *   A checker that can no longer fail is worse than no checker: it reports all
 *   green forever and you trust it.  That decay is silent.  This finds it.
 *   (It also replaces an earlier manual test whose PASS condition was a screen
 *   of red text and exit 1 — correct, but unreadable as a result.)
 *
 * METHOD — mutation testing (DeMillo/Lipton/Sayward 1978):
 *   plant a known fault, then confirm the checker detects it.  Four elements
 *   separate a rigorous mutation test from a weak one, and all four are here:
 *
 *   1. CONTROL RUN.  The pristine copy must PASS first.  Without this a broken
 *      environment (no node, no python) fails everything and every mutant looks
 *      "caught" — a false pass.
 *   2. TARGETED KILL.  Asserting "the run failed" is not enough: a mutant could
 *      be caught by the wrong check for the wrong reason.  Each mutant must be
 *      killed by ITS OWN check kind, with every other kind still green.
 *   3. EQUIVALENT MUTANTS.  Mutations that must NOT be reported, proving the
 *      checker is precise rather than merely noisy.  Both of ours lock in a
 *      boundary a future "improvement" could plausibly cross:
 *        - text placed after </script> is not JavaScript, the browser ignores it
 *          too, and an earlier hand-written test was wrong about exactly this;
 *        - a const inside a function that shadows a top-level binding in main.js
 *          is legal JavaScript.  Rule 3 is about DUPLICATE consts in one scope,
 *          and anyone "strengthening" this checker with a naive identifier grep
 *          would break every main-process launch.  This mutant blocks that.
 *   4. MACHINE-READABLE CONTRACT.  Asserts run against `check.js --json`, not
 *      against scraped human text.
 *
 * SAFETY:
 *   Every write goes through safeWrite(), which refuses any path outside the
 *   per-run temp dir or inside the real project.  Cleanup runs in `finally`.
 *
 * Zero dependencies.  Exit 0 = the checker works.  Exit 1 = do not trust it.
 */
const fs = require('fs')
const os = require('os')
const path = require('path')
const { execFileSync } = require('child_process')

const REAL_ROOT = path.resolve(path.join(os.homedir(), 'Documents', 'Amadeus'))
const CHECKER = path.join(__dirname, 'check.js')
const COPY = ['amadeus.html', 'call-window.html', 'kurisu_fish_server.py',
              'kurisu_rag_server.py', 'kurisu_whisper_server.py', 'build_kurisu_index.py',
              // main-process + preload files (backlog #170).  These MUST be copied or
              // the control run fails them as 'missing' and every mutant looks caught.
              'main.js', 'preload.js', 'preload_call.js']

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'amadeus-selftest-'))
// Hard guard: the sandbox must never be inside the real project.
if (path.resolve(TMP).startsWith(REAL_ROOT + path.sep)) {
  console.error('ABORT: temp dir resolved inside the project. Refusing to mutate anything.')
  process.exit(1)
}

const green = s => `\x1b[32m${s}\x1b[0m`
const red   = s => `\x1b[31m${s}\x1b[0m`

function safeWrite(p, content) {
  const r = path.resolve(p)
  if (!r.startsWith(path.resolve(TMP) + path.sep)) throw new Error(`refused write outside sandbox: ${r}`)
  if (r.startsWith(REAL_ROOT + path.sep)) throw new Error(`refused write inside the project: ${r}`)
  fs.writeFileSync(r, content)
}
const read = f => fs.readFileSync(path.join(TMP, f), 'utf8')
const write = (f, s) => safeWrite(path.join(TMP, f), s)

function freshCopy() {
  for (const f of COPY) fs.copyFileSync(path.join(REAL_ROOT, f), path.join(TMP, f))
}

/** Run the real checker against the sandbox and return its structured result. */
function runChecker() {
  const opts = { env: { ...process.env, AMADEUS_DIR: TMP }, stdio: 'pipe' }
  try {
    return JSON.parse(execFileSync(process.execPath, [CHECKER, '--json'], opts).toString())
  } catch (e) {
    const out = (e.stdout || '').toString()          // exit 1 still prints JSON
    if (!out) throw new Error(`checker produced no JSON: ${(e.stderr || '').toString().slice(0, 300)}`)
    return JSON.parse(out)
  }
}

// ── Mutants.  `kind` is the check that MUST catch it; null = must NOT be caught.
const MUTANTS = [
  {
    id: 'duplicate-const',
    kind: 'js-syntax',
    why: 'the exact bug 3 / rule 3 class — kills all JS, boot video sticks',
    apply() {
      const s = read('amadeus.html')
      const i = s.lastIndexOf('</script>')
      write('amadeus.html', s.slice(0, i) + '\nconst isLoading=1\n' + s.slice(i))
    }
  },
  {
    id: 'renamed-anchor',
    kind: 'anchor',
    why: 'buildSystemPrompt injection would silently no-op behind a console.warn',
    apply() {
      const s = read('amadeus.html')
      if (!s.includes('\nTWO MODES\n')) throw new Error('anchor absent before mutation')
      write('amadeus.html', s.replace('\nTWO MODES\n', '\nTWO MODES OF SPEECH\n'))
    }
  },
  {
    id: 'python-syntax',
    kind: 'python',
    why: 'a broken TTS server means no voice at all',
    apply() { write('kurisu_fish_server.py', read('kurisu_fish_server.py') + '\ndef broken(:\n') }
  },
  {
    id: 'main-js-syntax',
    kind: 'js-file',
    why: 'a main-process syntax error is NO WINDOW and no boot video — the blind spot #170 closed',
    apply() { write('main.js', read('main.js') + '\nconst broken = (\n') }
  },
  {
    id: 'preload-js-syntax',
    kind: 'js-file',
    why: 'proves BOTH files are really checked — a loop that stopped after main.js would pass without this',
    apply() { write('preload.js', read('preload.js') + '\nconst broken = (\n') }
  },
  {
    id: 'shadowed-const-in-main',
    kind: null,                                       // EQUIVALENT MUTANT
    why: 'a const shadowing a top-level binding inside a function is legal — a naive identifier grep would break every launch',
    apply() {
      const s = read('main.js')
      if (!/^let mainWindow\b/m.test(s)) throw new Error('top-level mainWindow binding absent — mutant is no longer equivalent')
      write('main.js', s + '\nfunction _selftestShadow() { const mainWindow = null; return mainWindow }\n')
    }
  },
  {
    id: 'text-after-script-tag',
    kind: null,                                       // EQUIVALENT MUTANT
    why: 'text after </script> is inert in the browser too — must NOT be reported',
    apply() { write('amadeus.html', read('amadeus.html') + '\nconst isLoading=1\n') }
  }
]

const lines = []
let failure = null

try {
  // ── Element 1: control run ────────────────────────────────────────────────
  freshCopy()
  const control = runChecker()
  if (!control.ok) {
    const which = control.results.filter(r => !r.ok).map(r => r.name).join(', ')
    failure = `the CONTROL run failed on an unmutated copy (${which}). ` +
              `Fix your project or environment first — mutant results would be meaningless.`
  } else {
    lines.push(`${green('✓')} control: an unmutated copy passes (${control.results.length} checks)`)

    // ── Elements 2 & 3: each mutant ─────────────────────────────────────────
    for (const m of MUTANTS) {
      freshCopy()
      m.apply()
      const r = runChecker()
      const failedKinds = [...new Set(r.results.filter(x => !x.ok).map(x => x.kind))]

      if (m.kind === null) {
        if (!r.ok) { failure = `equivalent mutant '${m.id}' was WRONGLY reported (${failedKinds.join(', ')}). The checker is over-eager.`; break }
        lines.push(`${green('✓')} ${m.id}: correctly ignored — ${m.why}`)
        continue
      }
      if (r.ok) { failure = `mutant '${m.id}' SURVIVED — the checker did not catch it. ${m.why}.`; break }
      if (!failedKinds.includes(m.kind)) { failure = `mutant '${m.id}' was caught, but by ${failedKinds.join('/')} instead of '${m.kind}' — right answer, wrong reason.`; break }
      const collateral = failedKinds.filter(k => k !== m.kind)
      if (collateral.length) { failure = `mutant '${m.id}' also broke unrelated checks (${collateral.join(', ')}) — the kill is not targeted.`; break }
      lines.push(`${green('✓')} ${m.id}: caught by the '${m.kind}' check, nothing else disturbed`)
    }
  }
} catch (e) {
  failure = `the self-test could not run: ${e.message}`
} finally {
  fs.rmSync(TMP, { recursive: true, force: true })
}

console.log('\nAmadeus checker self-test  (mutation testing — sandboxed copies only)\n')
for (const l of lines) console.log('  ' + l)
if (failure) {
  console.log(`  ${red('✗')} ${failure}`)
  console.log('\n' + red('SELF-TEST FAILED — do not trust `npm run check` until this is fixed.') + '\n')
  process.exit(1)
}
console.log('\n' + green(`SELF-TEST PASSED — ${MUTANTS.length}/${MUTANTS.length} mutants behaved correctly. \`npm run check\` has teeth.`) + '\n')
