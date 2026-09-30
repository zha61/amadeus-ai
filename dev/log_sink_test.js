/*
 * dev/log_sink_test.js — the log sink (backlog #203 / #204).
 * Run:  node dev/log_sink_test.js        (~15 s; spawns short python children, no model call)
 *
 * The helpers are EXTRACTED FROM THE SHIPPED main.js by anchor (exit 2 if one moves).
 * OUTCOME check (CLAUDE.md 50): a child that writes 2 MB now FINISHES, and its output is in
 * the file. CONTROL: the same child on the old default pipe must BLOCK, or this test has no teeth.
 * Plants 5 mutants; each must be caught. Check 9 runs the REAL Electron (backlog #219).
 */
const fs=require('fs'), path=require('path'), os=require('os'), {spawn}=require('child_process'), EventEmitter=require('events')
const ROOT=path.join(__dirname,'..')
const mainSrc=fs.readFileSync(path.join(ROOT,'main.js'),'utf8')
const html=fs.readFileSync(path.join(ROOT,'amadeus.html'),'utf8')
const rag=fs.readFileSync(path.join(ROOT,'kurisu_rag_server.py'),'utf8')
const cut=(src,a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);if(i<0||j<0){console.error('ANCHOR MISSING: '+a+' … '+b);process.exit(2)}return src.slice(i,j)}
const BLOCK=cut(mainSrc,'// ── LOG SINK (backlog #203 / #204) ──','let mainWindow, ttsProcess')
const PYTHON='/opt/homebrew/bin/python3'
const tmp=()=>fs.mkdtempSync(path.join(os.tmpdir(),'amadeus-logtest-'))
const sleep=ms=>new Promise(r=>setTimeout(r,ms))
const exitWithin=(p,ms)=>new Promise(res=>{let done=false;p.on('exit',c=>{done=true;res({exited:true,code:c})});setTimeout(()=>{if(!done)res({exited:false})},ms)})

function load(mutate=x=>x, fakeConsole=null){
  const out={}
  const con=fakeConsole||{log(){},warn(){},error(){}}
  new Function('require','path','fs','spawn','PYTHON','AMADEUS_DIR','console','out',
    mutate(BLOCK)+`;out.childStdio=childStdio;out.spawnLogged=spawnLogged;out.makeLineWriter=makeLineWriter;
      out.rotate=rotateLogIfLarge;out.wanted=rendererLineWanted;out.attach=attachRendererLog;out.install=installMainLog;
      out.ROT=LOG_ROTATE_BYTES;`)(require,path,fs,spawn,PYTHON,ROOT,con,out)
  return out
}
// Runs the LOG SINK block inside the real Electron from node_modules (same binary as dist/, checked
// with cmp 2026-09-29).  Hidden window, no model call, ~2 s, ~150 MB while it runs.
const ELECTRON=require(path.join(ROOT,'node_modules','electron'))
function electronRun(block,dir){
  const bf=path.join(dir,'block.js'), mf=path.join(dir,'main.js')
  fs.writeFileSync(bf,block)
  fs.writeFileSync(mf,`const {app,BrowserWindow}=require('electron'),path=require('path'),fs=require('fs'),{spawn}=require('child_process')
const out={}
new Function('require','path','fs','spawn','PYTHON','AMADEUS_DIR','console','out',fs.readFileSync(${JSON.stringify(bf)},'utf8')+';out.attach=attachRendererLog')(require,path,fs,spawn,'',${JSON.stringify(ROOT)},console,out)
app.whenReady().then(()=>{
  const w=new BrowserWindow({show:false})
  out.attach(w.webContents,${JSON.stringify(dir)})
  w.on('page-title-updated',()=>setTimeout(()=>{console.log('EL_DONE');app.quit()},300))
  w.loadURL('data:text/html,'+encodeURIComponent('<script>console.debug("el-debug");console.log("el-info");console.log("[LipSync] peak: 0.3");console.warn("el-warn");console.error("el-error");setTimeout(()=>document.title="x",100)</script>'))
})`)
  const env={...process.env}; delete env.ELECTRON_RUN_AS_NODE
  return new Promise(res=>{
    let out=''; const p=spawn(ELECTRON,[mf],{env})
    p.stdout.on('data',b=>out+=b); p.stderr.on('data',b=>out+=b)
    const timer=setTimeout(()=>p.kill('SIGKILL'),20000)
    p.on('exit',()=>{clearTimeout(timer);res({done:/EL_DONE/.test(out),out})})
  })
}
const WRITE2MB="import sys\nfor i in range(10000): sys.stdout.write('o'*99+'\\n'); sys.stderr.write('e'*99+'\\n')\n"

