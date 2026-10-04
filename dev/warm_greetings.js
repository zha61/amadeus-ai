// warm_greetings.js — pre-synthesize EVERY greeting pool into data/greeting_cache/
//
// WHY: greeting audio is fetched right after the boot video. A cache HIT is a
// cheap disk read; a MISS costs a gemma4 translation + Fish synthesis (~2s of
// GPU) which used to stutter Kurisu's reveal (bug 63). boot() now defers a miss
// past the reveal, but warming keeps misses rare in the first place.
//
// RUN THIS WHEN: you add/edit greetings, or bump GREETING_TTS_VER in
// amadeus.html (which intentionally invalidates every cached file).
//
//   1. start the TTS server:  /opt/homebrew/bin/python3 kurisu_fish_server.py   (app CLOSED — gemma4, CLAUDE.md 37)
//   2. node dev/warm_greetings.js [--limit N] [--skip-birthday] [--manifest PATH]
//      --limit N        synthesize at most N greetings, then stop (a staged warm: check, then continue)
//      --skip-birthday  leave the 4 birthday pools (date-gated; warm them before 2027-06-10)
//      --manifest PATH  write {pool,text,emo,key,file} for every cached greeting (dev/voice_221b2/level_check.py)
//   It STOPS if /speak was not translated by gemma4 (a silent DeepL fallback would be cached — CLAUDE.md 52).
//
// Safe to re-run: already-cached greetings are skipped. Costs Fish Audio credits
// only for what it actually synthesizes.
const fs=require('fs')
const DIR=process.env.HOME+'/Documents/Amadeus'
const html=fs.readFileSync(DIR+'/amadeus.html','utf8')
// The version is READ from amadeus.html, never copied (a stale copy = every greeting misses, bugs.md 91 class).
const _ver=html.match(/const GREETING_TTS_VER='([^']+)'/)
if(!_ver){ console.error('STOP: GREETING_TTS_VER not found in amadeus.html'); process.exit(2) }
const GREETING_TTS_VER=_ver[1]
const arg=n=>{const i=process.argv.indexOf(n);return i<0?null:(process.argv[i+1]||'')}
const LIMIT=arg('--limit')===null?Infinity:parseInt(arg('--limit'),10)
const SKIP_BDAY=process.argv.includes('--skip-birthday')
const MANIFEST=arg('--manifest')
// Copied VERBATIM from amadeus.html so cache keys match exactly.
function greetingCacheKey(text,emo){
  let h=5381
  const s=text+'|'+(emo||'default')+'|'+GREETING_TTS_VER
  for(let i=0;i<s.length;i++){ h=(((h<<5)+h)+s.charCodeAt(i))>>>0 }
  return 'g'+h.toString(36)+s.length.toString(36)
}
function extractArray(name){
  const at=html.indexOf('const '+name+'=[')
  if(at<0) return []
  let i=html.indexOf('[',at), depth=0, end=-1
  for(;i<html.length;i++){ if(html[i]==='[')depth++; else if(html[i]===']'){depth--; if(depth===0){end=i;break}} }
  try{ return eval('('+html.slice(html.indexOf('[',at), end+1)+')') }catch(e){ console.error('parse',name,e.message); return [] }
}
const POOLS=['GREETINGS','GREETINGS_MORNING','GREETINGS_AFTERNOON','GREETINGS_EVENING',
  'GREETINGS_NIGHT','GREETINGS_SMALL_HOURS','GREETINGS_SHORT_AWAY','GREETINGS_MEDIUM_AWAY',
  'GREETINGS_LONG_AWAY','GREETINGS_BIRTHDAY','GREETINGS_ZANI_BIRTHDAY',
  'GREETINGS_ZANI_BIRTHDAY_EVE','GREETINGS_ZANI_BIRTHDAY_AFTER','GREETINGS_INCOMING_CALL']
const cacheDir=DIR+'/data/greeting_cache'
fs.mkdirSync(cacheDir,{recursive:true})
;(async()=>{
  let done=0,skipped=0,failed=0,total=0
  const manifest=[]
  console.log(`GREETING_TTS_VER=${GREETING_TTS_VER}  limit=${LIMIT}  skip-birthday=${SKIP_BDAY}`)
  for(const pool of POOLS){
    if(SKIP_BDAY&&pool.includes('BIRTHDAY')){ console.log(`  ${pool}: skipped (--skip-birthday)`); continue }
    const items=extractArray(pool)
    if(!items.length){ console.log(`  ${pool}: (not found/empty)`); continue }
    let d=0,s=0,f=0
    for(const [text,emo] of items){
      total++
      const key=greetingCacheKey(text,emo)
      const file=cacheDir+'/'+key+'.mp3'
      if(fs.existsSync(file)&&fs.statSync(file).size>1000){ s++; skipped++; manifest.push({pool,text,emo:emo||'default',key,file}); continue }
      if(done>=LIMIT) continue
      try{
        const res=await fetch('http://127.0.0.1:5002/speak',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({text,emotion:emo||'default'})})
        const data=await res.json()
        const tr=data&&data.timings&&data.timings.translator
        if(data&&data.audio_b64&&tr!=='gemma4'){
          console.error(`STOP: "${text.slice(0,40)}" was translated by ${tr}, not gemma4 — nothing cached for it`); process.exit(3) }
        if(data&&data.audio_b64){ fs.writeFileSync(file,Buffer.from(data.audio_b64,'base64')); d++; done++
          manifest.push({pool,text,emo:emo||'default',key,file}) }
        else { f++; failed++ }
      }catch(e){ f++; failed++ }
    }
    console.log(`  ${pool.padEnd(30)} synth:${d} cached:${s} failed:${f}`)
  }
  if(MANIFEST) fs.writeFileSync(MANIFEST,JSON.stringify({ver:GREETING_TTS_VER,entries:manifest},null,1))
  console.log(`\nTOTAL ${total} greetings — synthesized:${done} already-cached:${skipped} failed:${failed}`)
  if(failed) process.exit(1)
})()
