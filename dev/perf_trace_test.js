#!/usr/bin/env node
// Unit test for the P1 presence-latency trace (backlog #186).
//
// It extracts the SHIPPED block out of amadeus.html by its anchors and evals
// that text — never a hand-copied duplicate.  A copy would drift from the real
// code and pass while the app was broken (the byte-identical discipline that
// bugs.md 77 used on SYSTEM_PROMPT).
//
// The thing actually under test is turn OWNERSHIP: a turn that opens must
// always close or abort, because a leaked t0 silently inflates the next turn's
// headline number, and nothing on screen would ever show it.
//
// Run: node dev/perf_trace_test.js

const fs = require('fs')
const path = require('path')

const HTML = path.join(__dirname, '..', 'amadeus.html')
const START = '// ── P1: PRESENCE LATENCY TRACE'
const END = 'window.latencyReset='

function extractBlock() {
  const lines = fs.readFileSync(HTML, 'utf8').split('\n')
  const s = lines.findIndex(l => l.startsWith(START))
  const e = lines.findIndex(l => l.startsWith(END))
  if (s < 0 || e < 0) throw new Error('P1 block anchors not found in amadeus.html')
  return lines.slice(s, e + 1).join('\n')
}

// Build a sandbox with just enough browser surface for the block.
function makeEnv({ perfTrace = true, storageThrows = false, seed = null } = {}) {
  let now = 0
  const store = {}
  const logs = []
  // Pre-existing rows from an earlier launch. The block reads localStorage at
  // parse time, so this must be planted BEFORE the factory runs.
  if (seed !== null) store['amadeus_perf_v1'] = seed
  const env = {
    now: (v) => { now = v },
    logs,
    performance: { now: () => now },
    localStorage: {
      getItem: (k) => (k in store ? store[k] : null),
      setItem: (k, v) => { if (storageThrows) throw new Error('QuotaExceededError'); store[k] = v },
      removeItem: (k) => { delete store[k] },
    },
    console: { log: (...a) => logs.push(a.join(' ')), warn: () => {} },
    document: { createElement: () => ({ click() {} }) },
    Blob: function () {},
    URL: { createObjectURL: () => 'blob:x', revokeObjectURL: () => {} },
    window: {},
  }
  let src = extractBlock()
  if (!perfTrace) src = src.replace('const PERF_TRACE = true', 'const PERF_TRACE = false')
  // Expose the internals the test drives.  `eval` inside a function scope keeps
  // each case isolated — no shared module state between cases.
  const factory = new Function('performance', 'localStorage', 'console', 'document', 'Blob', 'URL', 'window',
    src + '\n;return {perfStart,perfStartIfIdle,perfAbort,perfMark,perfMarkOnce,perfField,perfEnd,' +
    'ring:_perfRing,status:window.latencyStatus,reset:window.latencyReset,PERF_MAX,PERF_TRACE}')
  env.api = factory(env.performance, env.localStorage, env.console, env.document, env.Blob, env.URL, env.window)
  env.store = store
  return env
}

let pass = 0, fail = 0
function check(name, cond, detail) {
  if (cond) { pass++; console.log('  \x1b[32m✓\x1b[0m ' + name) }
  else { fail++; console.log('  \x1b[31m✗\x1b[0m ' + name + (detail ? '  → ' + detail : '')) }
}

console.log('\nP1 presence-latency trace — unit tests\n')

