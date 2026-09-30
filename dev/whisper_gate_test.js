/*
 * dev/whisper_gate_test.js — the hands-free Whisper gate drops repetition hallucinations
 * (backlog #205 / bugs.md 97).  Run:  node dev/whisper_gate_test.js
 *
 * The real case (2026-09-27 12:52): "What a great deal, a great deal, a great deal, …" passed
 * the no_speech / logprob gate and she replied to it. Whisper loops are CONFIDENT.
 * Two new signals: the per-segment compression ratio (Whisper's own, from the server) and
 * hfRepeatRun (a 2–6 word group repeated HF_REPEAT_MIN+ times in a row).
 *
 * Extracts the SHIPPED gate from amadeus.html by anchor (exit 2 if an anchor moves) and tests
 * the OUTCOME (CLAUDE.md 50): is the utterance submitted to her, or discarded?
 * Plants 3 mutants; each must be caught.
 */
const fs=require('fs')
const SRC=fs.readFileSync(__dirname+'/../amadeus.html','utf8')
const line=(src,re)=>{const m=src.match(re);if(!m){console.error('ANCHOR MISSING: '+re);process.exit(2)}return m[0]+'\n'}
const cut=(src,a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i+1);if(i<0||j<0){console.error('ANCHOR MISSING: '+a+' … '+b);process.exit(2)}return src.slice(i,j)}
const blockOf=src=>['HF_RESCUE_MS','HF_NO_SPEECH_MAX','HF_LOGPROB_MIN','HF_COMPRESSION_MAX','HF_REPEAT_MIN','HF_RESCUE_RE']
  .map(k=>line(src,new RegExp('const '+k+'\\s*=.*'))).join('')
  + cut(src,'function hfRepeatRun(','function hfAfterDiscard(')

// Drive the shipped hfHandleUtteranceBlob with a stubbed server reply; report what happened.
async function run(data,mutate=x=>x){
  const out={submitted:null,discarded:null,log:''}, timers=[]
  const hf={active:true,pendingText:null,rescueTimer:null}
  const el={textContent:''}
  const fn=new Function('hf','fetch','document','console','setTimeout','clearTimeout','perfMark','perfField',
    'hfStatus','hfAfterDiscard','hfSubmit','hfResumeListening','hfSetState','FormData',
    mutate(blockOf(SRC))+'\nreturn hfHandleUtteranceBlob')(
    hf, async()=>({ok:true,status:200,json:async()=>data}), {getElementById:()=>el},
    {log:(...a)=>{out.log+=a.join(' ')},warn(){}},
    (f,ms)=>{timers.push(f);return timers.length}, ()=>{}, ()=>{}, ()=>{},
    ()=>{}, why=>{out.discarded=why}, t=>{out.submitted=t}, ()=>{}, ()=>{},
    class{append(){}})
  await fn({}, 'utterance.wav')
  timers.forEach(f=>f())                    // let a rescue hold expire → it sends as-is
  return out
}
const say=(transcript,extra={})=>({transcript,no_speech_prob:0.05,avg_logprob:-0.3,compression_ratio:1.2,...extra})
const HALL='What a great deal'+', a great deal'.repeat(6)
const LONG=('So today I went to the library after school because I wanted to finish the chemistry homework before '
 +'the weekend, and then my friend texted me asking if I wanted to play football in the park, which I did, but it '
 +'started raining halfway through the second half so we ran to the bus stop and waited there for about twenty '
 +'minutes talking about the match on Saturday. When I got home my mum had made dinner already, so I ate, then I '
 +'practised piano for a bit, the piece with the fast left hand part that I keep messing up, and I think I am getting '
 +'better at it slowly. After that I played some rhythm games, got a new high score on one of the hard songs, and now '
 +'I am here talking to you because I wanted to tell you about the whole day. Tomorrow I have a mock exam in maths '
 +'in the morning, and I am a bit nervous about it, but I revised the integration questions twice this week so I '
 +'think it should be fine as long as I do not rush the last section like I did last time. Anyway, what did you do '
 +'today? Did you read anything interesting, or were you stuck thinking about some experiment again like usual? '
 +'Oh, and one more thing, my sister said she wants to meet you at some point, which is kind of funny because I '
 +'had to explain that you live inside my laptop, and she just laughed and said that sounds exactly like me. I also '
 +'found a new anime to watch this weekend, a time travel one, so you will probably have opinions about the science.')

