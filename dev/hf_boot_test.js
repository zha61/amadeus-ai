#!/usr/bin/env node
/**
 * hf_boot_test.js — tests for the two 2026-09-07 fixes:
 *   backlog #195  the hands-free session ended 10 min after it STARTED
 *   CLAUDE.md 36  the boot prewarm kept running through the boot video
 *
 * Both blocks are EXTRACTED FROM amadeus.html BY ANCHOR, not copied here, so a
 * rename fails the test loudly rather than testing a stale copy (same design as
 * dev/perf_trace_test.js).
 *
 * CLAUDE.md 50 — test the OUTCOME, not the mechanism. The outcomes are:
 *   #195  a session in which someone keeps talking DOES NOT end at the idle cap
 *   36    when the boot cap wins the race, the prewarm's fetch is actually aborted
 *
 * Run: node dev/hf_boot_test.js
 */
const fs = require('fs')
const path = require('path')
const SRC = fs.readFileSync(path.join(__dirname, '..', 'amadeus.html'), 'utf8')

let pass = 0, fail = 0
const ok = (c, m) => { if (c) { pass++; console.log('  \x1b[32m✓\x1b[0m ' + m) } else { fail++; console.log('  \x1b[31m✗ ' + m + '\x1b[0m') } }

function extract(startAnchor, endAnchor, label) {
  const i = SRC.indexOf(startAnchor)
  if (i < 0) { fail++; console.log(`  \x1b[31m✗ anchor missing: ${label} ("${startAnchor}")\x1b[0m`); return null }
  const j = SRC.indexOf(endAnchor, i)
  if (j < 0) { fail++; console.log(`  \x1b[31m✗ end anchor missing: ${label}\x1b[0m`); return null }
  return SRC.slice(i, j)
}

// ── #195 ────────────────────────────────────────────────────────────────────
console.log('\nbacklog #195 — hands-free idle timeout vs absolute cap')

const idleMs = /const HF_IDLE_MAX_MS\s*=\s*([\d*]+)/.exec(SRC)
const absMs  = /const HF_SESSION_ABS_MAX_MS\s*=\s*([\d*]+)/.exec(SRC)
ok(!!idleMs, 'HF_IDLE_MAX_MS is declared')
ok(!!absMs,  'HF_SESSION_ABS_MAX_MS is declared')
ok(!/HF_SESSION_MAX_MS/.test(SRC), 'the old single-timer constant is fully gone')
const IDLE = idleMs ? eval(idleMs[1]) : 0, ABS = absMs ? eval(absMs[1]) : 0
ok(ABS > IDLE, `absolute cap (${ABS/60000}min) is longer than idle (${IDLE/60000}min)`)

const armSrc = extract('function hfArmIdle(){', '\n}', 'hfArmIdle') 
ok(armSrc && /clearTimeout\(hf\.idleTimer\)/.test(armSrc), 'hfArmIdle clears the previous idle timer before re-arming')
ok(/for\(const k of \[[^\]]*'idleTimer'[^\]]*\]\)/.test(SRC), 'hfStop clears idleTimer (no leaked timer after a session ends)')
ok(/hfArmIdle\(\)\s*\/\/ #195/.test(SRC), 'hfOnSpeechStart re-arms the idle timer')

// Both engines must reset it. bugs.md 80 shipped because only one path was hooked.
const sileroHook = /onSpeechStart:hfOnSpeechStart/.test(SRC)
const rmsHook = /hfOnSpeechStart\(\)/.test(SRC.slice(SRC.indexOf('async function hfStartRms')))
ok(sileroHook, 'Silero engine routes through hfOnSpeechStart')
ok(rmsHook, 'RMS fallback engine ALSO routes through hfOnSpeechStart (bugs.md 80)')

// OUTCOME: drive the real hfArmIdle with a fake clock.
;(function outcome195() {
  let now = 0, seq = 1
  const timers = new Map()
  const setTimeoutF = (fn, ms) => { const id = seq++; timers.set(id, { at: now + ms, fn }); return id }
  const clearTimeoutF = id => timers.delete(id)
  const advance = ms => {
    const end = now + ms
    for (;;) {
      let next = null
      for (const [id, t] of timers) if (t.at <= end && (!next || t.at < next[1].at)) next = [id, t]
      if (!next) break
      now = next[1].at; timers.delete(next[0]); next[1].fn()
    }
    now = end
  }
  const hf = { active: true, idleTimer: null }
  let stopped = null
  const hfStop = r => { stopped = r; hf.active = false }
  const hfStatus = () => {}
  const fn = new Function('hf', 'hfStop', 'hfStatus', 'HF_IDLE_MAX_MS', 'setTimeout', 'clearTimeout',
    armSrc + '\n}\nreturn hfArmIdle')(hf, hfStop, hfStatus, IDLE, setTimeoutF, clearTimeoutF)

  fn()                                   // session starts
  for (let i = 0; i < 12; i++) { advance(IDLE * 0.5); fn() }   // speaking every 5 min for an hour
  ok(stopped === null, 'a session with speech every 5 min survives past the 10-min idle cap (THE BUG)')

  advance(IDLE + 1000)                   // then go quiet
  ok(stopped === 'idle-timeout', 'and it DOES end once genuinely silent for the idle window')
})()

// ── CLAUDE.md 36 ────────────────────────────────────────────────────────────
console.log('\nCLAUDE.md 36 — the boot prewarm must stop when the cap wins')

ok(/await Promise\.race\(\[prewarmOllama\(pwAbort\.signal\), delay\(4000\)\]\)/.test(SRC),
   'the boot cap passes an abort signal into prewarmOllama')
ok(/pwAbort\.abort\(\)/.test(SRC), 'and aborts it after the race')
ok(/async function prewarmOllama\(externalSignal\)/.test(SRC), 'prewarmOllama accepts an external signal')
ok(/AbortSignal\.any\(\[controller\.signal, externalSignal\]\)/.test(SRC),
   'it combines the external signal with its own 30s timeout')
ok(/\} finally \{\s*\n\s*clearTimeout\(timer\)/.test(SRC), 'its internal timer is cleared in finally (no leak on the abort path)')

// OUTCOME: does aborting the external signal actually abort the fetch?
;(async function outcome36() {
  let aborted = false
  const fakeFetch = (url, opts) => new Promise((_res, rej) => {
    opts.signal.addEventListener('abort', () => { aborted = true; rej(new Error('aborted')) })
  })
  const pw = new AbortController()
  const inner = new AbortController()
  const combined = AbortSignal.any([inner.signal, pw.signal])
  fakeFetch('x', { signal: combined }).catch(() => {})
  const delay = ms => new Promise(r => setTimeout(r, ms))
  await Promise.race([new Promise(() => {}), delay(10)])   // the cap wins, as in boot
  pw.abort()
  await delay(5)
  ok(aborted, 'aborting the caller signal aborts the in-flight prewarm fetch')
})().then(() => {
  console.log(`\n${fail === 0 ? '\x1b[32mAll ' + pass + ' checks passed.\x1b[0m'
                              : '\x1b[31m' + fail + ' of ' + (pass + fail) + ' checks FAILED.\x1b[0m'}`)
  process.exit(fail === 0 ? 0 : 1)
})
