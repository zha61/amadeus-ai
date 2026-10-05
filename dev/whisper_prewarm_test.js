// dev/whisper_prewarm_test.js — backlog #226b: BOTH voice entry points ask Whisper to load when the
// mic opens, and the prewarm can never throw into its caller (CLAUDE.md 48a, bugs.md 80).
// Extracts the SHIPPED code from amadeus.html by anchor. Run: node dev/whisper_prewarm_test.js
const fs = require('fs'), path = require('path')
const SRC = fs.readFileSync(path.join(__dirname, '..', 'amadeus.html'), 'utf8')

function fnBody(src, header) {
  const i = src.indexOf(header)
  if (i < 0) throw new Error('anchor not found: ' + header)
  let d = 0, j = src.indexOf('{', i)
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++
    else if (src[k] === '}' && --d === 0) return src.slice(i, k + 1)
  }
  throw new Error('unbalanced: ' + header)
}

function run(src) {
  let fails = 0
  const check = (name, ok) => { console.log((ok ? '  ok   ' : '  FAIL ') + name); if (!ok) fails++ }
  let pre, sr, hs
  try {
    pre = fnBody(src, 'function whisperPrewarm(){')
    sr = fnBody(src, 'async function startRecording(){')
    hs = fnBody(src, 'async function hfStart(){')
  } catch (e) { console.log('  FAIL ' + e.message); return 1 }
  check('tap-to-talk (startRecording) calls whisperPrewarm()', /\n\s*whisperPrewarm\(\)/.test(sr))
  check('hands-free (hfStart) calls whisperPrewarm()', /\n\s*whisperPrewarm\(\)/.test(hs))
  check('neither entry point AWAITS it', !/await\s+whisperPrewarm/.test(sr + hs))
  check('it POSTs to Whisper /warm', /fetch\('http:\/\/127\.0\.0\.1:5004\/warm',\{method:'POST'\}\)/.test(pre))
  const make = (fetchImpl) => new Function('fetch', pre + '\nreturn whisperPrewarm')(fetchImpl)
  let threw = false
  try { make(() => { throw new Error('sync boom') })() } catch (e) { threw = true }
  check('a fetch that THROWS does not escape', !threw)
  let unhandled = false
  const onU = () => { unhandled = true }
  process.on('unhandledRejection', onU)
  let rv
  try { rv = make(() => Promise.reject(new Error('refused')))() } catch (e) { threw = true }
  return new Promise(r => setTimeout(() => {
    process.off('unhandledRejection', onU)
    check('a REJECTED fetch is caught (no unhandled rejection)', !unhandled && !threw)
    check('it returns nothing to await', rv === undefined)
    r(fails)
  }, 50))
}

const MUTANTS = [
  ['hfStart call removed', "  hf.active=true\n  whisperPrewarm()   // #226b\n", "  hf.active=true\n"],
  ['startRecording call removed', "  whisperPrewarm()   // #226b\n`", null],
  ['try removed', "  try{ fetch('http://127.0.0.1:5004/warm',{method:'POST'}).catch(()=>{}) }catch(e){}",
   "  fetch('http://127.0.0.1:5004/warm',{method:'POST'}).catch(()=>{})"],
  ['catch removed', "fetch('http://127.0.0.1:5004/warm',{method:'POST'}).catch(()=>{})",
   "fetch('http://127.0.0.1:5004/warm',{method:'POST'})"],
]
;(async () => {
  const fails = await run(SRC)
  console.log(`\nshipped: ${fails === 0 ? 'all 7 checks passed' : fails + ' FAILED'}`)
  let missed = 0, n = 0
  for (const [name, a, b] of MUTANTS) {
    let mut
    if (b === null) {   // remove the call that sits right after the mic-denied line in startRecording
      const anchor = "Mic access denied'; return }\n  whisperPrewarm()   // #226b\n"
      if (!SRC.includes(anchor)) { console.log('  MUTANT NOT APPLIED: ' + name); missed++; n++; continue }
      mut = SRC.replace(anchor, "Mic access denied'; return }\n")
    } else {
      if (SRC.split(a).length !== 2) { console.log('  MUTANT NOT APPLIED: ' + name); missed++; n++; continue }
      mut = SRC.replace(a, b)
    }
    n++
    const log = console.log; console.log = () => {}
    const f = await run(mut)
    console.log = log
    console.log(`  ${f > 0 ? 'caught' : 'MISSED'}  ${name}`)
    if (f === 0) missed++
  }
  console.log(`${n - missed}/${n} mutants caught`)
  process.exit(fails || missed ? 1 : 0)
})()
