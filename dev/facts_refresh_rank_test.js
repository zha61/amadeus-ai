/*
 * dev/facts_refresh_rank_test.js — a memory-panel change re-selects facts with the BOOT ranking
 * (backlog #217 / bugs.md 96).  Run:  node dev/facts_refresh_rank_test.js
 *
 * Before the fix, _memoryRefreshActive() took the first 20 facts in STORE order, while boot
 * (initFacts) ranks them by _factRank — so after a panel add/edit/delete a live upcoming exam
 * could fall out of her prompt (>20 facts), and a dated fact lost its place at the top.
 *
 * Extracts the SHIPPED code from amadeus.html by anchor (exit 2 if an anchor moves), and the
 * PREVIOUS code from `git show <BASE>:amadeus.html` to prove the BOOT prompt is byte-identical.
 * Tests outcomes (CLAUDE.md 50): what is IN formatFactsSection() after a panel change.
 * Plants 3 mutants; each must be caught.
 */
const fs=require('fs'), {execSync}=require('child_process')
const ROOT=__dirname+'/../'
const BASE='b8e929e'   // last commit before #217 touched amadeus.html
const now=fs.readFileSync(ROOT+'amadeus.html','utf8')
const old=execSync('git show '+BASE+':amadeus.html',{cwd:ROOT,maxBuffer:1<<26}).toString()
const cut=(src,a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);if(i<0||j<0){console.error('ANCHOR MISSING: '+a+' … '+b);process.exit(2)}return src.slice(i,j)}
const line=(src,re)=>{const m=src.match(re);if(!m){console.error('ANCHOR MISSING: '+re);process.exit(2)}return m[0]+'\n'}
const blockOf=src=> line(src,/const FACTS_KEY\s*=.*/)+line(src,/const FACTS_MAX\s*=.*/)+line(src,/const FACTS_INJECT_MAX\s*=.*/)
  + line(src,/function loadFacts\(\)\{.*/)+line(src,/function saveFacts\(f\)\{.*/)+'let _factsActive=[]\n'
  + cut(src,'function _factRank(f){','// Extraction is a full gemma4 inference')
  + cut(src,'let _pendingMemoryNote=null',"document.getElementById('t-memory')")

function ago(n){ const d=new Date(); d.setHours(12,0,0,0); d.setDate(d.getDate()-n)
  return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0') }
function page(src,mutate=x=>x){
  const m=new Map(), storage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v))}
  const els={}, document={getElementById:id=>els[id]||(els[id]={value:'',innerHTML:'',style:{},querySelectorAll:()=>[]})}
  const out={}
  new Function('localStorage','console','document','out',
    mutate(blockOf(src))+`
    out.fmt=()=>formatFactsSection(); out.init=()=>initFacts(); out.active=()=>_factsActive;
    out.add=t=>{document.getElementById('memory-add-input').value=t;memoryAdd()};
    out.edit=(i,t)=>memoryEdit(i,t); out.del=i=>memoryDelete(i);
    out.load=()=>loadFacts(); out.save=f=>saveFacts(f);`)
    (storage,{log(){},warn(){}},document,out)
  return out
}
const set=(p,facts)=>{p.save(facts);p.init()}
const EXAM='Zani has a piano exam'
const has=(p,f)=>p.fmt().split('\n').some(l=>l.startsWith('- '+f))
// 25 facts; the upcoming exam sits at store position 22, below the 20-fact cut in store order
const many=()=>{ const f=Array.from({length:25},(_,i)=>({fact:'Zani fact '+i,category:'other',date:ago(5)}))
  f[22]={fact:EXAM,category:'event',date:ago(5),event_date:ago(-3)}; return f }
// 4 facts; the dated one is LAST in the store but ranks first
const few=()=>[{fact:'Zani likes chess',category:'preference',date:ago(1)},
  {fact:'Zani has a sister',category:'person',date:ago(2)},
  {fact:'Zani is learning guitar',category:'project',date:ago(3)},
  {fact:EXAM,category:'event',date:ago(4),event_date:ago(-2)}]
const J=x=>JSON.stringify(x)

