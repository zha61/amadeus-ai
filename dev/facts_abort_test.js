/*
 * dev/facts_abort_test.js — extractFactsNow's abort path (bugs.md 74 / CLAUDE.md 37b).
 * Run:  node dev/facts_abort_test.js
 *
 * The functions are EXTRACTED FROM THE SHIPPED amadeus.html at run time, never
 * retyped, and driven with a stubbed fetch — so this exercises the real control flow.
 *
 * What it protects: aborting must yield the GPU WITHOUT losing the harvest. A naive
 * abort would silently drop facts, which is the exact defect bugs.md 73 removed.
 */
const fs=require('fs')
const src=fs.readFileSync('/Users/zha61/Documents/Amadeus/amadeus.html','utf8')
const cut=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b);if(i<0||j<0)throw new Error('extract failed: '+a);return src.slice(i,j)}

const code = cut('let _factsAbort=null','function noteActivity(){')
  + cut('function noteActivity(){','function maybeFireProactive')
  + cut('let _factsExchangeCount','function _normFact')   // state + scheduler + extractFactsNow

const env = {
  history:[{role:'user',content:'a'},{role:'assistant',content:'b'},{role:'user',content:'c'},{role:'assistant',content:'d'}],
  FACTS_EXTRACT_EVERY:6, FACTS_IDLE_MS:45000, OLLAMA_MODEL:'gemma4:latest',
  isLoading:false,isRecording:false,isTranscribing:false,studyActive:false,hf:{active:false},
  _lastActivityTs:0, _greetingWarmStarted:false, _warmAbort:null,
  idleTimer:null, proactiveCount:0, proactiveAbort:null, idleSystemOn:false,
  loadFacts:()=>[], _localDateStr:()=>'2026-08-26',
  document:{hidden:true,getElementById:()=>null},
  scheduleIdleCheck:()=>{}, mergeFacts:f=>{env._merged=f}, _merged:null,
}
const names=Object.keys(env)
const make=new Function(...names,'fetchImpl','out', `
  const fetch = fetchImpl;
  ${code}
  out.extractFactsNow = extractFactsNow;
  out.noteActivity = noteActivity;
  out.state = () => ({ due:_factsDue, extracting:_factsExtracting, abort:_factsAbort });
  out.setDue = v => { _factsDue = v };
`)

let pass=0,fail=0
const t=(n,c)=>{c?(pass++,console.log('  PASS  '+n)):(fail++,console.log('  FAIL  '+n))}
const logs=[]; const realLog=console.log, realWarn=console.warn
const capture=()=>{console.log=(...a)=>logs.push(a.join(' ')); console.warn=(...a)=>logs.push(a.join(' '))}
const restore=()=>{console.log=realLog; console.warn=realWarn}

;(async()=>{
// ---- 1. HAPPY PATH: facts merge, state resets
{
  const out={}
  make(...names.map(k=>env[k]), async()=>({json:async()=>({message:{content:'{"facts":[{"fact":"Zani has an exam","category":"event"}]}'}})}), out)
  capture(); await out.extractFactsNow(); restore()
  t('happy path merges facts', env._merged && env._merged.length===1)
  t('happy path clears _factsExtracting', out.state().extracting===false)
  t('happy path clears _factsAbort', out.state().abort===null)
}
// ---- 2. ABORT PATH: noteActivity() cancels an in-flight extraction
{
  const out={}; env._merged=null
  const fetchImpl=(url,opts)=>new Promise((_,rej)=>{
    opts.signal.addEventListener('abort',()=>{const e=new Error('aborted');e.name='AbortError';rej(e)})
  })
  make(...names.map(k=>env[k]), fetchImpl, out)
  logs.length=0; capture()
  const p=out.extractFactsNow()
  await new Promise(r=>setImmediate(r))
  t('extraction is in flight', out.state().extracting===true && out.state().abort!==null)
  out.noteActivity()                       // <-- Zani starts typing
  await p; restore()
  t('abort does NOT throw out of extractFactsNow', true)
  t('abort re-queues the harvest (_factsDue)', out.state().due===true)
  t('abort clears _factsExtracting', out.state().extracting===false)
  t('abort clears _factsAbort', out.state().abort===null)
  t('abort does NOT merge partial facts', env._merged===null)
  t('abort logs the distinct yield message', logs.some(l=>/yielded to activity/.test(l)))
  t('abort does NOT log a failure warning', !logs.some(l=>/extraction failed/.test(l)))
}
// ---- 3. REAL FAILURE is still reported as a failure
{
  const out={}; env._merged=null
  make(...names.map(k=>env[k]), async()=>{throw new Error('connection refused')}, out)
  logs.length=0; capture(); await out.extractFactsNow(); restore()
  t('real failure logs the warning', logs.some(l=>/extraction failed/.test(l)))
  t('real failure does NOT re-queue', out.state().due===false)
  t('real failure clears _factsExtracting', out.state().extracting===false)
}
// ---- 4. noteActivity() is safe when nothing is running (every keystroke path)
{
  const out={}
  make(...names.map(k=>env[k]), async()=>({json:async()=>({message:{content:'{}'}})}), out)
  let threw=false
  try{ for(let i=0;i<50;i++) out.noteActivity() }catch(e){ threw=true }
  t('noteActivity x50 with no extraction never throws', !threw)
}
console.log(`\n${pass} passed, ${fail} failed`)
process.exit(fail?1:0)
})()