// 1. Happy path: a full voice turn records one row with the headline number.
{
  const e = makeEnv()
  const a = e.api
  e.now(0);    a.perfStart('voice')
  e.now(600);  a.perfMark('stt')
  e.now(780);  a.perfMark('rag')
  e.now(1600); a.perfMarkOnce('genFirst')
  e.now(1700); a.perfMarkOnce('genFirst')      // later tokens must not move it
  e.now(2800); a.perfMark('genDone')
  e.now(4900); a.perfMark('ttsResp')
  a.perfField('translateMs', 870); a.perfField('fishMs', 1180)
  e.now(5000); a.perfMark('audio'); a.perfEnd()
  const r = e.api.ring[0]
  check('one turn recorded', e.api.ring.length === 1, 'got ' + e.api.ring.length)
  check('headline totalMs is speech-end → first audio', r && r.totalMs === 5000, r && r.totalMs)
  check('genFirst is set once, by the FIRST token', r && r.marks.genFirst === 1600, r && r.marks.genFirst)
  check('server durations stored', r && r.translateMs === 870 && r.fishMs === 1180)
  check('t0 is not persisted (it is meaningless across turns)', r && r.t0 === undefined)
  check('one console line printed per turn', e.logs.length === 1, 'lines=' + e.logs.length)
}

// 2. THE regression this file exists for: a discarded utterance must not leave
//    its clock running for the next turn.
{
  const e = makeEnv()
  const a = e.api
  e.now(0);    a.perfStart('voice')       // VAD fired
  e.now(700);  a.perfMark('stt')
  e.now(700);  a.perfAbort()              // Whisper no-speech gate discarded it
  e.now(60000); a.perfStartIfIdle('text') // a minute later he types instead
  e.now(62000); a.perfMark('audio'); a.perfEnd()
  const r = e.api.ring[0]
  check('discarded utterance records nothing', e.api.ring.length === 1, 'rows=' + e.api.ring.length)
  check('next turn is TEXT, not the abandoned voice turn', r && r.kind === 'text', r && r.kind)
  check('next turn does NOT inherit the stale t0', r && r.totalMs === 2000, r && r.totalMs)
}

// 3. sendMsg's catch closes the turn, so a failed reply cannot poison the next.
{
  const e = makeEnv()
  const a = e.api
  e.now(0);     a.perfStart('voice')
  e.now(3000);  a.perfEnd('sendMsg-error')
  e.now(10000); a.perfStartIfIdle('text')
  e.now(11000); a.perfEnd()
  check('failed turn is stored with its note', e.api.ring[0].note === 'sendMsg-error')
  check('turn after a failure starts its own clock', e.api.ring[1].totalMs === 1000, e.api.ring[1].totalMs)
}

// 4. perfEnd is idempotent — 'playing' firing twice must not double-record.
{
  const e = makeEnv()
  const a = e.api
  e.now(0); a.perfStart('voice')
  e.now(900); a.perfEnd()
  e.now(950); a.perfEnd()
  check('second perfEnd is a no-op', e.api.ring.length === 1, 'rows=' + e.api.ring.length)
}

// 5. Marks with no open turn are silently ignored (greeting audio, boot, BGM
//    all call playSyncedAudio without a turn ever being started).
{
  const e = makeEnv()
  const a = e.api
  a.perfMark('audio'); a.perfField('fishMs', 10); a.perfEnd()
  check('marks outside a turn record nothing', e.api.ring.length === 0, 'rows=' + e.api.ring.length)
}

// 6. A full localStorage must never throw into the caller — ttsSpeak's failures
//    reaching sendMsg's catch would run history.pop() and corrupt the chat.
{
  const e = makeEnv({ storageThrows: true })
  const a = e.api
  let threw = false
  try { e.now(0); a.perfStart('voice'); e.now(100); a.perfEnd() } catch (err) { threw = true }
  check('perfEnd survives a full localStorage', !threw)
  check('the turn is still held in memory', e.api.ring.length === 1)
}

// 7. The kill switch really kills.
{
  const e = makeEnv({ perfTrace: false })
  const a = e.api
  e.now(0); a.perfStart('voice'); a.perfStartIfIdle('text')
  e.now(500); a.perfMark('audio'); a.perfEnd()
  check('PERF_TRACE=false records nothing', e.api.ring.length === 0, 'rows=' + e.api.ring.length)
  check('PERF_TRACE=false writes no console line', e.logs.length === 0)
  check('PERF_TRACE=false writes no localStorage key', Object.keys(e.store).length === 0)
}

