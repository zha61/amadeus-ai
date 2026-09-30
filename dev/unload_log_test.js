/*
 * dev/unload_log_test.js — the unload log lines (backlog #219).
 * Run:  node dev/unload_log_test.js        (<1 s, pure CPU, no model call)
 *
 * At close, beforeunload clears every media src.  That fired the BGM onerror ("BGM track not
 * found" — false, and it then STARTED the next track after audioCtx.close()) and the boot-video
 * trail's 'error' line.  The fix: a _pageUnloading flag set FIRST in beforeunload.
 * The shipped code is EXTRACTED FROM amadeus.html by anchor (exit 2 if one moves).
 * OUTCOME checks: the flag is already true at the moment a src is cleared; during unload a BGM
 * error writes no line and creates no Audio; outside unload the old skip still works.
 * Plants 3 mutants; each must be caught.
 */
const fs=require('fs'), path=require('path')
const html=fs.readFileSync(path.join(__dirname,'..','amadeus.html'),'utf8')
const cut=(src,a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);if(i<0||j<0){console.error('ANCHOR MISSING: '+a+' … '+b);process.exit(2)}return src.slice(i,j)}
const INITBGM=cut(html,'function initBGM(){','\nfunction startBGMOnce(){')
const UNLOAD=cut(html,"window.addEventListener('beforeunload', () => {",'\n// ── SESSION DIARY ──')
const TRAIL=cut(html,"for(const ev of ['loadstart'","\n  }")

// initBGM with a fake Audio.  Returns the created elements and the log lines.
function runBGM(src,unloading){
  const made=[], logs=[]
  class FakeAudio{constructor(u){this.u=u;made.push(this)} play(){return Promise.resolve()} pause(){}}
  const env=new Function('Audio','console','unloading',`
    let BGM_TRACKS=['music/a.mp3','music/b.mp3'],BGM_VOLUME=0.2,BGM_DUCK_VOLUME=0.1,_bgmDucked=false,bgmInterrupted=false,bgmAudio=null,_pageUnloading=unloading
    ${src}
    initBGM(); return ()=>bgmAudio`)(FakeAudio,{log:(...a)=>logs.push(a.join(' '))},unloading)
  const first=env(); first.onerror()
  return {made:made.length,logs}
}
// The beforeunload handler with fakes.  Records the flag value at the moment each src is cleared.
function runUnload(src){
  const atClear=[], logs=[]
  const media=()=>{const o={pause(){}};Object.defineProperty(o,'src',{set(){atClear.push(get())}});return o}
  let get
  const handler=new Function('console','media',`
    let _pageUnloading=false, currentAudio=media(), bgmAudio=media(), audioCtx=null, mediaRecorder=null, isRecording=false, hf={active:false}, studyActive=false
    const document={querySelectorAll:()=>[media()]}
    let captured; const window={addEventListener:(ev,fn)=>{captured=fn}}
    ${src.replace(/\n\}\)\s*$/,'})')}
    return {fire:captured,flag:()=>_pageUnloading}`)({log:(...a)=>logs.push(a.join(' '))},media)
  get=handler.flag
  handler.fire()
  return {atClear,logs,flag:handler.flag()}
}
function runTrail(src,unloading){
  const logs=[], L={}
  const vid={currentTime:0,readyState:0,addEventListener:(ev,fn)=>{L[ev]=fn}}
  new Function('vid','console','_pageUnloading',src)(vid,{log:(...a)=>logs.push(a.join(' '))},unloading)
  L.error(); return logs
}

function checks(M={}){
  const bgm=M.bgm||INITBGM, unl=M.unload||UNLOAD, trl=M.trail||TRAIL
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  const live=runBGM(bgm,false), down=runBGM(bgm,true), u=runUnload(unl)
  t('BGM error outside unload: logs "not found" and skips to the next track (unchanged)', live.made===2&&live.logs.some(l=>/BGM track not found/.test(l)))
  t('BGM error during unload: NO line and NO new Audio', down.made===1&&down.logs.length===0)
  t('beforeunload: the flag is TRUE at every src clear', u.atClear.length>=3&&u.atClear.every(v=>v===true))
  t('beforeunload: logs the [unload] marker', u.logs.some(l=>/^\[unload\] releasing audio\/video/.test(l)))
  const tl=runTrail(trl,true), tn=runTrail(trl,false)
  t('boot-video trail during unload: line KEPT and labelled "(unload teardown)"', tl.length===1&&/\[BootVideo\] error .*\(unload teardown\)/.test(tl[0]))
  t('boot-video trail outside unload: unchanged, no label', tn.length===1&&/\[BootVideo\] error t=0\.00 rs=0$/.test(tn[0]))
  return r
}

const res=checks(); let fail=0
for(const [n,ok] of res){ console.log((ok?'  PASS  ':'  FAIL  ')+n); if(!ok)fail++ }
const mutants={
  'BGM guard removed':{bgm:INITBGM.replace('if(_pageUnloading)return','')},
  'flag set AFTER the teardown':{unload:UNLOAD.replace('  _pageUnloading=true\n','').replace("    // Pause any playing <audio>/<video> elements in the DOM","    _pageUnloading=true\n    // Pause any playing <audio>/<video> elements in the DOM")},
  'trail label removed':{trail:TRAIL.replace(",...(_pageUnloading?['(unload teardown)']:[])","")},
}
let caught=0
for(const [name,m] of Object.entries(mutants)){
  const k=Object.keys(m)[0], orig={bgm:INITBGM,unload:UNLOAD,trail:TRAIL}[k]
  if(m[k]===orig){ console.log('  MUTANT DID NOT APPLY: '+name); fail++; continue }
  const hit=checks(m).some(([,ok])=>!ok)
  console.log((hit?'  CAUGHT  ':'  MISSED  ')+'mutant: '+name); hit?caught++:fail++
}
console.log(`\n${res.length-res.filter(([,o])=>!o).length}/${res.length} checks passed, ${caught}/${Object.keys(mutants).length} mutants caught`)
process.exit(fail?1:0)
