/*
 * dev/facts_age_test.js — fact age notes + renewal (backlog #216).
 * Run:  node dev/facts_age_test.js
 *
 * Extracts the SHIPPED code from amadeus.html by anchor (exit 2 if an anchor moves), and
 * the PREVIOUS prompt code from `git show <BASE>:amadeus.html`, to prove the prompt is
 * BYTE-IDENTICAL for every fact under 30 days old. Tests outcomes (CLAUDE.md 50): the note
 * is IN the built prompt; a renewed fact is at the FRONT and survives the 60-cap.
 * Plants 3 mutants; each must be caught.
 */
const fs=require('fs'), {execSync}=require('child_process')
const ROOT=__dirname+'/../'
const BASE='bbb0c8b'   // last commit before #216 touched amadeus.html
const now=fs.readFileSync(ROOT+'amadeus.html','utf8')
const old=execSync('git show '+BASE+':amadeus.html',{cwd:ROOT,maxBuffer:1<<26}).toString()
const cut=(src,a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);if(i<0||j<0){console.error('ANCHOR MISSING: '+a+' … '+b);process.exit(2)}return src.slice(i,j)}
const line=(src,re)=>{const m=src.match(re);if(!m){console.error('ANCHOR MISSING: '+re);process.exit(2)}return m[0]+'\n'}
const blockOf=src=> line(src,/const FACTS_KEY\s*=.*/)+line(src,/const FACTS_MAX\s*=.*/)+line(src,/const FACTS_INJECT_MAX\s*=.*/)
  + line(src,/function loadFacts\(\)\{.*/)+line(src,/function saveFacts\(f\)\{.*/)+'let _factsActive=[]\n'
  + cut(src,'function _factRank(f){','// Extraction is a full gemma4 inference')
  + cut(src,'function _normFact','// DEV: inspect the fact store')
  + cut(src,'function memoryEdit(','function memoryDelete(')

function ago(n){ const d=new Date(); d.setHours(12,0,0,0); d.setDate(d.getDate()-n)
  return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0') }
function page(src,mutate=x=>x){
  const m=new Map(), storage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v))}
  const out={}
  new Function('localStorage','console','_memoryRefreshActive','_memoryNote','renderMemory','out',
    mutate(blockOf(src))+`
    out.fmt=()=>formatFactsSection(); out.init=()=>initFacts(); out.active=()=>_factsActive;
    out.rank=f=>_factRank(f); out.merge=a=>mergeFacts(a); out.edit=(i,t)=>memoryEdit(i,t);
    out.age=typeof _factAge==='function'?_factAge:null; out.load=()=>loadFacts(); out.save=f=>saveFacts(f);`)
    (storage,{log(){},warn(){}},()=>{},()=>{},()=>{},out)
  return out
}
const set=(p,facts)=>{p.save(facts);p.init()}