async function checks(mutate=x=>x){
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  { // 1. OUTCOME: 2 MB of output no longer blocks the child, and all of it is in the file
    const L=load(mutate), d=tmp()
    const p=L.spawnLogged('child',['-c',WRITE2MB],d)
    const res=await exitWithin(p,10000); if(!res.exited) p.kill('SIGKILL')
    const f=path.join(d,'child.log'), size=fs.existsSync(f)?fs.statSync(f).size:0, txt=size?fs.readFileSync(f,'utf8'):''
    t('OUTCOME: child writing 2 MB exits (was blocked at ~131 KB)', res.exited&&res.code===0)
    t('OUTCOME: all 2 MB is in data/logs/<name>.log', size>=2000000)
    t('spawn header line written (name + pid)', /=== \S+ spawn child pid \d+ ===/.test(txt))
  }
  { // 2. PYTHONUNBUFFERED: a plain print() reaches the file while the child still runs
    const L=load(mutate), d=tmp()
    const p=L.spawnLogged('buf',['-c',"import time\nprint('line-before-sleep')\ntime.sleep(5)"],d)
    await sleep(1500); const txt=fs.readFileSync(path.join(d,'buf.log'),'utf8'); p.kill('SIGKILL')
    t('unbuffered: print() visible after 1.5 s, before exit', txt.includes('line-before-sleep'))
  }
  { // 3. rotation at 2 MB: old content → .1, new file starts fresh
    const L=load(mutate), d=tmp(), f=path.join(d,'rot.log')
    fs.writeFileSync(f,'x'.repeat(L.ROT+10)); fs.writeFileSync(f+'.1','older')
    const {fd}=L.childStdio('rot',d); fs.closeSync(fd)
    t('rotation: >2 MB file moved to .1 (replacing the older .1), new file empty', fs.statSync(f+'.1').size===L.ROT+10&&fs.statSync(f).size===0)
    const g=path.join(d,'small.log'); fs.writeFileSync(g,'keep'); const s=L.childStdio('small',d); fs.closeSync(s.fd)
    t('rotation: small file is kept and appended to', fs.readFileSync(g,'utf8')==='keep'&&!fs.existsSync(g+'.1'))
  }
  { // 4. unwritable folder → 'ignore', never 'pipe', never throws; the child still runs
    const L=load(mutate); let res, threw=false
    try{ res=L.childStdio('x','/dev/null/cannot') }catch(e){ threw=true }
    t("unwritable folder: stdio 'ignore' (NOT 'pipe'), fd null, no throw", !threw&&res.stdio==='ignore'&&res.fd===null)
    const p=L.spawnLogged('x',['-c',WRITE2MB],'/dev/null/cannot'); const e=await exitWithin(p,10000); if(!e.exited)p.kill('SIGKILL')
    t('unwritable folder: a 2 MB child still exits', e.exited&&e.code===0)
  }
  { // 5. line writer: session cap, one cap line, never throws
    const L=load(mutate), d=tmp(), f=path.join(d,'cap.log'), w=L.makeLineWriter(f,200)
    for(let i=0;i<50;i++) w('line number '+i)
    const txt=fs.readFileSync(f,'utf8')
    t('cap: stops at the cap and writes exactly one cap line', Buffer.byteLength(txt)<400&&(txt.match(/session cap/g)||[]).length===1)
    let threw=false; try{ L.makeLineWriter('/dev/null/nope/x.log')('hi') }catch(e){ threw=true }
    t('writer never throws on an unwritable path', !threw)
  }
  { // 6. renderer filter: deny-list only
    const L=load(mutate)
    t('drops [LipSync] peak / ticker INFO lines', !L.wanted('info','[LipSync] peak: 0.1 smooth: 0.1 form: 0.3')&&!L.wanted('info','[LipSync ticker] mouthY= 0.4'))
    t('keeps every warning and error, even LipSync', L.wanted('warning','[LipSync] peak: odd')&&L.wanted('warning','[LipSync] setup failed')&&L.wanted('error','x'))
    t('keeps other info lines ([Perf], [Facts], [parsEmo], untagged)', ['[Perf] text you→her 4000ms','[Facts] store size: 3','[parsEmo] no tag → default','plain'].every(m=>L.wanted('info',m)))
  }
  { // 7. attachRendererLog with the Electron 35 event shape (fake emitter; the REAL Electron is check 9)
    const warns=[], L=load(mutate,{log(){},warn:(...a)=>warns.push(a.join(' ')),error(){}}), d=tmp(), wc=new EventEmitter()
    L.attach(wc,d)
    wc.emit('console-message',{level:'info',message:'[Perf] text you→her 4321ms'})
    wc.emit('console-message',{level:'info',message:'[LipSync] peak: 0.2'})
    wc.emit('console-message',{level:'warning',message:'[RAG] unavailable — skipping retrieval for 60s'})
    wc.emit('render-process-gone',{},{reason:'crashed',exitCode:5})
    const txt=fs.readFileSync(path.join(d,'renderer.log'),'utf8')
    t('renderer.log: Electron 35 shape logged with level', /INFO \[Perf\] text you→her 4321ms/.test(txt))
    t('renderer.log: details.level warning logged as WARNING', /WARNING \[RAG\] unavailable/.test(txt))
    t('renderer.log: LipSync peak dropped', !/LipSync/.test(txt))
    t('render-process-gone reported', warns.some(w=>/renderer process gone: crashed exitCode 5/.test(w)))
  }
  { // 8. installMainLog: console still works AND lines land in main.log
    const seen=[], fake={log:(...a)=>seen.push(a.join(' ')),warn:(...a)=>seen.push(a.join(' ')),error:(...a)=>seen.push(a.join(' '))}
    const L=load(mutate,fake), d=tmp(); L.install(d)
    fake.warn('[main:watchdog] rag exited (code %d)',1)
    const txt=fs.readFileSync(path.join(d,'main.log'),'utf8')
    t('main.log: WARN line formatted like console', /WARN \[main:watchdog\] rag exited \(code 1\)/.test(txt))
    t('original console still receives it', seen.some(s=>/watchdog/.test(s)))
  }
  { // 9. OUTCOME in the REAL Electron (backlog #219): the shipped listener, a hidden window, one line
    //    per level.  Electron 35 warns when any 'console-message' listener has >1 parameter.
    const d=tmp(), e=await electronRun(mutate(BLOCK),d)
    const f=path.join(d,'renderer.log'), txt=fs.existsSync(f)?fs.readFileSync(f,'utf8'):''
    t('Electron: page finished and quit', e.done)
    t("Electron: NO 'console-message' deprecation warning", e.done&&!/console-message' arguments are deprecated/.test(e.out))
    t('Electron: levels are right (DEBUG, INFO, WARNING, ERROR)', /DEBUG el-debug/.test(txt)&&/INFO el-info/.test(txt)&&/WARNING el-warn/.test(txt)&&/ERROR el-error/.test(txt))
    t('Electron: LipSync peak info line dropped', /INFO el-info/.test(txt)&&!/LipSync/.test(txt))
  }
  return r
}
function staticChecks(){
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  t('main.js: no spawn(PYTHON …) outside spawnLogged', (mainSrc.match(/spawn\(PYTHON/g)||[]).length===1&&BLOCK.includes('spawn(PYTHON'))
  t('main.js: all 4 servers use spawnLogged', ["spawnLogged('fish'","spawnLogged('http'","spawnLogged('rag'","spawnLogged('whisper'"].every(s=>mainSrc.includes(s)))
  t('main.js: installMainLog only when gotTheLock', /if \(gotTheLock\) installMainLog\(\)/.test(mainSrc))
  t('main.js: renderer log attached BEFORE loadURL', mainSrc.indexOf('attachRendererLog(mainWindow.webContents)')>0&&mainSrc.indexOf('attachRendererLog(mainWindow.webContents)')<mainSrc.indexOf('mainWindow.loadURL(htmlUrl)'))
  t('main.js: #210 warn when the fallback diary prompt is used', /if \(!diarySystemPrompt\) console\.warn/.test(mainSrc))
  const ret=cut(rag,'def retrieve():','@app.route(\'/index-diary\'')
  t("rag: query='' is set BEFORE the try", ret.indexOf("query = ''")>0&&ret.indexOf("query = ''")<ret.indexOf('try:'))
  t('rag: error branch writes a trace line with the error', /except Exception as e:[\s\S]*_trace\(\{'q': query\[:80\], 'error': str\(e\)\[:200\]\}\)/.test(ret))
  return r
}
function parsEmoChecks(){  // behaviour must be unchanged; only a log line is added
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  const src=cut(html,'function parsEmo(text) {','\n// ')
  const logs=[]; const f=new Function('console',src+';return parsEmo')({log:(...a)=>logs.push(a.join(' '))})
  const cases=[['[EMOTION:smug] Hi.',{emotion:'smug',text:'Hi.'}],['[concerned] Hm.',{emotion:'default',text:'Hm.'}],['No tag.',{emotion:'default',text:'No tag.'}],['',{emotion:'default',text:''}]]
  t('parsEmo: return values unchanged', cases.every(([i,o])=>JSON.stringify(f(i))===JSON.stringify(o)))
  t('parsEmo: logs unknown tag and missing tag, nothing for a valid tag', logs.length===2&&/unknown tag → default: concerned/.test(logs[0])&&/no tag → default/.test(logs[1]))
  return r
}

;(async()=>{
  // CONTROL: the old default (pipe, unread) must block — otherwise check 1 proves nothing.
  const ctl=spawn(PYTHON,['-c',WRITE2MB]); const c=await exitWithin(ctl,3000); if(!c.exited) ctl.kill('SIGKILL')
  const res=[['CONTROL: the same child on an unread pipe BLOCKS (the bug is real)',!c.exited],...await checks(),...staticChecks(),...parsEmoChecks()]
  let fail=0
  for(const [n,ok] of res){ console.log((ok?'  PASS  ':'  FAIL  ')+n); if(!ok)fail++ }
  const mutants={
    'normal stdio back to pipe':x=>x.replace("return { stdio: ['ignore', fd, fd], fd }","return { stdio: 'pipe', fd }"),
    "fallback 'pipe' instead of 'ignore'":x=>x.replace("return { stdio: 'ignore', fd: null }","return { stdio: 'pipe', fd: null }"),
    'filter drops warnings':x=>x.replace("if (level === 'warning' || level === 'error') return true","if (level === 'error') return true"),
    'session cap removed':x=>x.replace('if (written + n > cap) {','if (false) {'),
    'listener takes the deprecated positional args (#219)':x=>x.replace("wc.on('console-message', (details) => {","wc.on('console-message', (details, lvl, msg) => {"),
  }
  let caught=0
  for(const [name,mut] of Object.entries(mutants)){
    if(mut(BLOCK)===BLOCK){ console.log('  MUTANT DID NOT APPLY: '+name); fail++; continue }
    const hit=(await checks(mut)).some(([,ok])=>!ok)
    console.log((hit?'  CAUGHT  ':'  MISSED  ')+'mutant: '+name); hit?caught++:fail++
  }
  console.log(`\n${res.length-res.filter(([,o])=>!o).length}/${res.length} checks passed, ${caught}/${Object.keys(mutants).length} mutants caught`)
  process.exit(fail?1:0)
})()
