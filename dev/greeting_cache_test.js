#!/usr/bin/env node
// Greeting audio cache — the READ path must resolve to the file the WRITER saved.
//
// bugs.md 91: from 2026-07-13 to 2026-09-27 the renderer read
//   amadeus-asset://greeting_cache/<key>.mp3  →  ~/Documents/Amadeus/greeting_cache/…
// while main.js wrote ~/Documents/Amadeus/data/greeting_cache/…  The cache never
// hit once, every boot greeting was synthesised after her reveal, and nothing on
// screen said so — the miss path is a silent, working fallback.
//
// This tests the OUTCOME (CLAUDE.md 50): for every greeting she can pick, the file
// the app looks for is the file the app wrote. It reads the shipped code BY ANCHOR
// and fails loudly if an anchor moves, rather than testing a stale copy.
//
// Usage: node dev/greeting_cache_test.js [path/to/amadeus.html]
const fs = require('fs'), path = require('path'), os = require('os')
const ROOT = path.join(__dirname, '..')
const htmlPath = process.argv[2] || path.join(ROOT, 'amadeus.html')
const html = fs.readFileSync(htmlPath, 'utf8')
const mainJs = fs.readFileSync(path.join(ROOT, 'main.js'), 'utf8')
let pass = 0, fail = 0
const ok = (cond, msg) => { if (cond) { pass++; console.log('  \x1b[32m✓\x1b[0m ' + msg) } else { fail++; console.log('  \x1b[31m✗\x1b[0m ' + msg) } }
const need = (m, what) => { if (!m) { console.log('\x1b[31mANCHOR MISSING: ' + what + ' — update this test, do not skip it.\x1b[0m'); process.exit(2) } return m }

console.log('\nGreeting cache path test  (' + path.relative(ROOT, htmlPath) + ')\n')

// 1. Renderer: the URL both readers fetch.
const fnBody = name => need(html.match(new RegExp('async function ' + name + '\\([\\s\\S]*?\\n}')), 'function ' + name)[0]
const readPrefix = name => need(fnBody(name).match(/fetch\('amadeus-asset:\/\/([^']*)'\+key\+'\.mp3'\)/), 'amadeus-asset fetch in ' + name)[1]
const pIs = readPrefix('greetingIsCached'), pFetch = readPrefix('fetchGreetingAudio')
ok(pIs === pFetch, 'greetingIsCached and fetchGreetingAudio read the same URL prefix ("' + pIs + '")')

// 2. main.js: the protocol handler's URL → file rule, asserted verbatim.
ok(/const filename = decodeURIComponent\(url\.host \+ url\.pathname\)/.test(mainJs) &&
   /const filePath = path\.join\(AMADEUS_DIR, filename\)/.test(mainJs),
   'handler maps amadeus-asset://<host><path> to AMADEUS_DIR/<host><path> (rule this test re-implements)')

// 3. main.js: the directory the cache-greeting-audio IPC writes to.
const w = need(mainJs.match(/ipcMain\.on\('cache-greeting-audio'[\s\S]*?const dir = path\.join\(AMADEUS_DIR, ([^)]*)\)/), 'cache-greeting-audio writer')
const writeParts = w[1].split(',').map(s => s.trim().replace(/^'|'$/g, ''))
const AMADEUS_DIR = path.join(os.homedir(), 'Documents', 'Amadeus')
const writeDir = path.join(AMADEUS_DIR, ...writeParts)

// 4. Every greeting she can pick: key exactly as the renderer computes it.
const ver = need(html.match(/const GREETING_TTS_VER='([^']*)'/), 'GREETING_TTS_VER')[1]
const keyFn = new Function('GREETING_TTS_VER', need(html.match(/function greetingCacheKey\(text,emo\)\{[\s\S]*?\n\}/), 'greetingCacheKey')[0] + '\nreturn greetingCacheKey')(ver)
const greetings = []
for (const m of html.matchAll(/const (GREETINGS[A-Z_]*)\s*=\s*(\[[\s\S]*?\n\])/g)) greetings.push(...eval(m[2]))
ok(greetings.length >= 50, greetings.length + ' greetings found across all GREETINGS arrays')

const readPathFor = key => {
  const url = new URL('amadeus-asset://' + pIs + key + '.mp3')
  return path.resolve(path.join(AMADEUS_DIR, decodeURIComponent(url.host + url.pathname)))
}
const mismatched = greetings.filter(g => { const k = keyFn(g[0], g[1]); return readPathFor(k) !== path.join(writeDir, k + '.mp3') })
ok(mismatched.length === 0, 'OUTCOME: every greeting is READ from the file the writer SAVES' +
   (mismatched.length ? '  → reads ' + path.dirname(readPathFor('x')) + ' but writes ' + writeDir : ''))

// 5. On this machine: the cache the app already paid for is reachable.
if (fs.existsSync(writeDir)) {
  const reachable = greetings.filter(g => fs.existsSync(readPathFor(keyFn(g[0], g[1])))).length
  ok(reachable > 0, reachable + '/' + greetings.length + ' greetings resolve to an existing cached file')
} else console.log('  - ' + writeDir + ' absent (fresh checkout) — existence check skipped')

console.log('\n' + (fail ? '\x1b[31m' + fail + ' failed, ' + pass + ' passed.\x1b[0m' : '\x1b[32mAll ' + pass + ' checks passed.\x1b[0m'))
process.exit(fail ? 1 : 0)