function checks(mutate=x=>x){
  const r=[]; const t=(n,c)=>r.push([n,!!c])
  const P=()=>page(now,mutate), O=()=>page(old)
  { // 1. OUTCOME: >20 facts, a panel ADD keeps the upcoming exam in her prompt
    const p=P(); set(p,many())
    t('boot: exam in prompt (25 facts, store position 22)', has(p,EXAM))
    p.add('Zani plays the violin')
    t('OUTCOME: after memoryAdd the exam is STILL in formatFactsSection()', has(p,EXAM)&&p.active().length===20)
  }
  { // 2. the same after DELETE and after EDIT
    const p=P(); set(p,many()); p.del(0)
    const s=many(); s.unshift({fact:'Zani filler',category:'other',date:ago(5)}); s.unshift({fact:'Zani filler 2',category:'other',date:ago(5)})
    const q=P(); set(q,s); q.del(0)   // 27 → 26 facts: exam at position 23 after the delete
    t('OUTCOME: after memoryDelete the exam is STILL in the prompt', has(p,EXAM)&&has(q,EXAM))
    const e=P(); set(e,s); e.edit(1,'Zani filler edited')
    t('OUTCOME: after memoryEdit the exam is STILL in the prompt', has(e,EXAM)&&has(e,'Zani filler edited'))
  }
  { // 3. after each panel change the active set equals a fresh boot selection (order too)
    const ok=[]
    for(const act of [p=>p.add('Zani plays the violin'),p=>p.edit(0,'Zani likes blitz chess'),p=>p.del(1)]){
      const p=P(); set(p,few()); act(p)
      const after=J(p.active()); p.init()
      ok.push(after===J(p.active()) && p.active()[0].fact===EXAM)
    }
    t('after add / edit / delete: _factsActive === fresh initFacts(), dated fact first', ok.every(Boolean))
  }
  { // 4. a fact added in the panel reaches the prompt at once
    const p=P(); set(p,few()); p.add('Zani plays the violin')
    t('OUTCOME: the added fact IS in formatFactsSection() at once', has(p,'Zani plays the violin'))
  }
  { // 5. BOOT is byte-identical to BASE (mixed dated / undated / stale / >20)
    const mixed=[...few(),{fact:'Zani had a mock exam',category:'event',date:ago(40),event_date:ago(20)},
      {fact:'Zani went to Paris',category:'event',date:ago(6),event_date:ago(5)},
      {fact:'Zani is currently coding',category:'project',date:ago(200)},{fact:'Zani has a cat',category:'other'}]
    const same=[few(),many(),mixed,[]].every(fx=>{const p=P(),o=O(); set(p,fx); set(o,fx); return p.fmt()===o.fmt()&&J(p.active())===J(o.active())})
    t('boot prompt block byte-identical to '+BASE+' (4 fixtures)', same)
  }
  return r
}

const MUTANTS=[
  ['M1 old unranked slice', s=>s.replace('function _memoryRefreshActive(){ initFacts() }','function _memoryRefreshActive(){ _factsActive=loadFacts().slice(0,FACTS_INJECT_MAX) }')],
  ['M2 initFacts without the sort', s=>s.replace('.sort((a,b)=> a.r-b.r || a.i-b.i)','')],
  ['M3 refresh without reading the store', s=>s.replace('function _memoryRefreshActive(){ initFacts() }','function _memoryRefreshActive(){ _factsActive=_factsActive.slice(0,FACTS_INJECT_MAX) }')],
]

let fail=0
for(const [n,c] of checks()){ console.log((c?'  ok   ':'  FAIL ')+n); if(!c)fail++ }
const base=blockOf(now); let caught=0
for(const [n,mut] of MUTANTS){
  if(mut(base)===base){ console.error('MUTANT DID NOT APPLY (anchor moved?): '+n); process.exit(2) }
  const bad=checks(mut).filter(([,c])=>!c).length
  console.log((bad?'  caught   ':'  MISSED   ')+n+(bad?' ('+bad+' checks failed)':''))
  if(bad)caught++
}
const total=checks().length
console.log(`\n${total-fail}/${total} checks passed, ${caught}/${MUTANTS.length} mutants caught`)
process.exit(fail||caught<MUTANTS.length?1:0)