// 8. The ring is bounded, so the localStorage footprint cannot grow forever.
{
  const e = makeEnv()
  const a = e.api
  for (let i = 0; i < a.PERF_MAX + 25; i++) { e.now(i * 10); a.perfStart('text'); e.now(i * 10 + 5); a.perfEnd() }
  check('ring is capped at PERF_MAX', e.api.ring.length === a.PERF_MAX, 'len=' + e.api.ring.length)
  const bytes = e.store['amadeus_perf_v1'].length
  check('full ring stays small in localStorage (<80KB)', bytes < 80000, bytes + ' bytes')
  console.log('    (measured: ' + bytes + ' bytes for ' + a.PERF_MAX + ' turns)')
}

// 9. sendMsg's early returns (empty text / isLoading / diary overlay) drop an
//    open voice turn.  Without this, an utterance that never becomes a reply
//    leaves its clock running and the NEXT text turn reports a false wait.
{
  const e = makeEnv()
  const a = e.api
  e.now(0);     a.perfStart('voice')     // he spoke
  e.now(800);   a.perfMark('stt')
  e.now(800);   a.perfAbort()            // sendMsg early-returned (isLoading)
  e.now(45000); a.perfStartIfIdle('text')
  e.now(46200); a.perfEnd()
  check('turn stranded by an early return is dropped', e.api.ring.length === 1)
  check('following text turn times only itself', e.api.ring[0].totalMs === 1200, e.api.ring[0].totalMs)
}

// 10. latencyStatus reports per-stage deltas, not raw offsets.
{
  const e = makeEnv()
  const a = e.api
  for (let i = 0; i < 3; i++) {
    e.now(0); a.perfStart('voice')
    e.now(500); a.perfMark('stt')
    e.now(700); a.perfMark('rag')
    e.now(1500); a.perfMark('genFirst')
    e.now(2500); a.perfMark('genDone')
    e.now(4000); a.perfMark('ttsResp')
    e.now(4100); a.perfMark('audio'); a.perfEnd()
  }
  const s = a.status()
  check('stt is an absolute offset', s.stt.median === 500, s.stt && s.stt.median)
  check('rag is a DELTA, not an offset', s.rag.median === 200, s.rag && s.rag.median)
  check('tts_round_trip is a delta', s.tts_round_trip.median === 1500, s.tts_round_trip && s.tts_round_trip.median)
  check('headline median reported', s.total_you_to_her.median === 4100)
  check('filtering by kind works', a.status('text') === 'no turns recorded yet')
}

// 11. A TEXT turn has no 'stt' mark, and its RAG stage must still be reported.
//     Found live on 2026-09-06 at n=4: latencyStatus() printed `rag: null` for
//     every typed turn while the raw dump held marks.rag = 91..120ms.  The mark
//     was fine; the DELTA subtracted a stage that text turns never have.
//     Shape below is one of Zani's real rows.
{
  const e = makeEnv()
  const a = e.api
  e.now(0);    a.perfStart('text')
  e.now(120);  a.perfMark('rag')
  e.now(1185); a.perfMark('genFirst')
  e.now(2730); a.perfMark('genDone')
  e.now(5589); a.perfMark('ttsResp')
  a.perfField('promptTokens', 4151); a.perfField('evalCount', 44)
  e.now(5592); a.perfMark('audio'); a.perfEnd()
  const s = a.status()
  check('text turn reports a RAG stage (was null)', s.rag && s.rag.median === 120, s.rag && s.rag.median)
  check('text turn reports no STT stage', s.stt === null, JSON.stringify(s.stt))
  check('later stages still need a real predecessor', s.think_to_1st_tok.median === 1065)
  check('prompt tokens reported', s.prompt_tokens.median === 4151)
  check('generated tokens reported', s.generated_tokens.median === 44)
}

