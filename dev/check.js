#!/usr/bin/env node
/**
 * dev/check.js — pre-launch sanity check.  Run: `npm run check`
 *
 * WHY THIS EXISTS (backlog #157):
 *   amadeus.html is a single ~4,300-line inline <script>.  A duplicate `const`
 *   silently kills ALL JS and the only symptom is the boot video sticking
 *   (CLAUDE.md rule 3 / bugs.md 4) — a symptom that points nowhere near the
 *   cause.  Nothing caught that before launch.  Now this does, in ~1 second.
 *
 * Checks:
 *   1. Every inline <script> in amadeus.html parses (`node --check`).
 *      Error line numbers are remapped to real amadeus.html lines.
 *   2. The python servers compile (`py_compile`).
 *   3. buildSystemPrompt's injection anchors still exist in SYSTEM_PROMPT.
 *      Without them memory/relationship injection silently no-ops — it only
 *      console.warns, which you will never see at 2am.
 *   4. The main-process and preload files parse (`node --check`).
 *      Added after backlog #170: checks 1-3 read amadeus.html and the python
 *      servers only, so a change confined to main.js passed a green "safe to
 *      relaunch" having never been read.  That is this checker's most expensive
 *      possible blind spot — see the note above checkNodeFiles().
 *
 * Flags:
 *   --json   machine-readable output: {ok, results:[{kind,name,ok,detail}]}.
 *            Used by `npm run check:selftest` so it can assert WHICH check
 *            failed, not merely that something failed.  Human output is the
 *            default and is unchanged by this flag's existence.
 *
 * Zero dependencies.  Exit 0 = safe to relaunch, exit 1 = do not launch.
 */
const fs = require('fs')
const os = require('os')
const path = require('path')
const { execFileSync } = require('child_process')

// AMADEUS_DIR override exists so this checker can be tested against a mutated copy
// without ever touching the real project (see dev/check.selftest.js).
const ROOT = process.env.AMADEUS_DIR || path.join(os.homedir(), 'Documents', 'Amadeus')
const PYTHON = '/opt/homebrew/bin/python3'      // bug 19: Electron/PATH — same hardcode
const JSON_MODE = process.argv.includes('--json')

// kind is the machine-readable category: 'js-syntax' | 'js-file' | 'python' | 'anchor'.
// 'js-syntax' is an inline <script> extracted from HTML; 'js-file' is a real .js
// file on disk.  They are separate kinds so the self-test can assert that a fault
// planted in main.js is killed by the main-process check specifically, and not by
// some other check for an unrelated reason.
const results = []
const ok = (kind, name) => results.push({ kind, name, ok: true, detail: null })
const bad = (kind, name, detail) => results.push({ kind, name, ok: false, detail })

// ── 1. Inline <script> syntax ────────────────────────────────────────────────
// NOTE: only text BETWEEN <script> and </script> is checked, because only that
// text is JavaScript.  Content after the closing tag is inert in the browser
// too, so the checker deliberately ignores it (see the equivalent mutant in
// dev/check.selftest.js, which locks this boundary in).
function checkInlineScripts(file) {
  const label = path.basename(file)
  const src = fs.readFileSync(file, 'utf8')
  const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g
  let m, n = 0
  while ((m = re.exec(src)) !== null) {
    n++
    const body = m[1]
    // Line in the ORIGINAL file where this script's body starts.
    const startLine = src.slice(0, m.index + m[0].indexOf(body)).split('\n').length
    const tmp = path.join(os.tmpdir(), `amadeus_check_${process.pid}_${n}.js`)
    fs.writeFileSync(tmp, body)
    try {
      execFileSync(process.execPath, ['--check', tmp], { stdio: 'pipe' })
      ok('js-syntax', `${label} inline script #${n} parses (${body.split('\n').length} lines)`)
    } catch (e) {
      const err = (e.stderr || '').toString()
      // node prints "<tmpfile>:<line>" — remap to the real amadeus.html line.
      const lm = err.match(new RegExp(`${tmp.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}:(\\d+)`))
      const realLine = lm ? Number(lm[1]) + startLine - 1 : null
      const reason = (err.split('\n').find(l => /Error/.test(l)) || 'syntax error').trim()
      bad('js-syntax', `${label} inline script #${n}`,
          `${reason}${realLine ? `\n      → ${label}:${realLine}` : ''}`)
    } finally { try { fs.unlinkSync(tmp) } catch (_) {} }
  }
  if (n === 0) bad('js-syntax', label, 'no inline <script> found — did the file structure change?')
}