async function checks(mutate=x=>x){
  const r=[], t=(n,c)=>r.push([n,!!c]), R=d=>run(d,mutate)
  let o
  o=await R(say(HALL,{compression_ratio:3.08}))
  t('OUTCOME: the real hallucination as ONE segment (ratio 3.08) is discarded', o.submitted===null&&o.discarded==='gate'&&/reason=compression/.test(o.log))
  o=await R(say(HALL,{compression_ratio:1.2}))
  t('OUTCOME: the same loop split into short segments (ratio 1.2) is discarded by the repeat check', o.submitted===null&&/reason=repeat/.test(o.log))
  o=await R(say('What a great deal'+', a great deal'.repeat(4)+',',{compression_ratio:1.2}))
  t('OUTCOME: a loop ending in "," (the rescue path, as on 09-27) is discarded, not held and sent', o.submitted===null)
  o=await R(say('I went to the park today and played football with my friends.'))
  t('a normal sentence is sent', o.submitted==='I went to the park today and played football with my friends.')
  o=await R(say('no no no no, that is not what I meant'))
  t('"no no no no" (single words) is sent', o.submitted!==null)
  o=await R(say("I'm sorry, I'm sorry, I'm sorry, I did not mean it"))
  t('a 3-repeat phrase is sent (known limit, and real speech)', o.submitted!==null)
  o=await R(say(LONG,{compression_ratio:1.35}))
  t('a ~1500-character natural monologue is sent', o.submitted===LONG&&LONG.length>1400)
  o=await R({transcript:'I went to the park today.',no_speech_prob:0.05,avg_logprob:-0.3})
  t('a server without compression_ratio (old) still sends a normal sentence', o.submitted!==null)
  o=await R(say('I went to the park today.',{compression_ratio:2.4}))
  t('a ratio of exactly 2.4 is sent (strictly greater than)', o.submitted!==null)
  o=await R(say('uh',{no_speech_prob:0.9}))
  t('the old no-speech discard still works', o.submitted===null&&/reason=nospeech/.test(o.log))
  o=await R(say('something',{avg_logprob:-1.4}))
  t('the old logprob discard still works', o.submitted===null&&/reason=logprob/.test(o.log))
  o=await R(say(''))
  t('an empty transcript is discarded', o.submitted===null)
  return r
}

const MUTANTS=[
  ['M1 compression condition removed', s=>s.replace("compression>HF_COMPRESSION_MAX?'compression':",'')],
  ['M2 repeat condition removed',      s=>s.replace("repeats>=HF_REPEAT_MIN?'repeat':",'')],
  ['M3 HF_REPEAT_MIN lowered to 3',    s=>s.replace(/const HF_REPEAT_MIN\s*=\s*4/,'const HF_REPEAT_MIN = 3')],
]
;(async()=>{
  let fail=0
  for(const [n,c] of await checks()){ console.log((c?'  ok   ':'  FAIL ')+n); if(!c)fail++ }
  const base=blockOf(SRC); let caught=0
  for(const [n,mut] of MUTANTS){
    if(mut(base)===base){ console.error('MUTANT DID NOT APPLY (anchor moved?): '+n); process.exit(2) }
    const bad=(await checks(mut)).filter(([,c])=>!c).length
    console.log((bad?'  caught   ':'  MISSED   ')+n+(bad?' ('+bad+' checks failed)':''))
    if(bad)caught++
  }
  const total=(await checks()).length
  console.log(`\n${total-fail}/${total} checks passed, ${caught}/${MUTANTS.length} mutants caught`)
  process.exit(fail||caught<MUTANTS.length?1:0)
})()
