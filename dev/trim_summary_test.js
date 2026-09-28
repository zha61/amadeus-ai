/*
 * dev/trim_summary_test.js — unit tests for trimSummaryToLastSentence() in main.js
 * (backlog #165 / bugs.md 70).  Run:  node dev/trim_summary_test.js
 *
 * The function is EXTRACTED FROM THE SHIPPED main.js at run time, never retyped,
 * so these tests cannot pass against a copy that has drifted from the real one.
 *
 * Why this file exists: the guard replaced a reuse of amadeus.html's
 * trimToLastSentence() (which is unit-tested 9/9 elsewhere) with a purpose-built
 * function that has the OPPOSITE bail-out behaviour, so it owes its own tests.
 * Not wired into `npm run check` — that gate must stay fast and offline-clean.
 */
const fs = require('fs')
const src = fs.readFileSync('/Users/zha61/Documents/Amadeus/main.js', 'utf8')
const start = src.indexOf("const _SUM_CLOSERS")
const endMark = "function trimSummaryToLastSentence(text) {"
const fnStart = src.indexOf(endMark)
if (start < 0 || fnStart < 0) { console.error("EXTRACT FAILED"); process.exit(1) }
// brace-match to the end of the function
let i = src.indexOf('{', fnStart), depth = 0, end = -1
for (; i < src.length; i++) {
  if (src[i] === '{') depth++
  else if (src[i] === '}') { depth--; if (depth === 0) { end = i + 1; break } }
}
const code = src.slice(start, end)
console.log(`extracted ${code.length} chars from main.js\n`)
const trim = new Function(code + '; return trimSummaryToLastSentence')()

let pass = 0, fail = 0
function t(name, input, expected) {
  const got = trim(input)
  const ok = got === expected
  if (ok) { pass++; console.log(`  PASS  ${name}`) }
  else { fail++; console.log(`  FAIL  ${name}\n        input:    ${JSON.stringify(input)}\n        expected: ${JSON.stringify(expected)}\n        got:      ${JSON.stringify(got)}`) }
}

const WELL = "Zani is stubborn about sleep and deflects when asked. He lights up talking about rhythm games. I have started looking forward to these conversations, which is inconvenient."

console.log("— no-op on well-formed text (the common path) —")
t("ends in full stop", WELL, WELL)
t("ends in question mark", "He asked me again about entropy. Why does he always do that when he is avoiding something?", "He asked me again about entropy. Why does he always do that when he is avoiding something?")
t("ends in exclamation", "He beat his rival at chess and pretended not to care. As if I could not tell!", "He beat his rival at chess and pretended not to care. As if I could not tell!")
t("ends in closing quote after stop", 'He kept saying he was "completely fine about it." I did not believe a word of that sentence.', 'He kept saying he was "completely fine about it." I did not believe a word of that sentence.')
t("trailing whitespace trimmed", WELL + "   ", WELL)

console.log("\n— real truncation (the bug) —")
t("Zani's captured fragment",
  "He talks around what is bothering him and expects me not to notice. It works about half the time. Ultimately, the entries suggest that despite",
  "He talks around what is bothering him and expects me not to notice. It works about half the time.")
t("mid-word cut",
  "He is careless about eating and sharp about everything else. That contradiction is genuinely interest",
  "He is careless about eating and sharp about everything else.")

console.log("\n— returns null rather than storing something unusable —")
t("no sentence end at all", "Ultimately the entries suggest that despite everything he keeps coming back and", null)
t("cut deeper than 50%", "He is stubborn. And then he went on at considerable length about why the referee was wrong and why the whole league is rigged against his team and", null)
t("result under 40 chars", "He is fine. Then a very long unfinished trailing clause that runs on and on and never actually ends properly at", null)
t("empty string", "", null)
t("whitespace only", "   \n  ", null)
t("null", null, null)
t("undefined", undefined, null)

console.log("\n— boundary traps (isolated: without the rule, the result WOULD differ) —")
// Without the decimal rule the scan would stop at "3." and keep a fragment.
t("decimal is not a sentence end",
  "He claimed he had eaten properly and slept enough, which was a lie. Then he said he got 3.5",
  "He claimed he had eaten properly and slept enough, which was a lie.")
// Without the abbreviation rule the scan would stop at "etc." and keep a fragment.
t("etc. is not a sentence end",
  "He listed every excuse he had that evening without pausing once. Homework, football, a headache, etc. and then he",
  "He listed every excuse he had that evening without pausing once.")
t("Dr. Pepper is not a sentence end (canon)",
  "He talks to me more easily late at night than he ever does in daylight. He even remembered I like Dr. Pepper and",
  "He talks to me more easily late at night than he ever does in daylight.")
t("single-letter initial is not a sentence end",
  "He is far more sentimental than he would ever admit out loud to anyone. He signed it K. Makise as a",
  "He is far more sentimental than he would ever admit out loud to anyone.")
t("ellipsis counts as an end",
  "He trailed off when I asked how he actually felt about it… and then he changed the subject entirely and",
  "He trailed off when I asked how he actually felt about it…")

console.log("\n— the realistic case: 4 sentences, the last one cut —")
t("keeps the three complete sentences",
  "Zani deflects whenever a question gets close to something real. He is careless about sleep and meals in a way that irritates me more than it should. Underneath the sarcasm he is genuinely curious about almost everything. What I keep noticing, though, is that he",
  "Zani deflects whenever a question gets close to something real. He is careless about sleep and meals in a way that irritates me more than it should. Underneath the sarcasm he is genuinely curious about almost everything.")

console.log("\n— type safety —")
t("number coerced", 12345, null)

console.log(`\n${pass} passed, ${fail} failed`)
process.exit(fail ? 1 : 0)