// ── 1b. Main-process / preload files parse ──────────────────────────────────
// WHY (backlog #170, found while shipping bugs.md 70): checks 1-3 never read
// main.js or the preload scripts.  A change confined to the main process — which
// is exactly what a diary/IPC/lifecycle fix is — got a green "safe to relaunch"
// with literally zero coverage, and `npm run build` only packages, it does not
// parse.  The failure mode is also the worst one in this app: a main-process
// syntax error is not a broken feature, it is NO WINDOW AND NO BOOT VIDEO, with
// nothing on screen pointing anywhere near the cause.
//
// preload_call.js is included because call-window.html is already checked above;
// checking the window but not the script Electron injects into it would be a gap
// of the same shape.
//
// These are real files rather than fragments extracted from HTML, so node's own
// line numbers are already correct — no remapping needed (contrast the inline case).
function checkNodeFiles(files) {
  for (const f of files) {
    const full = path.join(ROOT, f)
    if (!fs.existsSync(full)) { bad('js-file', f, 'missing'); continue }
    try {
      execFileSync(process.execPath, ['--check', full], { stdio: 'pipe' })
      ok('js-file', `${f} parses`)
    } catch (e) {
      const err = (e.stderr || '').toString()
      const reason = (err.split('\n').find(l => /Error/.test(l)) || 'syntax error').trim()
      const lm = err.match(new RegExp(`${full.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}:(\\d+)`))
      bad('js-file', f, `${reason}${lm ? `\n      → ${f}:${lm[1]}` : ''}`)
    }
  }
}

// ── 2. Python servers compile ────────────────────────────────────────────────
function checkPython(files) {
  const py = fs.existsSync(PYTHON) ? PYTHON : 'python3'
  for (const f of files) {
    const full = path.join(ROOT, f)
    if (!fs.existsSync(full)) { bad('python', f, 'missing'); continue }
    try {
      execFileSync(py, ['-m', 'py_compile', full], { stdio: 'pipe' })
      ok('python', `${f} compiles`)
    } catch (e) {
      bad('python', f, ((e.stderr || '').toString().split('\n').filter(Boolean).pop() || 'compile error').trim())
    }
  }
}

// ── 3. System-prompt injection anchors ───────────────────────────────────────
// buildSystemPrompt() injects memory at /\nCHARACTER\n/ and the relationship
// directive at /\nTWO MODES\n/.  If either header is reworded or loses its
// surrounding blank lines, injection silently does nothing.
function checkAnchors(file) {
  const src = fs.readFileSync(file, 'utf8')
  const m = src.match(/const SYSTEM_PROMPT\s*=\s*`([\s\S]*?)`\s*\n/)
  if (!m) { bad('anchor', 'SYSTEM_PROMPT', 'template literal not found in amadeus.html'); return }
  const prompt = m[1]
  for (const anchor of ['\nCHARACTER\n', '\nTWO MODES\n']) {
    const label = `prompt anchor ${JSON.stringify(anchor.trim())}`
    const count = prompt.split(anchor).length - 1
    if (count === 1) ok('anchor', `${label} present`)
    else bad('anchor', label, `found ${count}x (expected exactly 1) — buildSystemPrompt injection would ${count === 0 ? 'silently no-op' : 'hit the wrong site'}`)
  }
}

checkInlineScripts(path.join(ROOT, 'amadeus.html'))
checkInlineScripts(path.join(ROOT, 'call-window.html'))
checkNodeFiles(['main.js', 'preload.js', 'preload_call.js'])
checkPython(['kurisu_fish_server.py', 'kurisu_rag_server.py', 'kurisu_whisper_server.py', 'build_kurisu_index.py'])
checkAnchors(path.join(ROOT, 'amadeus.html'))

const failed = results.filter(r => !r.ok)

if (JSON_MODE) {
  process.stdout.write(JSON.stringify({ ok: failed.length === 0, results }, null, 2) + '\n')
  process.exit(failed.length ? 1 : 0)
}

console.log('\nAmadeus pre-launch check\n')
for (const r of results) {
  if (r.ok) console.log(`  \x1b[32m✓\x1b[0m ${r.name}`)
  else console.log(`  \x1b[31m✗\x1b[0m ${r.name}: ${r.detail}`)
}
if (failed.length) {
  console.log(`\n\x1b[31m${failed.length} problem(s) — DO NOT relaunch until fixed.\x1b[0m\n`)
  process.exit(1)
}
console.log('\n\x1b[32mAll checks passed — safe to relaunch.\x1b[0m\n')
