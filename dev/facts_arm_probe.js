/*
 * dev/facts_arm_probe.js — measures the facts extractor, HEAD vs an arm (backlog #216).
 * Run:  node dev/facts_arm_probe.js <head|arm> <fixture> <num_predict> <n> [out.json]
 *       fixtures: real | mention-close | mention-idle | light | dense
 * CALLS gemma4 — refuses to run while Amadeus is open (CLAUDE.md 37). Spends no Fish credit.
 * The prompt and the matcher (_normFact) are EXTRACTED from amadeus.html by anchor, never retyped.
 * Pre-registration: dev/facts_arms/PREREG_216.md.
 */
const fs=require('fs'), {execSync}=require('child_process')
try{ execSync('pgrep -x Amadeus',{stdio:'ignore'}); console.error('Amadeus is running — close it first (CLAUDE.md 37).'); process.exit(3) }catch(e){}
const html=fs.readFileSync(__dirname+'/../amadeus.html','utf8')
const a=html.indexOf("    const sys='You extract durable personal facts"), b=html.indexOf("JSON only.'",a)+11
if(a<0||b<11){ console.error('ANCHOR MISSING: extractor sys'); process.exit(2) }
const todayStr='2026-09-27 (Sunday)'
const HEAD=eval(html.slice(a,b).replace('const sys=','(')+')')   // evaluate the shipped concatenation
const nf=html.match(/function _normFact\(s\)\{return [^\n]*\}/); if(!nf){ console.error('ANCHOR MISSING: _normFact'); process.exit(2) }
const _normFact=eval('('+nf[0].replace('function _normFact(s){','(s)=>{')+')')

// The #216 arm as a pure transform of HEAD. Each replace must hit exactly once.
function armPrompt(s){
  const reps=[
    ['"replaces":"<exact known fact text this supersedes or makes untrue, or null>"}]}. ',
     '"replaces":"<exact known fact text this supersedes or makes untrue, or null>"}],"confirmed":["<exact text of a KNOWN FACT>"]}. '],
    ['Resolve relative dates',
     'In "confirmed", copy EXACTLY each KNOWN FACT that the conversation mentions again or clearly shows is still true; do not repeat those in "facts". Leave it empty if none. Resolve relative dates'],
    ['If nothing durable was said, respond {"facts":[]}.',
     'If nothing durable was said and no known fact was confirmed, respond {"facts":[],"confirmed":[]}.'],
  ]
  for(const [x,y] of reps){ if(s.split(x).length!==2) throw new Error('arm transform did not apply once: '+x.slice(0,40)); s=s.replace(x,y) }
  return s
}

const KUR=["[EMOTION:tsundere] Hmph. Don't expect me to care about that. ...Fine, I'll remember it.",
  "[EMOTION:curious] Really? That's more interesting than I expected from you.",
  "[EMOTION:smug] As expected. You're predictable, Zani.",
  "[EMOTION:annoyed] You could have mentioned that earlier, you know."]
const FILLER=['I am so tired today, school was long','what do you think about time travel honestly','lol you are so mean',
  'did you sleep well? oh wait you do not sleep','the weather is so grey here','haha ok fine you win',
  'what are you working on right now','I watched some YouTube videos','I feel kind of bored','that is actually interesting']
const KNOWN10=['Zani is learning to play the guitar.','Zani has a sister named Mia.','Zani supports Arsenal.',
  'Zani is allergic to peanuts.','Zani is learning Japanese on Duolingo.','Zani plans to apply to Imperial for computer science.',
  'Zani has a part-time job at Tesco.','Zani owns a Keychron K2 keyboard.','Zani is vegetarian.','Zani likes the anime Frieren.']
const MENTION=['I practised guitar for like an hour today, my fingers hurt','Mia kept stealing my phone charger again',
  'we beat Chelsea 2-0 last night, Arsenal are flying','oh and I signed up for a 10k charity run on 8 November']
const DENSE=[ "my piano grade 8 exam is on 14 October, I'm so nervous about the Chopin piece","I switched from osu to Project Sekai this week, way more fun on my phone",
 "my friend Tom is coming to visit next Saturday, we're going to the cinema","I got a part-time job at the Tesco near my house, I start on Monday",
 "I'm not doing chess club anymore, I quit last week because of the new job","my mocks start on 3 November, maths first then physics",
 "I want to apply to Imperial for computer science next year","my sister Mia turns 12 on 30 October, I need to get her a present",
 "I started learning Japanese on Duolingo, I'm on a 20 day streak","I support Arsenal, we're playing Spurs on 18 October",
 "I bought a new keyboard, a Keychron K2, it's really clicky","I'm allergic to peanuts by the way, so no satay",
 "I'm going to Tokyo with my family next summer, in August","my favourite anime right now is Frieren, I finished it yesterday",
 "I moved my piano lessons to Thursdays at 5pm","my driving theory test is booked for 21 November",
 "I've been sleeping at 2am every night this week","I'm vegetarian now, I stopped eating meat last month",
 "my laptop is a MacBook Pro M5 with 16GB","I joined the school football team as a goalkeeper"]
const DENSE_KNOWN=['Zani is in chess club','Zani plays osu','Zani has piano lessons on Tuesdays','Zani eats meat',
 'Zani is 18 years old','Zani lives in England','Zani plays rhythm games','Zani likes anime','Zani plays football','Zani plays piano',
 'Zani plays chess','Zani is a student',...Array.from({length:28},(_,k)=>'Zani mentioned hobby number '+(k+1)+' once in passing')]
const REAL=[...FILLER.slice(0,4),DENSE[0],...FILLER.slice(4,8),DENSE[5],...FILLER.slice(8),DENSE[8]]