async function checks(mutate=x=>x){
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  const P=()=>page(now,mutate), O=()=>page(old)
  { // 1. BYTE-IDENTICAL below 30 days, incl. dated facts and a missing/invalid date
    const facts=[{fact:'Zani is currently coding',category:'project',date:ago(0)},
      {fact:'Zani is learning guitar',category:'project',date:ago(29)},
      {fact:'Zani has a piano exam',category:'event',date:ago(3),event_date:ago(-10)},
      {fact:'Zani had a mock exam',category:'event',date:ago(40),event_date:ago(20)},
      {fact:'Zani has a sister',category:'person'},{fact:'Zani likes chess',category:'other',date:'garbage'}]
    const p=P(),o=O(); set(p,facts); set(o,facts)
    t('prompt byte-identical to '+BASE+' when every undated fact is <30 days old', p.fmt()===o.fmt()&&p.fmt().length>0)
  }
  { // 2. the note: thresholds and wording
    const p=P(), a=d=>p.age({fact:'x',date:ago(d)})
    t('29 days → no note', a(29)==='')
    t('30 days → "learned over a month ago — it may have changed"', a(30)==='  [learned over a month ago — it may have changed]')
    t('59 → a month; 60 → 2 months; 179 → 5 months', /over a month ago/.test(a(59))&&/over 2 months ago/.test(a(60))&&/over 5 months ago/.test(a(179)))
    t('180 and 400 → six months', /over six months ago/.test(a(180))&&/over six months ago/.test(a(400)))
    t('note says "learned", never "mentioned"', /learned/.test(a(90))&&!/mention/i.test(a(90)))
    t('seen overrides date (date 100d, seen 5d → no note)', p.age({fact:'x',date:ago(100),seen:ago(5)})==='')
    t('missing / invalid date → no note, no throw', p.age({fact:'x'})===''&&p.age({fact:'x',date:'2026-13-99'})==='')
    t('dated fact → no age note (bug 64 label owns it)', p.age({fact:'x',date:ago(90),event_date:ago(80)})==='')
  }
  { // 3. OUTCOME: an old undated fact shows the note IN the prompt; dated labels unchanged
    const p=P(),o=O(), facts=[{fact:'Zani is currently coding',category:'project',date:ago(45)},
      {fact:'Zani had a mock exam',category:'event',date:ago(90),event_date:ago(80)}]
    set(p,facts); set(o,facts)
    t('OUTCOME: 45-day-old undated fact carries the note in formatFactsSection()', p.fmt().includes('- Zani is currently coding  [learned over a month ago — it may have changed]'))
    t('dated fact line identical to '+BASE, p.fmt().split('\n').find(l=>/mock/.test(l))===o.fmt().split('\n').find(l=>/mock/.test(l)))
  }
  { // 4. rank: stale undated facts drop out of the top 20 first; dated ranks unchanged
    const p=P(),o=O()
    t('undated 179d → rank 2, 180d → rank 3', p.rank({date:ago(179)})===2&&p.rank({date:ago(180)})===3)
    const dated=[ago(-5),ago(0),ago(-1),ago(3),ago(30)].map(e=>({date:ago(1),event_date:e}))
    t('dated ranks identical to '+BASE, dated.every(f=>p.rank(f)===o.rank(f)))
    const facts=[...Array.from({length:5},(_,i)=>({fact:'stale '+i,date:ago(200)})),...Array.from({length:20},(_,i)=>({fact:'fresh '+i,date:ago(10)}))]
    set(p,facts); t('>20 facts: the 5 stale undated ones are the ones left out', p.active().length===20&&p.active().every(f=>/fresh/.test(f.fact)))
  }
  { // 5. renewal on a duplicate: seen=today, moved to front, no duplicate, first-learned date kept
    const p=P(); p.save([{fact:'Zani likes chess',date:ago(1)},{fact:'Zani is learning to play the guitar.',category:'project',date:ago(90)}])
    p.merge([{fact:'zani is learning to play the guitar',category:'project'}])
    const s=p.load()
    t('duplicate renews: moved to front, seen=today, date kept, no copy', s.length===2&&/guitar/.test(s[0].fact)&&s[0].seen===ago(0)&&s[0].date===ago(90))
    set(p,s); t('OUTCOME: after renewal the note is gone from the prompt', !/learned over/.test(p.fmt()))
  }
  { // 6. replace: renewed and moved to front
    const p=P(); p.save([{fact:'a',date:ago(1)},{fact:'Zani plays osu',date:ago(70)}])
    p.merge([{fact:'Zani plays Project Sekai',category:'preference',replaces:'Zani plays osu'}])
    const s=p.load(); t('replace: new text at front, date today, old gone', s.length===2&&s[0].fact==='Zani plays Project Sekai'&&s[0].date===ago(0)&&!s.some(f=>f.fact==='Zani plays osu'))
  }
  { // 7. LRU at the 60-cap: a renewed old fact survives; the least-recently-renewed one goes
    const p=P(); p.save(Array.from({length:60},(_,i)=>({fact:'fact number '+i,date:ago(i)})))
    p.merge([{fact:'fact number 59'}]); p.merge([{fact:'brand new fact'}])
    const s=p.load(); t('cap: renewed #59 kept, #58 (least recently renewed) dropped', s.length===60&&s.some(f=>f.fact==='fact number 59')&&!s.some(f=>f.fact==='fact number 58')&&s[0].fact==='brand new fact')
  }
  { // 8. memoryEdit: renewed but NOT moved
    const p=P(); p.save([{fact:'a',date:ago(1)},{fact:'b',date:ago(50)},{fact:'c',date:ago(2)}])
    p.edit(1,'b edited'); const s=p.load()
    t('memoryEdit: seen=today, positions unchanged', s.map(f=>f.fact).join()==='a,b edited,c'&&s[1].seen===ago(0))
  }
  return r
}

;(async()=>{
  const res=await checks(); let fail=0
  for(const [n,ok] of res){ console.log((ok?'  PASS  ':'  FAIL  ')+n); if(!ok)fail++ }
  const mutants={
    'note threshold 0 days':c=>c.replace('const FACT_AGE_NOTE_DAYS = 30','const FACT_AGE_NOTE_DAYS = 0'),
    'duplicate renewed in place (no move)':c=>c.replace('f.seen=today; facts.unshift(f); continue','f.seen=today; facts.splice(dup,0,f); continue'),
    'memoryEdit does not renew':c=>c.replace("  facts[idx].seen=_localDateStr()\n",''),
  }
  let caught=0
  for(const [name,mut] of Object.entries(mutants)){
    if(mut(blockOf(now))===blockOf(now)){ console.log('  MUTANT DID NOT APPLY: '+name); fail++; continue }
    const hit=(await checks(mut)).some(([,ok])=>!ok)
    console.log((hit?'  CAUGHT  ':'  MISSED  ')+'mutant: '+name); hit?caught++:fail++
  }
  console.log(`\n${res.length-res.filter(([,o])=>!o).length}/${res.length} checks passed, ${caught}/${Object.keys(mutants).length} mutants caught`)
  process.exit(fail?1:0)
})()
