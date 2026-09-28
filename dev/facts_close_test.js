/*
 * dev/facts_close_test.js — the once-per-session facts pass at close (backlog #202).
 * Run:  node dev/facts_close_test.js
 *
 * Every function under test is EXTRACTED FROM THE SHIPPED amadeus.html / main.js by
 * anchor, never retyped. If an anchor moves, the test exits 2 instead of testing a
 * stale copy. It tests the OUTCOME (CLAUDE.md 50): after a close with a fact in the
 * reply, the fact is IN the store — not merely "my function was called".
 * It also plants 3 mutants and requires each one to be caught, so the checks have teeth.
 */
const fs=require('fs'), EventEmitter=require('events')
const ROOT='/Users/zha61/Documents/Amadeus/'
const html=fs.readFileSync(ROOT+'amadeus.html','utf8'), mainSrc=fs.readFileSync(ROOT+'main.js','utf8')
const cut=(src,a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);if(i<0||j<0){console.error('ANCHOR MISSING: '+a+' … '+b);process.exit(2)}return src.slice(i,j)}
const line=(src,re)=>{const m=src.match(re);if(!m){console.error('ANCHOR MISSING: '+re);process.exit(2)}return m[0]+'\n'}

const BASE = cut(html,'let _factsAbort=null','function noteActivity(){')
  + cut(html,'function noteActivity(){','function maybeFireProactive')
  + line(html,/const FACTS_KEY\s*=.*/) + line(html,/const FACTS_MAX\s*=.*/)
  + line(html,/function loadFacts\(\)\{.*/) + line(html,/function saveFacts\(f\)\{.*/)
  + cut(html,'let _factsExchangeCount','function _normFact')
  + cut(html,'function _normFact','// DEV: inspect the fact store')
const HANDLER = cut(html,'  if (window.electronAPI.onRunFactsExtraction) {','  // ── end facts close handler')
const MAINSTEP = cut(mainSrc,'    // Step 5 (backlog #202)','  } finally {\n    diaryInProgress = false')

function fakeStorage(throwing){
  const m=new Map()
  return throwing
    ? {getItem(){throw new Error('denied')},setItem(){throw new Error('quota')},removeItem(){throw new Error('denied')}}
    : {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k),_m:m}
}
const H=n=>Array.from({length:n},(_,i)=>({role:i%2?'assistant':'user',content:i%2?'[EMOTION:smug] Hmph.':'message '+i}))

// Build one isolated page instance. mutate(code) lets a mutant replace shipped text.
function page({history=H(4),fetchImpl,storage=fakeStorage(),mutate=x=>x,timeoutMs=null}={}){
  let code=BASE+HANDLER
  if(timeoutMs!=null) code=code.replace(/const FACTS_CLOSE_TIMEOUT_MS\s*=\s*\d+/,'const FACTS_CLOSE_TIMEOUT_MS = '+timeoutMs)
  code=mutate(code)
  const api={doneCount:0,cb:null,
    onRunFactsExtraction(cb){api.cb=cb}, factsExtractionDone(){api.doneCount++}}
  const env={history, FACTS_EXTRACT_EVERY:6, OLLAMA_MODEL:'gemma4:latest',
    isLoading:false,isRecording:false,isTranscribing:false,studyActive:false,hf:{active:false},
    _lastActivityTs:0,_warmAbort:null,idleTimer:null,proactiveCount:0,proactiveAbort:null,idleSystemOn:false,
    _localDateStr:()=>'2026-09-27', document:{hidden:false,getElementById:()=>null},
    scheduleIdleCheck:()=>{}, localStorage:storage, window:{electronAPI:api},
    console:{log(){},warn(){},error(){},table(){}}}
  const names=Object.keys(env), out={}
  new Function(...names,'fetch','out',`${code}
    out.extractFactsNow=extractFactsNow; out.noteActivity=noteActivity; out.parse=_parseFactsJson;
    out.st=()=>({extracting:_factsExtracting,abort:_factsAbort}); out.setExtracting=v=>{_factsExtracting=v}`)
    (...names.map(k=>env[k]), fetchImpl, out)
  out.api=api; out.storage=storage
  out.facts=()=>{try{return JSON.parse(storage.getItem('amadeus_facts_v1')||'null')}catch(e){return 'THREW'}}
  out.runs=()=>{try{return JSON.parse(storage.getItem('amadeus_facts_runs_v1')||'[]')}catch(e){return []}}
  return out
}
const reply=content=>{const calls=[];const f=async(url,opts)=>{calls.push(JSON.parse(opts.body));f.signal=opts.signal;return{json:async()=>({message:{content},eval_count:42,done_reason:'stop'})}};f.calls=calls;return f}
const FACT2='{"facts":[{"fact":"Zani has a piano exam on 14 October","category":"event","event_date":"2026-10-14","replaces":null},{"fact":"Zani switched to Project Sekai","category":"preference","event_date":null,"replaces":null}]}'

// ── the checks, as functions, so each mutant can be run through the SAME checks ──
async function runChecks(mutate=x=>x){
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  { // parser units
    const p=page({fetchImpl:reply('{}'),mutate}).parse
    const v=p(FACT2); t('parse: valid JSON → 2 facts, not salvaged', v&&v.facts.length===2&&!v.salvaged)
    const cutMid=FACT2.slice(0,FACT2.indexOf('Project')+3)
    const s=p(cutMid); t('parse: cut inside 2nd fact → 1 closed fact kept', s&&s.facts.length===1&&s.salvaged&&/piano/.test(s.facts[0].fact))
    const br='{"facts":[{"fact":"a } { b \\" c","category":"other"},{"fact":"x {'
    const b=p(br); t('parse: braces/escaped quote inside a string handled', b&&b.facts.length===1&&b.facts[0].fact==='a } { b " c')
    t('parse: cut before any closed fact → null', p('{"facts":[{"fact":"half')===null)
    t('parse: facts not an array → null', p('{"facts":{"fact":"x"}}')===null)
    t('parse: garbage / empty → null', p('nope')===null&&p('')===null)
    const f=p('{"facts":[1,null,"s",{"fact":"ok"}]}'); t('parse: non-object items dropped', f&&f.facts.length===1)
  }
  { // OUTCOME: a close with a fact in the reply puts the fact IN the store
    const f=reply(FACT2), pg=page({fetchImpl:f,mutate})
    await pg.api.cb(); const st=pg.facts()||[]
    t('OUTCOME: both facts are in amadeus_facts_v1 after close', st.length===2&&st.some(x=>/piano exam/.test(x.fact)))
    t('close: done sent exactly once', pg.api.doneCount===1)
    t('close: request uses num_predict 800, num_ctx 8192, think false', f.calls[0]&&f.calls[0].options.num_predict===800&&f.calls[0].options.num_ctx===8192&&f.calls[0].think===false)
    const run=pg.runs().pop()||{}; t('close: run log says close/ok/n=2', run.trigger==='close'&&run.outcome==='ok'&&run.n===2&&run.evalCount===42)
    t('close: state reset', pg.st().extracting===false)
  }
  { // truncated reply: the closed fact is kept, the fragment is never stored
    const pg=page({fetchImpl:reply(FACT2.slice(0,FACT2.indexOf('Project')+3)),mutate})
    await pg.api.cb(); const st=pg.facts()||[]
    t('truncated: closed fact stored, fragment NOT stored', st.length===1&&/piano/.test(st[0].fact))
    t('truncated: run log marks salvaged', (pg.runs().pop()||{}).salvaged===true)
  }
  { const pg=page({fetchImpl:reply('{"facts":[]}'),mutate}); await pg.api.cb()
    t('empty: store untouched, outcome empty, done x1', pg.facts()===null&&(pg.runs().pop()||{}).outcome==='empty'&&pg.api.doneCount===1) }
  { const pg=page({fetchImpl:async()=>{throw new Error('ECONNREFUSED')},mutate}); await pg.api.cb()
    t('error: outcome error, done x1, state reset', (pg.runs().pop()||{}).outcome==='error'&&pg.api.doneCount===1&&!pg.st().extracting) }
  { const hang=(u,o)=>new Promise((_,rej)=>o.signal.addEventListener('abort',()=>{const e=new Error('a');e.name='AbortError';rej(e)}))
    const pg=page({fetchImpl:hang,timeoutMs:30,mutate}); await pg.api.cb()
    t('timeout: own timer ends it, outcome timeout, done x1', (pg.runs().pop()||{}).outcome==='timeout'&&pg.api.doneCount===1&&!pg.st().extracting) }
  { const f=reply(FACT2), pg=page({fetchImpl:f,mutate}); pg.setExtracting(true); await pg.api.cb()
    t('in-flight idle run: close skips, no fetch, done x1', f.calls.length===0&&(pg.runs().pop()||{}).outcome==='skipped-inflight'&&pg.api.doneCount===1) }
  { const pg=page({history:H(2),fetchImpl:reply(FACT2),mutate}); await pg.api.cb()
    t('short history: skipped-short, done x1', (pg.runs().pop()||{}).outcome==='skipped-short'&&pg.api.doneCount===1) }
  { // noteActivity() must NOT stop the close pass
    let release; const gate=new Promise(r=>release=r); let aborted=false
    const f=async(u,o)=>{o.signal.addEventListener('abort',()=>aborted=true); await gate; if(aborted){const e=new Error('a');e.name='AbortError';throw e}; return {json:async()=>({message:{content:FACT2}})}}
    const pg=page({fetchImpl:f,mutate}); const p=pg.api.cb(); await new Promise(r=>setImmediate(r))
    pg.noteActivity(); release(); await p
    t('noteActivity during close pass does not abort it', !aborted&&(pg.facts()||[]).length===2)
  }
  { const pg=page({fetchImpl:reply(FACT2),storage:fakeStorage(true),mutate}); let threw=false
    try{ await pg.api.cb() }catch(e){ threw=true }
    t('localStorage throwing: no throw, done x1', !threw&&pg.api.doneCount===1) }
  { const long=Array.from({length:80},(_,i)=>({role:i%2?'assistant':'user',content:(i%2?'[EMOTION:calm] reply ':'long message ')+'x'.repeat(90)+i}))
    const f=reply('{"facts":[]}'), pg=page({history:long,fetchImpl:f,mutate}); await pg.api.cb()
    const conv=(f.calls[0].messages[1].content.split('CONVERSATION:\n')[1])||''
    t('window: ≤4800 chars and starts on a whole line', conv.length<=4800&&/^(Zani|Kurisu): /.test(conv)&&conv.endsWith('79')) }
  { // idle pass unchanged: 500, and noteActivity still aborts it and re-queues
    const hang=(u,o)=>new Promise((_,rej)=>o.signal.addEventListener('abort',()=>{const e=new Error('a');e.name='AbortError';rej(e)}))
    const calls=[]; const f=(u,o)=>{calls.push(JSON.parse(o.body));return hang(u,o)}
    const pg=page({fetchImpl:f,mutate}); const p=pg.extractFactsNow(); await new Promise(r=>setImmediate(r))
    pg.noteActivity(); await p
    t('idle pass: num_predict 500, abortable by noteActivity', calls[0].options.num_predict===500&&(pg.runs().pop()||{}).outcome==='aborted') }
  return r
}

async function mainChecks(){
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  const run=async({factsClose,reply,destroyed=false,waitMs=60})=>{
    const ipcMain=new EventEmitter(); let sent=0
    const mainWindow={isDestroyed:()=>destroyed,webContents:{send:ch=>{if(ch==='run-facts-extraction'){sent++; if(reply) setTimeout(()=>ipcMain.emit('facts-extraction-done'),5)}}}}
    const data={conv:'x',factsClose}
    const fn=new Function('ipcMain','mainWindow','data','FACTS_CLOSE_WAIT_MS','console',`return (async()=>{ ${MAINSTEP} })()`)
    const t0=Date.now(); await fn(ipcMain,mainWindow,data,waitMs,{warn(){},log(){}})
    return {ms:Date.now()-t0,sent,left:ipcMain.listenerCount('facts-extraction-done')}
  }
  let o=await run({factsClose:true,reply:true}); t('main: reply → resolves early, sent once, no listener left', o.ms<50&&o.sent===1&&o.left===0)
  o=await run({factsClose:true,reply:false}); t('main: no reply → resolves at the wait, listener removed', o.ms>=55&&o.sent===1&&o.left===0)
  o=await run({factsClose:undefined,reply:true}); t('main: page without factsClose → step skipped', o.sent===0&&o.ms<20)
  o=await run({factsClose:true,reply:true,destroyed:true}); t('main: destroyed window → no send, no listener', o.sent===0&&o.left===0)
  t('page: conversation payload declares factsClose:true', /sendConversation\(\{[^}]*factsClose:\s*true/.test(html))
  t('preload: both channels exposed', /onRunFactsExtraction[\s\S]*'run-facts-extraction'/.test(fs.readFileSync(ROOT+'preload.js','utf8'))&&/factsExtractionDone[\s\S]*'facts-extraction-done'/.test(fs.readFileSync(ROOT+'preload.js','utf8')))
  return r
}

;(async()=>{
  const shipped=[...await runChecks(), ...await mainChecks()]
  let fail=0
  for(const [n,ok] of shipped){ console.log((ok?'  PASS  ':'  FAIL  ')+n); if(!ok)fail++ }
  // Mutants: each must make at least one check FAIL.
  const mutants={
    'done() removed from finally':c=>c.replace('finally { done() }','finally { }'),
    'close pass abortable by noteActivity':c=>c.replace("else _factsAbort=ctl","_factsAbort=ctl"),
    'salvage disabled':c=>c.replace("if(!m) return null","return null"),
  }
  let caught=0
  for(const [name,mut] of Object.entries(mutants)){
    const probe=mut(BASE+HANDLER); if(probe===BASE+HANDLER){ console.log('  MUTANT DID NOT APPLY: '+name); fail++; continue }
    const res=await runChecks(mut); const hit=res.some(([,ok])=>!ok)
    console.log((hit?'  CAUGHT  ':'  MISSED  ')+'mutant: '+name); hit?caught++:fail++
  }
  console.log(`\n${shipped.length-shipped.filter(([,o])=>!o).length}/${shipped.length} checks passed, ${caught}/${Object.keys(mutants).length} mutants caught`)
  process.exit(fail?1:0)
})()