function chat(zlines,chars){
  let c='',i=0
  while(c.length<chars+800){ c+='Zani: '+zlines[i%zlines.length]+'\nKurisu: '+KUR[i%KUR.length]+'\n'; i++ }
  c=c.slice(-chars); const nl=c.indexOf('\n'); return c.slice(nl+1)   // same whole-line cut as the shipped close pass
}
function mentionLines(){ // filler first, the 4 mention lines inside the LAST 12 lines (so the idle window sees them)
  return [...FILLER,...FILLER.slice(0,3),MENTION[0],FILLER[3],MENTION[1],FILLER[4],MENTION[2],MENTION[3]]
}
function fixture(name){
  if(name==='real') return {known:[],conv:chat(REAL,4800)}
  if(name==='dense') return {known:DENSE_KNOWN,conv:chat(DENSE,4800)}
  if(name==='light') return {known:KNOWN10,conv:FILLER.slice(0,6).map((z,i)=>'Zani: '+z+'\nKurisu: '+KUR[i%4]).join('\n')}
  const ml=mentionLines(), lines=ml.map((z,i)=>'Zani: '+z+'\nKurisu: '+KUR[i%4])
  if(name==='mention-idle') return {known:KNOWN10,conv:lines.slice(-6).join('\n')}   // last 12 history lines = 6 exchanges
  if(name==='mention-close'){ let c=lines.join('\n'); while(c.length<4800) c=FILLER.map((z,i)=>'Zani: '+z+'\nKurisu: '+KUR[i%4]).join('\n')+'\n'+c
    c=c.slice(-4800); return {known:KNOWN10,conv:c.slice(c.indexOf('\n')+1)} }
  throw new Error('unknown fixture '+name)
}

async function main(){
  const [arm,fx,cap,n,out]=[process.argv[2],process.argv[3],+process.argv[4],+process.argv[5],process.argv[6]]
  if(!['head','arm'].includes(arm)||!cap||!n){ console.error('usage: head|arm fixture num_predict n [out]'); process.exit(1) }
  const sys=arm==='arm'?armPrompt(HEAD):HEAD, {known,conv}=fixture(fx)
  const user='KNOWN FACTS:\n'+(known.map(f=>'- '+f).join('\n')||'(none)')+'\n\nCONVERSATION:\n'+conv
  const kn=known.map(_normFact), rows=[]
  for(let s=0;s<n;s++){
    const r=await fetch('http://127.0.0.1:11434/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({model:'gemma4:latest',messages:[{role:'system',content:sys},{role:'user',content:user}],
        stream:false,think:false,keep_alive:'30m',format:'json',options:{temperature:0.2,num_predict:cap,num_ctx:8192,seed:1000+s}})})
    const d=await r.json(); let o=null; try{ o=JSON.parse(d.message.content) }catch(e){}
    const facts=o&&Array.isArray(o.facts)?o.facts.filter(f=>f&&typeof f==='object'):null
    const conf=o&&Array.isArray(o.confirmed)?o.confirmed.filter(x=>typeof x==='string'):[]
    const hit=conf.map(c=>kn.indexOf(_normFact(c)))
    rows.push({seed:1000+s,eval:d.eval_count,done:d.done_reason,ms:Math.round(d.total_duration/1e6),parsed:!!facts,
      nFacts:facts?facts.length:null,factTexts:facts?facts.map(f=>String(f.fact)):[],confirmed:conf,confIdx:hit,
      newRun:facts?facts.some(f=>/10k|charity run|\brun\b/i.test(String(f.fact))):false,
      reemitK123:facts?facts.filter(f=>[0,1,2].includes(kn.indexOf(_normFact(f.fact)))).length:0})
  }
  const cut=rows.filter(r=>!r.parsed||r.done==='length').length
  const sum={arm,fixture:fx,num_predict:cap,n,convChars:conv.length,known:known.length,cut}
  if(fx==='real') sum.all3=rows.filter(r=>r.nFacts>=3&&[/piano|grade 8/i,/mock/i,/japanese|duolingo/i].every(re=>r.factTexts.some(t=>re.test(t)))).length
  if(fx.startsWith('mention')||fx==='light'){
    const tp=rows.reduce((x,r)=>x+new Set(r.confIdx.filter(i=>i>=0&&i<=2)).size,0)
    const fp=rows.reduce((x,r)=>x+new Set(r.confIdx.filter(i=>i>=3)).size,0)
    sum.recallK123=+(tp/(3*n)).toFixed(3); sum.falseConfirmRate=+(fp/((fx==='light'?10:7)*n)).toFixed(3)
    sum.noMatchStrings=rows.reduce((x,r)=>x+r.confIdx.filter(i=>i<0).length,0)
    sum.reemitK123=rows.reduce((x,r)=>x+r.reemitK123,0)
  }
  if(fx.startsWith('mention')) sum.newFactFound=rows.filter(r=>r.newRun).length
  if(fx==='light') sum.factsEmpty=rows.filter(r=>r.nFacts===0).length
  const ev=rows.map(r=>r.eval).sort((x,y)=>x-y), ms=rows.map(r=>r.ms).sort((x,y)=>x-y)
  Object.assign(sum,{evalMedian:ev[n>>1],evalMax:ev[n-1],msMedian:ms[n>>1],msMax:ms[n-1]})
  console.log(JSON.stringify(sum))
  if(out) fs.writeFileSync(out,JSON.stringify({summary:sum,sys,user,rows},null,1))
}
if(require.main===module) main()
module.exports={armPrompt,HEAD,fixture}
