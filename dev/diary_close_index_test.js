/*
 * dev/diary_close_index_test.js — the close-time diary re-index is gone (backlog #218, bugs.md 95).
 * Run:  node dev/diary_close_index_test.js        (<1 s, pure CPU, no model call)
 *
 * The onSaveDiarySummary handler used to ack main and THEN fire an unawaited /index-diary
 * fetch, which raced the quit.  The boot index reconciles the entry instead.
 * The shipped handler is EXTRACTED FROM amadeus.html by anchor (exit 2 if one moves).
 * OUTCOME checks: the summary is still saved, main is acked exactly once on every path
 * (a lost ack costs main a 3 s wait at close), and nothing is indexed or fetched at close;
 * both boot paths still run the reconciling index.
 * Plants 3 mutants; each must be caught.
 */
const fs=require('fs'), path=require('path')
const html=fs.readFileSync(path.join(__dirname,'..','amadeus.html'),'utf8')
const cut=(src,a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);if(i<0||j<0){console.error('ANCHOR MISSING: '+a+' … '+b);process.exit(2)}return src.slice(i,j)}
const HANDLER=cut(html,'  if (window.electronAPI.onSaveDiarySummary) {','\n  // Main → renderer: user accepted an incoming call')
const BOOT_IC=cut(html,"setTimeout(() => ttsGreeting(gIC[0], gIC[1]), 500)","return  // ← incoming call path complete")
const BOOT=cut(html,"setTimeout(()=>ttsGreeting(g[0],g[1],greetingAudioPromise),500)","startIdleSystem()")

function run(src,payload,setItemThrows=false){
  const store={}, calls={ack:0,index:0,fetch:0,warn:0}; let cb=null
  const window={electronAPI:{onSaveDiarySummary:f=>{cb=f},diarySummarySaved:()=>calls.ack++}}
  const localStorage={setItem:(k,v)=>{if(setItemThrows)throw new Error('quota');store[k]=v}}
  new Function('window','localStorage','indexDiaryInBackground','fetch','console',src)(
    window,localStorage,()=>calls.index++,()=>{calls.fetch++;return Promise.resolve()},{warn:()=>calls.warn++,log(){}})
  if(!cb) return {calls,store,registered:false}
  cb(payload); return {calls,store,registered:true}
}

function checks(M={}){
  const h=M.handler||HANDLER, bic=M.bootIC||BOOT_IC, b=M.boot||BOOT
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  const ok=run(h,{summary:'I remember him.',watermark:'abc123'})
  t('handler registered', ok.registered)
  t('normal payload: summary AND watermark saved', ok.store.amadeus_diary_summary==='I remember him.'&&ok.store.amadeus_diary_summary_watermark==='abc123')
  t('normal payload: main acked exactly once', ok.calls.ack===1)
  t('normal payload: NO index call and NO fetch at close', ok.calls.index===0&&ok.calls.fetch===0)
  const bad=run(h,{summary:'x',watermark:'w'},true)
  t('setItem throws: warned, still acked exactly once, no index', bad.calls.warn===1&&bad.calls.ack===1&&bad.calls.index===0&&bad.calls.fetch===0)
  const none=run(h,null)
  t('empty payload: nothing written, acked once, no index', Object.keys(none.store).length===0&&none.calls.ack===1&&none.calls.index===0)
  t('boot (normal): still calls indexDiaryInBackground()', /\bindexDiaryInBackground\(\)/.test(b))
  t('boot (incoming call): still calls indexDiaryInBackground()', /\bindexDiaryInBackground\(\)/.test(bic))
  return r
}

const res=checks(); let fail=0
for(const [n,ok] of res){ console.log((ok?'  PASS  ':'  FAIL  ')+n); if(!ok)fail++ }
const mutants={
  'index call added back at close':{handler:HANDLER.replace('window.electronAPI.diarySummarySaved()','window.electronAPI.diarySummarySaved()\n        indexDiaryInBackground()')},
  'ack removed':{handler:HANDLER.replace('window.electronAPI.diarySummarySaved()','void 0')},
  'normal boot index removed':{boot:BOOT.replace('indexDiaryInBackground()','void 0')},
}
let caught=0
for(const [name,m] of Object.entries(mutants)){
  const k=Object.keys(m)[0], orig={handler:HANDLER,bootIC:BOOT_IC,boot:BOOT}[k]
  if(m[k]===orig){ console.log('  MUTANT DID NOT APPLY: '+name); fail++; continue }
  const hit=checks(m).some(([,ok])=>!ok)
  console.log((hit?'  CAUGHT  ':'  MISSED  ')+'mutant: '+name); hit?caught++:fail++
}
console.log(`\n${res.length-res.filter(([,o])=>!o).length}/${res.length} checks passed, ${caught}/${Object.keys(mutants).length} mutants caught`)
process.exit(fail?1:0)