// 12. A VOICE turn keeps measuring RAG from the STT mark, not from t0.
{
  const e = makeEnv()
  const a = e.api
  e.now(0);   a.perfStart('voice')
  e.now(600); a.perfMark('stt')
  e.now(700); a.perfMark('rag')
  e.now(900); a.perfMark('audio'); a.perfEnd()
  const s = a.status()
  check('voice RAG is measured from stt, not from t0', s.rag.median === 100, s.rag && s.rag.median)
}

// 13. Turns SURVIVE a relaunch. The ring is read back from localStorage at load,
//     so n accumulates across launches and Zani does not have to reach n>=30 in
//     one sitting. Seeded with two of his real rows from 2026-09-06.
{
  const prior = JSON.stringify([
    { kind: 'text', at: '2026-09-06T09:40:02.384Z', marks: { rag: 106, genFirst: 1765, genDone: 2885, ttsResp: 4622, audio: 4624 }, prefillMs: 1594, promptTokens: 3884, evalCount: 30, translateMs: 855, fishMs: 872, translator: 'gemma4', totalMs: 4624 },
    { kind: 'text', at: '2026-09-06T09:40:26.499Z', marks: { rag: 95, genFirst: 989, genDone: 2360, ttsResp: 4671, audio: 4673 }, prefillMs: 855, promptTokens: 3946, evalCount: 40, translateMs: 1270, fishMs: 1036, translator: 'gemma4', totalMs: 4673 },
  ])
  const e = makeEnv({ seed: prior })
  const a = e.api
  check('previous launches are loaded back in', a.ring.length === 2, 'len=' + a.ring.length)
  check('their numbers survive intact', a.status().total_you_to_her.n === 2)
  e.now(0); a.perfStart('voice')
  e.now(4000); a.perfMark('audio'); a.perfEnd()
  check('a new turn appends to them, it does not replace them', a.ring.length === 3, 'len=' + a.ring.length)
  check('n counts every launch together', a.status().turns === 3)
  check('the old rows are still first', a.ring[0].totalMs === 4624)
}

// 14. Corrupt or half-written storage must not lose the session or crash the
//     boot — the block runs during page parse, so a throw here is a dead app.
{
  let threw = false, ring = null
  try { ring = makeEnv({ seed: '{not valid json' }).api.ring } catch (err) { threw = true }
  check('corrupt storage does not crash the load', !threw)
  check('corrupt storage starts from empty', ring && ring.length === 0)
  const wrongShape = makeEnv({ seed: '{"turns":5}' }).api.ring
  check('a non-array in storage is rejected', wrongShape.length === 0)
}

// 15. latencyStatus('voice') must cover EVERY voice kind. Exact equality told
//     Zani "no turns recorded yet" after a real conversation (2026-09-07),
//     because the manual mic path records 'voice-tap' and the fallback engine
//     records 'voice-rms'. A filter that hides data reads as data loss.
{
  const e = makeEnv()
  const a = e.api
  for (const kind of ['voice', 'voice-rms', 'voice-tap', 'text']) {
    e.now(0); a.perfStart(kind)
    e.now(500); a.perfMark('stt')
    e.now(3000); a.perfMark('audio'); a.perfEnd()
  }
  check('voice filter covers voice + voice-rms + voice-tap', a.status('voice').turns === 3,
    'got ' + a.status('voice').turns)
  check('it does NOT sweep in text turns', a.status('text').turns === 1)
  check('unfiltered still counts everything', a.status().turns === 4)
  check('an exact kind still selects just itself', a.status('voice-tap').turns === 1)
}

console.log('\n' + (fail === 0
  ? '\x1b[32mAll ' + pass + ' checks passed.\x1b[0m\n'
  : '\x1b[31m' + fail + ' FAILED, ' + pass + ' passed.\x1b[0m\n'))
process.exit(fail === 0 ? 0 : 1)
