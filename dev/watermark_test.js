/*
 * dev/watermark_test.js — the stage-2 summary regeneration gate (bugs.md 72).
 * Run:  node dev/watermark_test.js
 *
 * The gate logic is EXTRACTED FROM THE SHIPPED main.js at run time, never retyped,
 * so these tests cannot pass against a copy that has drifted from the real one.
 *
 * The bug this locks down: the watermark used to be `entries.length`, and the diary
 * is capped at 50 — so at the cap `50 > 50` was false forever and the long-term
 * memory froze permanently.  Found live on Zani's machine.
 */
const fs=require('fs'), crypto=require('crypto')
const src=fs.readFileSync('/Users/zha61/Documents/Amadeus/main.js','utf8')
const start=src.indexOf('      // entries are newest-first; slice(7) gives older entries')
const end=src.indexOf('      if (inputFingerprint !== storedMark) {')
if(start<0||end<0){console.error('EXTRACT FAILED');process.exit(1)}
const block=src.slice(start,end)
console.log(`extracted ${block.length} chars of real gate logic from main.js\n`)
const MEMORY_WINDOW_SIZE=7
// shouldRegen(entries, storedWatermark) -> {regen, fingerprint}
const shouldRegen=new Function('entriesData','MEMORY_WINDOW_SIZE','crypto',
  block+'\n return {regen: inputFingerprint !== storedMark, fingerprint: inputFingerprint}')

const mk=n=>Array.from({length:n},(_,i)=>({date:`day${n-i}`,text:`Entry — thing number ${n-i}`}))
let pass=0,fail=0
const t=(name,cond)=>{cond?(pass++,console.log('  PASS  '+name)):(fail++,console.log('  FAIL  '+name))}

// 1. Zani's exact live state: 50 entries, old numeric watermark 50
const capped=mk(50)
const r1=shouldRegen({entries:capped,watermark:50},MEMORY_WINDOW_SIZE,crypto)
t("THE BUG: 50 entries + numeric watermark 50 now regenerates", r1.regen===true)

// 2. after that save, the same input must NOT regenerate
const r2=shouldRegen({entries:capped,watermark:r1.fingerprint},MEMORY_WINDOW_SIZE,crypto)
t("idempotent: unchanged input does not regenerate", r2.regen===false)

// 3. a new entry at the cap (unshift + pop) changes the older set -> must regenerate
const next=[{date:'day51',text:'Entry — brand new'},...capped]; next.pop()
t("cap holds at 50 after unshift+pop", next.length===50)
const r3=shouldRegen({entries:next,watermark:r1.fingerprint},MEMORY_WINDOW_SIZE,crypto)
t("new entry at the cap regenerates (this is what was broken)", r3.regen===true)

// 4. only the newest-7 window edited -> older set identical -> no regeneration
const winEdit=capped.map((e,i)=>i<7?{...e,text:'edited '+i}:e)
const r4=shouldRegen({entries:winEdit,watermark:r1.fingerprint},MEMORY_WINDOW_SIZE,crypto)
t("edits confined to the 7-entry window do not regenerate", r4.regen===false)

// 5. an OLD entry edited -> a count could never see this
const oldEdit=capped.map((e,i)=>i===30?{...e,text:'materially different'}:e)
const r5=shouldRegen({entries:oldEdit,watermark:r1.fingerprint},MEMORY_WINDOW_SIZE,crypto)
t("an edited OLD entry regenerates (a count cannot see this)", r5.regen===true)

// 6. missing / empty watermark
t("null watermark regenerates",      shouldRegen({entries:capped,watermark:null},MEMORY_WINDOW_SIZE,crypto).regen===true)
t("undefined watermark regenerates", shouldRegen({entries:capped},MEMORY_WINDOW_SIZE,crypto).regen===true)
t("empty-string watermark regenerates", shouldRegen({entries:capped,watermark:''},MEMORY_WINDOW_SIZE,crypto).regen===true)

// 7. pre-cap growth still behaves as before
const g8=mk(8), g9=mk(9)
const rg=shouldRegen({entries:g8,watermark:''},MEMORY_WINDOW_SIZE,crypto)
t("8 entries: first summary generates", rg.regen===true)
t("9 entries: growth regenerates", shouldRegen({entries:g9,watermark:rg.fingerprint},MEMORY_WINDOW_SIZE,crypto).regen===true)

// 8. fingerprint shape
t("fingerprint is 16 hex chars", /^[0-9a-f]{16}$/.test(r1.fingerprint))
t("old numeric value can never collide with a fingerprint", !/^[0-9a-f]{16}$/.test('50'))

console.log(`\n${pass} passed, ${fail} failed`)
process.exit(fail?1:0)
