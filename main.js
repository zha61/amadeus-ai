const { app, BrowserWindow, nativeImage, ipcMain, protocol, net, session, desktopCapturer } = require('electron')
const path = require('path')
const { spawn, execSync, exec } = require('child_process')
const os = require('os')
const fs = require('fs')
const { pathToFileURL } = require('url')
const crypto = require('crypto')   // stage-2 summary input fingerprint (bugs.md 72)

// Custom protocol scheme for serving local assets directly from disk.
// MUST be registered BEFORE app is ready. Used by the boot video to bypass
// the http.server entirely — http.server has been a source of timing bugs on
// quick relaunches and the boot video black-screen issue is the symptom.
protocol.registerSchemesAsPrivileged([{
  scheme: 'amadeus-asset',
  privileges: { bypassCSP: true, supportFetchAPI: true, stream: true, secure: true, standard: true }
}])

// Hardcoded Python path — Electron's spawn doesn't inherit Terminal's PATH
const PYTHON = '/opt/homebrew/bin/python3'
// Hardcoded Ollama path — same reason. Run `which ollama` in Terminal to find your path.
const OLLAMA = '/usr/local/bin/ollama'
const AMADEUS_DIR = path.join(os.homedir(), 'Documents', 'Amadeus')
const ICON_PATH = path.join(AMADEUS_DIR, 'assets', 'icon.icns')

// ── LOG SINK (backlog #203 / #204) ──
// Before this, every server wrote into a PIPE that nothing read: its output was lost,
// and a full pipe BLOCKS the writer (measured ~131 KB; the fish server would hang
// after ~150 replies).  Now the OS writes each server's output straight into a file
// (the launchd StandardOutPath pattern) — no pipe exists, so nothing can fill up.
// main.js and renderer consoles are kept too, so fallbacks leave evidence (#204).
// data/ is git-ignored: these logs hold her replies and his words and stay local.
// Disk: 2 MB + one .1 backup per file, 6 files → 24 MB worst case.
const util = require('util')
const LOG_DIR = path.join(AMADEUS_DIR, 'data', 'logs')
const LOG_ROTATE_BYTES = 2 * 1024 * 1024
const LOG_SESSION_CAP_BYTES = 5 * 1024 * 1024
function rotateLogIfLarge(file, limit = LOG_ROTATE_BYTES) {
  try { if (fs.statSync(file).size > limit) fs.renameSync(file, file + '.1') } catch (e) {}
}
// stdio for a child: an append-mode file descriptor.  If the file cannot be opened
// it falls back to 'ignore' — NEVER to 'pipe', which is the hang this removes.
function childStdio(name, dir = LOG_DIR) {
  try {
    fs.mkdirSync(dir, { recursive: true })
    const file = path.join(dir, name + '.log')
    rotateLogIfLarge(file)
    const fd = fs.openSync(file, 'a')
    return { stdio: ['ignore', fd, fd], fd }
  } catch (e) {
    return { stdio: 'ignore', fd: null }
  }
}
// spawn a python child with its output in data/logs/<name>.log.  PYTHONUNBUFFERED:
// a file is block-buffered (8 KB), so lines would arrive late and die with the process.
function spawnLogged(name, args, dir = LOG_DIR) {
  const { stdio, fd } = childStdio(name, dir)
  let proc = null
  try {
    proc = spawn(PYTHON, args, { cwd: AMADEUS_DIR, stdio, env: { ...process.env, PYTHONUNBUFFERED: '1' } })
  } finally {
    if (fd != null) {
      try { fs.writeSync(fd, `=== ${new Date().toISOString()} spawn ${name} pid ${proc && proc.pid} ===\n`) } catch (e) {}
      try { fs.closeSync(fd) } catch (e) {}   // the child holds its own copy
    }
  }
  return proc
}
// A line writer that never throws (CLAUDE.md 48a) and stops at a per-session cap.
function makeLineWriter(file, cap = LOG_SESSION_CAP_BYTES) {
  let written = 0, capped = false
  return (line) => {
    try {
      if (capped) return
      const s = line.endsWith('\n') ? line : line + '\n'
      const n = Buffer.byteLength(s)
      if (written + n > cap) {
        capped = true
        fs.appendFileSync(file, `${new Date().toISOString()} [log] session cap of ${cap} bytes reached — later lines dropped\n`)
        return
      }
      fs.appendFileSync(file, s)
      written += n
    } catch (e) {}
  }
}
function openLineLog(name, dir = LOG_DIR) {
  try { fs.mkdirSync(dir, { recursive: true }) } catch (e) {}
  const file = path.join(dir, name + '.log')
  rotateLogIfLarge(file)
  const write = makeLineWriter(file)
  write(`=== ${new Date().toISOString()} ${name} log start, main pid ${process.pid} ===`)
  return write
}
// main.js console → data/logs/main.log (the watchdog, page reload, diary, summary and
// facts-close messages had nowhere to go).  The original console still runs.
function installMainLog(dir = LOG_DIR) {
  const write = openLineLog('main', dir)
  for (const level of ['log', 'warn', 'error']) {
    const orig = console[level].bind(console)
    console[level] = (...args) => {
      try { orig(...args) } catch (e) {}
      try { write(`${new Date().toISOString()} ${level.toUpperCase()} ${util.format(...args)}`) } catch (e) {}
    }
  }
}
// Renderer console → data/logs/renderer.log.  Keeps EVERY warning and error, and every
// info line except two known-noisy LipSync debug lines (~4/s while she speaks).  A
// deny-list, not an allow-list: a filter that hides data looks like lost data (CLAUDE.md 48d).
const RENDERER_LOG_DROP = [/^\[LipSync\] peak:/, /^\[LipSync ticker\]/]
function rendererLineWanted(level, message) {
  if (level === 'warning' || level === 'error') return true
  return !RENDERER_LOG_DROP.some(re => re.test(message))
}
let _rendererWrite = null
function attachRendererLog(wc, dir = LOG_DIR) {
  try {
    if (!_rendererWrite) _rendererWrite = openLineLog('renderer', dir)
    // ONE parameter only (backlog #219): Electron 35 prints a deprecation warning when ANY
    // 'console-message' listener declares more than one.  details.level is a string —
    // debug / info / warning / error (probed on Electron 35.7.5, 2026-09-29).
    wc.on('console-message', (details) => {
      try {
        const level = typeof details?.level === 'string' ? details.level : 'info'
        const message = String(details?.message ?? '')
        if (!rendererLineWanted(level, message)) return
        _rendererWrite(`${new Date().toISOString()} ${level.toUpperCase()} ${message}`)
      } catch (e) {}
    })
    wc.on('render-process-gone', (_e, d) => {
      try { console.warn('[main] renderer process gone:', d && d.reason, 'exitCode', d && d.exitCode) } catch (e) {}
    })
  } catch (e) {}
}

let mainWindow, ttsProcess, serverProcess, ragProcess, whisperProcess
let isIncomingCall = false  // set true when launched with --incoming-call; appends ?incomingCall=1

app.setName('Amadeus')

// Single-instance lock — prevents a second Electron process from starting while
// the first is still alive (e.g. during diary-on-close save).
// Second launch attempt is silently ignored; the existing window comes to front.
const gotTheLock = app.requestSingleInstanceLock()
// Only the instance that holds the lock logs — a second launch must not rotate its files.
if (gotTheLock) installMainLog()
if (!gotTheLock) {
  app.quit()  // second instance — exit immediately, first instance handles it
} else {
  app.on('second-instance', (_event, argv) => {
    if (argv.includes('--incoming-call')) {
      // AmadeusCall scheduler accepted a call while Amadeus was already open.
      // Show + focus the existing window and trigger the incoming call greeting.
      if (mainWindow && !mainWindow.isDestroyed()) {
        if (mainWindow.isMinimized()) mainWindow.restore()
        mainWindow.show()
        mainWindow.focus()
        mainWindow.webContents.send('incoming-call-accepted')
      }
      return
    }
    // Normal relaunch — bring window to front
    if (mainWindow && !mainWindow.isDestroyed()) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })
}

// ── DIARY-ON-CLOSE COORDINATOR (Phase 3) ──
// On quit (any path: Cmd+Q OR window X button), this orchestrates:
// ask renderer for conversation, run Ollama, send entry back to renderer for save,
// wait for save confirmation, then allow exit. Has a hard timeout — if anything
// stalls, we don't block exit indefinitely.

// Sequential budget: diary Ollama (≤12s) + summary Ollama (≤12s) + IPC round-trips (≤8s) + headroom (8s) = 40s
const DIARY_TIMEOUT_MS = 40000         // outer race timeout — covers diary + summary in sequence
const OLLAMA_FETCH_TIMEOUT_MS = 12000  // per-call timeout (diary generation)
const SUMMARY_FETCH_TIMEOUT_MS = 12000 // per-call timeout (summary generation)
// Backlog #202 facts pass: realistic 3.6s median / 5.4s max, dense 20-fact chat 21.8s max
// (n=30).  The renderer aborts at 24s, so its 'done' always beats this.  The step runs
// LAST, so if DIARY_TIMEOUT_MS runs out first it is the only step lost.
const FACTS_CLOSE_WAIT_MS = 25000
const MEMORY_WINDOW_SIZE = 7           // must match amadeus.html

// ── SUMMARY TRUNCATION GUARD (backlog #165 — extends bugs.md 67/40) ─────────
// The stage-2 rollup used to be stored with no completeness check at all, so a
// capped generation ("...the entries suggest that despite") was written to
// amadeus_diary_summary and injected into EVERY prompt as LONG-TERM IMPRESSIONS
// until the next diary write.  Measured Aug 26 2026, n=30 per arm: at
// num_predict 100 that happened 19/30 = 63% of the time; at 180, 0/30
// (Fisher one-sided p = 2.7e-08).
//
// DELIBERATELY NOT a copy of amadeus.html's trimToLastSentence().  That one KEEPS
// the fragment when trimming would cost more than ~60% of the text, because a chat
// reply has ALREADY BEEN SPOKEN — losing most of what she said out loud is worse
// than a rough ending.  Nothing here is spoken.  A summary fragment sits in every
// prompt until the next close, so the trade-off inverts: trim willingly, and
// return null rather than store something unusable.  Different rule, different
// name, nothing to keep in sync — this is not duplication.
//
// null is safe by construction: the caller's `if (summaryText)` guards BOTH the
// IPC send AND the watermark advance, so null keeps the previous good summary and
// simply retries on the next close.
//
// Not gated on done_reason: trimming well-formed text is a no-op (the last
// terminal punctuation IS the final character), so this also catches EOS emitted
// mid-sentence, and does not depend on an Ollama response field that already
// changed shape between 0.21.0 and 0.32.15.
const _SUM_CLOSERS   = '"\'”’)]'  // quotes/brackets that may follow the full stop
const _SUM_MIN_CHARS = 40    // below this it is not a usable memory block
const _SUM_MIN_KEEP  = 0.5   // keep <50% of the text => something went wrong; retry instead
// Periods that are NOT sentence ends.  "Dr. Pepper" is canon for this character,
// so a naive backward scan would cut a summary at "...he mentioned Dr."
const _SUM_ABBREV = new Set(['dr','mr','mrs','ms','st','prof','vs','etc','no','e.g','i.e','a.m','p.m'])

function trimSummaryToLastSentence(text) {
  if (!text) return null
  const t = String(text).trim()
  if (!t) return null
  let end = -1
  for (let i = t.length - 1; i >= 0; i--) {
    if (!'.!?…'.includes(t[i])) continue
    let j = i + 1
    while (j < t.length && _SUM_CLOSERS.includes(t[j])) j++
    // A real sentence end is followed by whitespace or nothing.  This rejects
    // decimals ("3.5 hours") without needing to know they are numbers.
    if (j < t.length && !/\s/.test(t[j])) continue
    // Reject known abbreviations: look at the word immediately before the dot.
    const before = t.slice(0, i).match(/([A-Za-z.]+)$/)
    if (before && _SUM_ABBREV.has(before[1].toLowerCase())) continue
    // Reject a single-letter initial ("K. Makise").
    if (before && before[1].length === 1) continue
    end = j
    break
  }
  if (end < 0) return null                                  // no complete sentence at all
  const cand = t.slice(0, end).trim()
  if (cand.length < _SUM_MIN_CHARS) return null             // too little left to be a memory
  if (cand.length < t.length * _SUM_MIN_KEEP) return null    // cut too deep — retry next close
  return cand
}

let diaryHandled = false   // set true after diary work done; short-circuits second pass
let diaryInProgress = false  // prevents re-entry mid-flow

async function runDiaryOnClose() {
  if (diaryInProgress) return
  if (!mainWindow || mainWindow.isDestroyed()) return
  diaryInProgress = true

  try {
    // Step 1: ask renderer for the conversation + model name
    // (passing model avoids hardcoding it here — single source of truth in amadeus.html)
    const data = await new Promise((resolve) => {
      const timer = setTimeout(() => resolve(null), 3000)
      ipcMain.once('conversation-response', (_e, payload) => {
        clearTimeout(timer)
        resolve(payload)
      })
      mainWindow.webContents.send('request-conversation')
    })

    if (!data || !data.conv) return  // no conversation or renderer didn't respond — skip

    // Show overlay only now that we know a conversation exists
    mainWindow.webContents.send('show-saving-overlay')

    const { conv, model, diarySystemPrompt } = data
    const ollamaModel = model || 'gemma4:latest'  // fallback if renderer somehow didn't send model
    if (!diarySystemPrompt) console.warn('[main:diary-on-close] renderer sent no diarySystemPrompt — using the main.js fallback prompt (backlog #210)')
    // Fallback only — the renderer always sends diarySystemPrompt (bugs.md 57).
    // The PLAIN LANGUAGE clause is copied VERBATIM from buildDiarySystemPrompt()
    // in amadeus.html (bugs.md 69): the diary is injected into every later prompt
    // as "in your own past words", and without a vocabulary constraint she quotes
    // lab prose back verbatim.  That exact wording is what was measured — do not
    // reword it here without re-running the comparison.  This fallback had drifted
    // and still carried the pre-69 text until Aug 26 2026.
    const diarySysContent = diarySystemPrompt || 'You are Kurisu Makise writing a private diary entry about a conversation you just had as Amadeus. Write in first person in Kurisu voice — precise, slightly tsundere, occasionally vulnerable. 2-4 sentences. Reflect personally, not robotically. Start with "Entry —"'
      + '\n\nPLAIN LANGUAGE — this is a private journal, not a lab report. Write it the way you would THINK it, in ordinary words. NEVER describe yourself or him in technical or biological terms: no "biological hardware", "processing unit", "physiological", "calibrate", "parameters", "efficiency", "optimal", "metabolic", "system". Say "tired" not "depleted", "sleep" not "adequate rest", "eat" not "nutritional intake". If a sentence sounds like something from a paper, rewrite it as something a person would actually write about their own evening.'

    // Step 2: call Ollama from main process to generate entry
    let entryText = null
    try {
      const controller = new AbortController()
      const fetchTimer = setTimeout(() => controller.abort(), OLLAMA_FETCH_TIMEOUT_MS)
      const res = await fetch('http://127.0.0.1:11434/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: ollamaModel,
          messages: [
            { role: 'system', content: diarySysContent },
            { role: 'user', content: 'Write a brief diary entry reflecting on this conversation:\n' + conv }
          ],
          stream: false,
          keep_alive: '30m',
          think: false,
          // num_ctx MUST match sendMsg's 8192 — a different value forces a full
          // model reload (KV buffer resize), which can eat most of the 12s diary
          // timeout and lose the entry. Extends bugs 33/34 to ALL Ollama calls.
          options: { temperature: 0.9, num_ctx: 8192 }
        }),
        signal: controller.signal
      })
      clearTimeout(fetchTimer)
      const result = await res.json()
      entryText = result.message?.content || null
    } catch (e) {
      console.warn('[main:diary-on-close] Ollama call failed:', e.message)
      return
    }

    if (!entryText) return

    // Step 3: send back to renderer for localStorage save, wait for confirm
    await new Promise((resolve) => {
      const timer = setTimeout(() => resolve(), 3000)
      ipcMain.once('diary-save-complete', () => {
        clearTimeout(timer)
        resolve()
      })
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('save-diary-entry', entryText)
      } else {
        resolve()  // window died mid-flow; can't save, just unblock
      }
    })

    // Step 4: Stage 2 summary — ask renderer for the full diary array + watermark.
    // Only runs if there are more entries than the sliding window (> 7), and only
    // regenerates when the text actually fed to the summariser has CHANGED.
    // Shares the outer DIARY_TIMEOUT_MS race — never blocks close indefinitely.
    const entriesData = await new Promise((resolve) => {
      const timer = setTimeout(() => resolve(null), 3000)
      ipcMain.once('diary-entries-response', (_e, payload) => {
        clearTimeout(timer)
        resolve(payload)
      })
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('request-diary-entries')
      } else {
        resolve(null)
      }
    })

    if (entriesData && Array.isArray(entriesData.entries) && entriesData.entries.length > MEMORY_WINDOW_SIZE) {
      // entries are newest-first; slice(7) gives older entries, also newest-first → reverse for chronological
      const olderEntries = entriesData.entries.slice(MEMORY_WINDOW_SIZE).reverse()
      const summaryInput = olderEntries.map(e => {
        const text = (e.text || '').replace(/^Entry\s*[—-]\s*/i, '').trim()
        const date = e.date || '(unknown date)'
        return `${date}: ${text}`
      }).join('\n\n')

      // WATERMARK = a fingerprint of the exact text fed to the summariser (bugs.md 72).
      // It used to be `entries.length`, regenerating when the count GREW.  The diary is
      // capped at 50 (amadeus.html: unshift then pop), so once a user reaches the cap the
      // length is pinned at 50 and `50 > 50` is false FOREVER — the long-term memory
      // freezes permanently at whatever was last stored, and no later fix to the generator
      // can ever take effect.  Found live on Zani's machine: entries 50, watermark 50, the
      // summary byte-identical across a full close/relaunch cycle.
      //
      // A fingerprint is correct at the cap, and also correct if entries are ever edited or
      // deleted (a count cannot see either).  Comparison is by STRING so the old numeric
      // value simply fails to match and regenerates once, which is the migration.
      const inputFingerprint = crypto.createHash('sha1').update(summaryInput).digest('hex').slice(0, 16)
      const storedMark = (entriesData.watermark === null || entriesData.watermark === undefined)
        ? '' : String(entriesData.watermark)
      if (inputFingerprint !== storedMark) {

        let summaryText = null
        try {
          const controller = new AbortController()
          const summaryTimer = setTimeout(() => controller.abort(), SUMMARY_FETCH_TIMEOUT_MS)
          const sres = await fetch('http://127.0.0.1:11434/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              model: ollamaModel,
              messages: [
                // REGISTER CONSTRAINT (backlog #168 — bugs.md 71, extends bugs.md 69).
                // This block is injected into EVERY prompt as LONG-TERM IMPRESSIONS, so it is
                // subject to CLAUDE.md rule 42 exactly like the diary was.  Unconstrained, it
                // came out as a case file — measured 29/30 (97%) therapy/analysis register:
                // "exhibits", "underlying anxieties", "validation", "reliance on".  With this
                // clause: 2/30 (7%), Fisher one-sided p < 0.00001, replicated on fresh samples.
                // Remembered content is NOT reduced (themes carried 3.97 -> 4.47, permutation
                // p = 0.186) — a high p is the good outcome there.
                //
                // The banned-word sentence and the substitutions are VERBATIM from
                // buildDiarySystemPrompt() in amadeus.html (bugs.md 69).  Only the framing
                // sentence is adapted, because a rollup is not "a private journal entry".
                // THIS adapted wording is what was measured — do not reword it without
                // re-running the comparison.
                //
                // A stronger variant that ALSO dropped the "memory system ... about Zani"
                // framing scored a perfect 0/30 on register and was REJECTED: it cut
                // remembered content in half (4.4 -> 2.1 themes, some summaries carrying
                // none). It optimised the metric and destroyed the thing the metric stands
                // for. Do not "improve" this by making it more first-person.
                { role: 'system', content: 'You are Kurisu Makise\'s memory system. Summarise these older diary entries into 3-4 sentences capturing lasting impressions, recurring themes, and emotional patterns about Zani. Be concise and specific. Output only the summary text, no preamble, no labels.'
                  + ' PLAIN LANGUAGE — this is your own memory, not a lab report or a case file. Write it the way you would THINK it, in ordinary words. NEVER describe yourself or him in technical, clinical or biological terms: no "biological hardware", "processing unit", "physiological", "calibrate", "parameters", "efficiency", "optimal", "metabolic", "system". Say "tired" not "depleted", "sleep" not "adequate rest", "eat" not "nutritional intake". If a sentence sounds like something from a paper, rewrite it as something a person would actually write.' },
                { role: 'user', content: summaryInput }
              ],
              stream: false,
              keep_alive: '30m',
              think: false,
              // num_predict 180, NOT 100 (backlog #165).  The prompt above asks for
              // "3-4 sentences" of dense prose, which measured 103 tokens median and
              // 132 max over 30 runs on a worst-case 43-entry input (the diary caps at
              // 50, the window is 7).  At 100 that truncated 63% of the time.  180
              // leaves ~27% headroom over the observed max and costs +0.11s median.
              // 220 was measured too and buys nothing.  num_ctx MUST stay 8192 (bugs 33/34/51).
              options: { temperature: 0.7, num_predict: 180, num_ctx: 8192 }
            }),
            signal: controller.signal
          })
          clearTimeout(summaryTimer)
          const sresult = await sres.json()
          const rawSummary = sresult.message?.content?.trim() || null
          if (rawSummary && sresult.done_reason === 'length') {
            console.warn('[main:diary-summary] hit the num_predict cap (done_reason=length) — trimming to the last complete sentence')
          }
          summaryText = trimSummaryToLastSentence(rawSummary)
          if (rawSummary && !summaryText) {
            console.warn('[main:diary-summary] result unusable after trim — keeping the previous summary, will retry next close')
          }
        } catch (e) {
          console.warn('[main:diary-summary] Ollama call failed:', e.message)
        }

        if (summaryText) {
          await new Promise((resolve) => {
            const timer = setTimeout(() => resolve(), 3000)
            ipcMain.once('diary-summary-saved', () => {
              clearTimeout(timer)
              resolve()
            })
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.send('save-diary-summary', {
                summary: summaryText,
                watermark: inputFingerprint
              })
            } else {
              resolve()
            }
          })
        }
      }
    }

    // Step 5 (backlog #202): the once-per-session facts pass.  The renderer runs it —
    // one prompt, one merge, one store — and main only waits.  LAST on purpose: the
    // diary and summary keep all of their time.  Skipped unless the page said it has
    // the handler (data.factsClose), so a page/build mismatch can never cost a 25s wait.
    if (data.factsClose === true) {
      await new Promise((resolve) => {
        if (!mainWindow || mainWindow.isDestroyed()) return resolve()
        const onDone = () => { clearTimeout(timer); resolve() }
        const timer = setTimeout(() => {
          ipcMain.removeListener('facts-extraction-done', onDone)
          console.warn('[main:facts-close] no reply in ' + FACTS_CLOSE_WAIT_MS + 'ms — continuing to quit')
          resolve()
        }, FACTS_CLOSE_WAIT_MS)
        ipcMain.once('facts-extraction-done', onDone)
        mainWindow.webContents.send('run-facts-extraction')
      })
    }
  } finally {
    diaryInProgress = false
  }
}

// Shared exit-with-diary function — called from BOTH window close AND app before-quit.
// Sets diaryHandled before calling app.quit() so the second-pass before-quit short-circuits.
async function runDiaryWithExit() {
  if (diaryHandled) return  // already done, don't repeat
  diaryHandled = true
  try {
    await Promise.race([
      runDiaryOnClose(),
      new Promise(resolve => setTimeout(resolve, DIARY_TIMEOUT_MS))
    ])
  } catch (e) {
    console.warn('[main:exit] diary error:', e.message)
  }
  // Force-clear diaryInProgress: if timeout won the race, runDiaryOnClose() may still
  // be running its own async work but we need to allow app.quit() to proceed past the
  // before-quit guard which checks !diaryInProgress. Without this, the app would
  // deadlock — app.quit() gets blocked because diaryInProgress is still true.
  diaryInProgress = false
  app.quit()  // re-trigger normal quit; diaryHandled flag short-circuits before-quit
}

function createWindow() {
  const icon = nativeImage.createFromPath(ICON_PATH)
  if (process.platform === 'darwin' && !icon.isEmpty()) app.dock.setIcon(icon)

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 640,
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#000000',
    icon: icon,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,        // Allow renderer to fetch local APIs (Ollama, TTS server)
      autoplayPolicy: 'no-user-gesture-required',
      preload: path.join(__dirname, 'preload.js')
    }
  })

  // If this window is being created in response to an incoming call accept,
  // append ?incomingCall=1 so boot() skips the boot video and uses the
  // incoming call greeting. Reset the flag immediately so normal relaunches
  // are never affected.
  const incomingCallParam = isIncomingCall ? '&incomingCall=1' : ''
  isIncomingCall = false
  const htmlUrl = `http://localhost:8765/amadeus.html?v=${Date.now()}${incomingCallParam}`
  attachRendererLog(mainWindow.webContents)   // backlog #204 — before loadURL, so boot lines are kept
  mainWindow.loadURL(htmlUrl)
  // Retry reuses the SAME URL (including ?incomingCall=1 if present) so the
  // incoming-call boot path isn't silently dropped on a slow http.server start.
  let loadRetries = 0
  mainWindow.webContents.on('did-fail-load', () => {
    // Bounded: if http.server never comes up, stop after 10 attempts (~15s)
    // instead of retrying forever.
    if (++loadRetries > 10) {
      console.warn('[main] page load failed 10 times — giving up retries')
      return
    }
    setTimeout(() => mainWindow && mainWindow.loadURL(htmlUrl), 1500)
  })
  // Phase 3: catch X-button close path (doesn't fire 'before-quit', only 'close' then 'closed').
  // Allow normal close ONLY when diary is fully done (handled AND not in flight).
  // diaryHandled is set BEFORE diary work starts — so a second close attempt during
  // save would otherwise see diaryHandled=true and let the window die mid-save.
  // Pause heavy rendering and BGM when window is hidden (Cmd+H / programmatic hide).
  // Resume when window comes back. This keeps Amadeus invisible to the user's system
  // resources while it waits in the background for the scheduled incoming call.
  mainWindow.on('hide', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('window-hidden')
    }
  })
  mainWindow.on('show', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('window-shown')
    }
  })

  mainWindow.on('close', (event) => {
    if (diaryHandled && !diaryInProgress) return  // truly done, allow normal close
    event.preventDefault()
    if (!diaryHandled) runDiaryWithExit()
    // If diary is already running (second close attempt during save), just block
    // and let the in-flight runDiaryWithExit complete normally.
  })
  mainWindow.on('closed', () => {
    mainWindow = null
    // Stamp the exit time so the renderer on the next launch can compute how
    // long to wait before engaging the audio renderer (CoreAudio safety margin).
    try {
      fs.writeFileSync(path.join(app.getPath('userData'), '.last-exit'), Date.now().toString())
    } catch(e) {}
    stopServices()
    // Do NOT call process.exit() here. That kills only the main process and
    // leaves Electron's audio service child process running, which keeps
    // CoreAudio locked. The new instance then hits AUDIO_RENDERER_ERROR.
    // Instead, let Electron's natural quit (initiated by app.quit() in
    // runDiaryWithExit) proceed — it sends proper IPC shutdown messages to
    // all child processes so they release CoreAudio before exiting.
  })
}

// ── SERVICE WATCHDOG (#80) ──
// If a python child dies mid-session, Kurisu silently loses voice/UI/RAG/mic
// until relaunch. Respawn crashed children with linear backoff, capped so a
// truly broken server can't respawn-loop forever. Intentional kills are guarded
// by isShuttingDown (set at the top of stopServices()).
let isShuttingDown = false
const RESPAWN_MAX = 3
const RESPAWN_BASE_MS = 2000
const respawnCounts = { tts: 0, http: 0, rag: 0, whisper: 0 }
function superviseChild(name, proc, respawnFn) {
  if (!proc) return
  proc.on('exit', (code, signal) => {
    if (isShuttingDown) return
    if (respawnCounts[name] >= RESPAWN_MAX) {
      console.warn(`[main:watchdog] ${name} exited (code ${code}) — respawn limit reached, giving up`)
      return
    }
    respawnCounts[name] += 1
    const delay = RESPAWN_BASE_MS * respawnCounts[name]
    console.warn(`[main:watchdog] ${name} exited (code ${code}, signal ${signal}) — respawn ${respawnCounts[name]}/${RESPAWN_MAX} in ${delay}ms`)
    setTimeout(() => { if (!isShuttingDown) respawnFn() }, delay)
  })
}

// ── STALE-SERVER KILL (backlog #150, bugs.md 100) ──
// Before a spawn, free the port from an ORPHANED Amadeus server (a crash or force-quit left it).
// The old `lsof -ti:PORT | xargs kill -9` killed EVERY process with a socket on the port: a
// CLIENT too (measured 2026-10-05 — a held connection was listed beside the server), and any
// other app on that port.  Now only the LISTENER, and only if it is OUR server: the same script
// resolved against the process's own folder (so a hand-started `python3 kurisu_rag_server.py`
// counts), or `http.server <port>` run from AMADEUS_DIR.  Anything else is NOT killed, and is
// logged (CLAUDE.md 52).  The single-instance lock means no live Amadeus owns these servers, so
// a match is an orphan.  Every call is bounded (2 s) and never throws into a spawn.
const PORT_EXEC_OPTS = { timeout: 2000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }
const AMADEUS_DIRS = (() => {
  const dirs = [path.resolve(AMADEUS_DIR)]
  try { dirs.push(fs.realpathSync(AMADEUS_DIR)) } catch (e) {}
  return dirs
})()
function listenerPids(port) {
  try {
    return execSync(`lsof -nP -t -iTCP:${port} -sTCP:LISTEN`, PORT_EXEC_OPTS)
      .split('\n').map(Number).filter(n => n > 0)
  } catch (e) {
    if (e.status === 1 && !String(e.stdout || '').trim()) return []   // exit 1, no output = nobody listens
    console.warn(`[main:ports] lsof failed for port ${port}: ${e.message} — nothing killed`)
    return []
  }
}
function procArgs(pid) {
  try { return execSync(`ps -ww -o args= -p ${pid}`, PORT_EXEC_OPTS).trim() } catch (e) { return '' }
}
function procCwd(pid) {
  try {
    const line = execSync(`lsof -a -nP -p ${pid} -d cwd -Fn`, PORT_EXEC_OPTS)
      .split('\n').find(l => l.startsWith('n'))
    return line ? line.slice(1) : ''
  } catch (e) { return '' }
}
// target: { script: 'kurisu_fish_server.py' } or { module: 'http.server' }.
// An unreadable cwd or command line never matches — the safe default is "do not kill".
function isOurServer(args, cwd, port, target) {
  const argv = args.split(/\s+/).filter(Boolean)
  if (target.script) {
    if (!cwd) return false
    const want = AMADEUS_DIRS.map(d => path.join(d, target.script))
    return argv.slice(1).some(a => path.basename(a) === target.script && want.includes(path.resolve(cwd, a)))
  }
  const m = argv.indexOf('-m')
  return m > 0 && argv[m + 1] === target.module && argv.includes(String(port)) && AMADEUS_DIRS.includes(cwd)
}
function killStaleServer(port, target) {
  for (const pid of listenerPids(port)) {
    if (pid === process.pid) continue
    const args = procArgs(pid)
    if (isOurServer(args, procCwd(pid), port, target)) {
      try {
        process.kill(pid, 'SIGKILL')
        console.log(`[main:ports] killed a stale Amadeus server on port ${port} (pid ${pid})`)
      } catch (e) { console.warn(`[main:ports] could not kill pid ${pid} on port ${port}: ${e.message}`) }
    } else {
      console.warn(`[main:ports] port ${port} is held by another program (pid ${pid}: ${args.slice(0, 160) || 'command unknown'}) — NOT killed; the Amadeus server cannot start on this port`)
    }
  }
}
// ── end STALE-SERVER KILL ──

function spawnTtsServer() {
  // Free port 5002 from a stale fish server only (#150) before spawning a fresh one
  killStaleServer(5002, { script: 'kurisu_fish_server.py' })
  ttsProcess = spawnLogged('fish', [path.join(AMADEUS_DIR, 'kurisu_fish_server.py')])
  ttsProcess.on('error', (err) => {
    console.warn('[main:tts] spawn failed:', err.message, '- TTS unavailable this session')
  })
  superviseChild('tts', ttsProcess, spawnTtsServer)
}

function spawnHttpServer() {
  // Free port 8765 from a stale Amadeus http.server only (#150) — a crash can leave one holding it
  killStaleServer(8765, { module: 'http.server' })
  serverProcess = spawnLogged('http', ['-m', 'http.server', '8765'])
  serverProcess.on('error', (err) => {
    console.warn('[main:http] spawn failed:', err.message, '- UI server unavailable this session')
  })
  superviseChild('http', serverProcess, spawnHttpServer)
}

// poll=true (default, used by the watchdog on respawn) polls /health in the
// background purely for logging. The boot path passes false because it awaits
// waitForRagServer() itself as part of the pre-window gate.
function spawnRagServer(poll = true) {
  killStaleServer(5003, { script: 'kurisu_rag_server.py' })   // #150
  ragProcess = spawnLogged('rag', [path.join(AMADEUS_DIR, 'kurisu_rag_server.py')])
  ragProcess.on('error', (err) => {
    console.warn('[main:rag] spawn failed:', err.message, '- RAG unavailable this session')
  })
  superviseChild('rag', ragProcess, spawnRagServer)
  // Background poll (logging only) — skipped when the caller awaits readiness itself.
  if (poll) waitForRagServer()
}

function spawnWhisperServer() {
  killStaleServer(5004, { script: 'kurisu_whisper_server.py' })   // #150
  whisperProcess = spawnLogged('whisper', [path.join(AMADEUS_DIR, 'kurisu_whisper_server.py')])
  whisperProcess.on('error', (err) => {
    console.warn('[main:whisper] spawn failed:', err.message, '- voice input unavailable this session')
  })
  superviseChild('whisper', whisperProcess, spawnWhisperServer)
}

function startServices() {
  // No OLLAMA_FLASH_ATTENTION here (backlog #169): Ollama runs from Ollama.app under launchd,
  // so a variable set by main.js never reached it — the live llama-server shows
  // `--flash-attn auto`.  Ollama decides flash attention itself in every start path.

  // Set OLLAMA_ORIGINS so Electron renderer can connect regardless of how Ollama started.
  // Fire-and-forget — directly-spawned Ollama gets env vars via spawn options below.
  // These are belt-and-suspenders for externally-started Ollama; no need to block.
  exec('launchctl setenv OLLAMA_ORIGINS "*"', () => {})
  exec('launchctl setenv OLLAMA_HOST "127.0.0.1:11434"', () => {})

  // Only start Ollama if not already running — never kill it
  // Killing forces model to reload causing connection errors
  const ollamaRunning = (() => {
    try { execSync('pgrep -x Ollama || pgrep -x ollama'); return true } catch(e) { return false }
  })()
  if (!ollamaRunning) {
    try {
      const ollamaProc = spawn(OLLAMA, ['serve'], {
        env: { ...process.env, OLLAMA_ORIGINS: '*', OLLAMA_HOST: '127.0.0.1:11434' },
        detached: true, stdio: 'ignore'
      })
      // Catch async spawn errors (e.g., binary not found) so they don't crash Electron with uncaught exception popup
      ollamaProc.on('error', (err) => {
        console.warn('[main:ollama] spawn failed:', err.message, '- check OLLAMA path constant in main.js')
      })
    } catch (e) {
      console.warn('[main:ollama] spawn threw:', e.message)
    }
  }
  spawnTtsServer()
  spawnHttpServer()

  // RAG and Whisper servers are spawned with delays after window open — see app.whenReady() below
}

function stopServices() {
  // Tell the watchdog these kills are intentional — no respawns from here on.
  isShuttingDown = true
  // Kill only processes WE started (via stored handles).
  // Do NOT use lsof port-kills here — on quick relaunch the new instance may have
  // already claimed those ports, and lsof would kill the new instance's servers.
  if (ttsProcess) { try { ttsProcess.kill() } catch(e) {} ttsProcess = null }
  if (serverProcess) { try { serverProcess.kill() } catch(e) {} serverProcess = null }
  if (ragProcess) { try { ragProcess.kill() } catch(e) {} ragProcess = null }
  if (whisperProcess) { try { whisperProcess.kill() } catch(e) {} whisperProcess = null }
  try { require('child_process').execSync('pkill -x afplay') } catch(e) {}
}

async function waitForHttpServer(maxAttempts = 20, intervalMs = 200) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch('http://localhost:8765/amadeus.html', { method: 'HEAD' })
      if (res.ok) { console.log('[main:http] http.server ready.'); return true }
    } catch(e) {}
    await new Promise(r => setTimeout(r, intervalMs))
  }
  console.warn('[main:http] http.server did not respond in 4s — opening anyway.')
  return false
}

async function waitForRagServer(maxAttempts = 20, intervalMs = 500) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch('http://127.0.0.1:5003/health')
      if (res.ok) { console.log('[main:rag] RAG server ready.'); return true }
    } catch(e) {}
    await new Promise(r => setTimeout(r, intervalMs))
  }
  console.warn('[main:rag] RAG server did not respond in 10s — opening window without RAG.')
  return false
}

// Loads gemma4 into RAM during the pre-window 5s delay.
// Accepts an AbortSignal so the caller can cancel if the window opens before it finishes —
// preventing a stale 'hi' request from racing against the renderer's KV-cache prewarm.
// This only ensures the model binary is resident; KV cache is built by the renderer's
// prewarmOllama() which sends the real system prompt with the correct num_ctx.
async function prewarmOllamaMain(signal) {
  // Poll until Ollama is ready — it may have just been spawned by startServices()
  for (let i = 0; i < 10; i++) {
    if (signal.aborted) return
    try {
      const res = await fetch('http://127.0.0.1:11434/api/tags', { signal })
      if (res.ok) break
    } catch(e) {
      if (signal.aborted) return
    }
    await new Promise(r => setTimeout(r, 500))
  }
  if (signal.aborted) return
  try {
    await fetch('http://127.0.0.1:11434/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'gemma4:latest',
        messages: [{ role: 'user', content: 'hi' }],
        stream: false,
        think: false,
        // num_ctx MUST be 8192 — without it the model loads with a 4096 KV buffer
        // and the renderer's 8192 prewarm forces a full model reload from disk (a ~9.6 GB
        // READ — the file size, not RAM; see backlog #172) during the boot video
        // (double disk I/O = video stutter). Extends bug 33 to this call.
        options: { num_predict: 1, temperature: 0, num_ctx: 8192 },
        keep_alive: '30m'
      }),
      signal
    })
    console.log('[main:prewarm] gemma4 loaded into RAM')
  } catch(e) {
    if (e.name !== 'AbortError') console.log('[main:prewarm] skipped:', e.message)
  }
}

// Only run startup if we're the first (and only) instance
if (gotTheLock) {
  app.whenReady().then(async () => {
    // Register the amadeus-asset:// handler. Streams files from AMADEUS_DIR
    // straight off disk — no http.server, no cache, no port races. The boot
    // video uses this scheme so it's immune to all http.server-related timing
    // bugs that were causing the black-screen-on-quick-relaunch issue.
    protocol.handle('amadeus-asset', (request) => {
      try {
        const url = new URL(request.url)
        // Root files: "amadeus-asset://amadeus_startup.mp4" → host holds the name.
        // Nested paths: "amadeus-asset://data/greeting_cache/x.mp3" → host + pathname
        // = data/greeting_cache/x.mp3. The URL must carry the FULL path under
        // AMADEUS_DIR — without "data/" the cache never hit for ten weeks (bugs.md 91).
        const filename = decodeURIComponent(url.host + url.pathname)
        const filePath = path.join(AMADEUS_DIR, filename)
        // Path traversal guard: must resolve inside AMADEUS_DIR
        const resolved = path.resolve(filePath)
        if (!resolved.startsWith(path.resolve(AMADEUS_DIR))) {
          return new Response('forbidden', { status: 403 })
        }
        // Delegate to Electron's native file fetcher. Critically, this gives
        // us proper HTTP range-request support (Accept-Ranges/Content-Range),
        // which HTML5 <video> needs for reliable progressive loading. A simple
        // new Response(buffer) doesn't expose ranges and was the cause of
        // intermittent boot-video load failures even on cold boots.
        // The try/catch around this handler only covers the SYNCHRONOUS part —
        // net.fetch returns a promise, and a missing file (e.g. a greeting-cache
        // miss) REJECTS it, surfacing as an unhandled net::ERR_FILE_NOT_FOUND
        // instead of a clean 404. Catch on the promise itself.
        return net.fetch(pathToFileURL(resolved).href, {
          bypassCustomProtocolHandlers: true
        }).catch((e) => {
          console.warn('[main:amadeus-asset] fetch failed:', filename, e.message)
          return new Response('not found', { status: 404 })
        })
      } catch (e) {
        console.warn('[main:amadeus-asset]', e.message)
        return new Response('not found', { status: 404 })
      }
    })

    // Screen-capture routing for Study Mode (B1): the renderer's
    // getDisplayMedia() lands here. Prefer the macOS system picker (user
    // explicitly chooses which screen/window to share — privacy-first, same UX
    // as Copilot Vision); the callback is the fallback for older macOS, which
    // shares the primary screen. Requires the OS Screen Recording permission
    // for Amadeus.app (macOS prompts on first use).
    session.defaultSession.setDisplayMediaRequestHandler((request, callback) => {
      desktopCapturer.getSources({ types: ['screen'] }).then((sources) => {
        if (sources && sources.length) callback({ video: sources[0] })
        else callback({})
      }).catch((e) => { console.warn('[main:display-media]', e.message); callback({}) })
    }, { useSystemPicker: true })

    // Greeting audio disk cache (#32) — renderer sends synthesized greeting MP3s
    // here; future boots read them back via amadeus-asset://data/greeting_cache/<key>.mp3
    // (no Fish Audio call, works offline, instant playback). Key is sanitized to
    // [a-z0-9_] and size-capped so this channel can't write arbitrary files.
    ipcMain.on('cache-greeting-audio', (_e, payload) => {
      try {
        if (!payload || typeof payload.key !== 'string' || typeof payload.b64 !== 'string') return
        if (!/^[a-z0-9_]+$/.test(payload.key) || payload.b64.length > 3000000) return
        const dir = path.join(AMADEUS_DIR, 'data', 'greeting_cache')
        fs.mkdirSync(dir, { recursive: true })
        fs.writeFileSync(path.join(dir, payload.key + '.mp3'), Buffer.from(payload.b64, 'base64'))
      } catch (e) { console.warn('[main:greeting-cache]', e.message) }
    })

    // Do NOT clear cache — clearing removes the boot video from Chromium's disk
    // cache, causing black screen on quick relaunch (window opens after waitForRagServer,
    // video has zero time to buffer). amadeus.html is cache-busted via ?v= timestamp
    // in loadURL below; video and other static assets stay cached across sessions.
    startServices()

    // 5s pre-window delay — window intentionally doesn't open immediately on click.
    // During this time, prewarmOllamaMain() loads gemma4 from disk into RAM so the
    // renderer's prewarmOllama() only pays KV-cache prefill cost (~0.5s) during the
    // boot video instead of model-load + prefill. AbortController cancels the prewarm
    // at exactly 5s — prevents a still-running 'hi' request from arriving late and
    // evicting the renderer's system-prompt KV cache (race condition guard).
    const prewarmAbort = new AbortController()
    prewarmOllamaMain(prewarmAbort.signal)   // fire-and-forget, bounded by abort below

    // Bug 62: the RAG server used to spawn 20s AFTER the window opened, and its
    // startup is heavy (~10s: ChromaDB load + a bge-m3 warm-up embed, which is
    // GPU work). That left it cold for the first message — fetchRagContext then
    // burned its full 4s timeout — and put GPU load right where the user was
    // interacting. Spawning it HERE moves that cost into the pre-window phase,
    // where nothing is rendered and nothing competes: the boot video still
    // decodes on an idle system (bug 60) and RAG is genuinely warm by message 1.
    // The server only starts serving /health AFTER its warm-up finishes, so a
    // healthy response is a true readiness signal, not just "process alive".
    spawnRagServer(false)                    // false = we await readiness ourselves

    // Adaptive gate: open the window as soon as everything is actually ready,
    // rather than after a fixed guess. waitForRagServer is self-bounded (10s,
    // then resolves false), so a broken RAG can never block launch.
    await Promise.all([
      waitForHttpServer(),
      waitForRagServer(),
      new Promise(r => setTimeout(r, 5000))  // minimum 5s (CoreAudio/renderer settle)
    ])
    prewarmAbort.abort()  // cancel prewarm if still in-flight — renderer takes over

    // CoreAudio safety margin — on quick relaunch the old instance's audio
    // service child may still hold the CoreAudio device lock. The .last-exit
    // stamp (written in mainWindow.on('closed')) lets us measure the gap and
    // wait it out before opening the window, which is what triggers audio init.
    // 3s gap is enough: will-quit → child IPC shutdown → CoreAudio release
    // takes ~1-2s on Apple Silicon. Without this, quick relaunch hits
    // AUDIO_RENDERER_ERROR → boot video plays silently or fails entirely.
    const COREAUDIO_SAFE_GAP_MS = 3000
    try {
      const lastExitPath = path.join(app.getPath('userData'), '.last-exit')
      const lastExit = parseInt(fs.readFileSync(lastExitPath, 'utf8'))
      const gap = Date.now() - lastExit
      if (!isNaN(lastExit) && gap < COREAUDIO_SAFE_GAP_MS) {
        const wait = COREAUDIO_SAFE_GAP_MS - gap
        console.log(`[main] Quick relaunch (${gap}ms since last exit) — waiting ${wait}ms for CoreAudio release`)
        await new Promise(r => setTimeout(r, wait))
      }
    } catch(e) {} // No .last-exit on first ever launch — fine, skip

    // If launched by AmadeusCall scheduler (accept-call → open --args --incoming-call),
    // skip the boot video and use the incoming call greeting instead.
    if (process.argv.includes('--incoming-call')) {
      isIncomingCall = true
    }

    // Open window immediately so boot video can start
    createWindow()

    // The RAG server is spawned in the pre-window phase above (bug 62), not here.

    // Whisper server spawned 30s after window open, clear of the boot video (9.78s) and
    // the greeting (CLAUDE.md 36).  Since backlog #226 the server does NOT load the model at
    // start — the spawn costs only its Python/MLX imports; whisper-large-v3-turbo loads on
    // the first mic press (#226b prewarm).  Until this timer fires the mic cannot work.
    setTimeout(spawnWhisperServer, 30000)
  })
}

app.on('window-all-closed', () => {
  stopServices()
  // Don't process.exit() here either — same reason as above. app.quit() is
  // already in progress from runDiaryWithExit; Electron will fire will-quit
  // and exit cleanly on its own.
  // On Windows/Linux (non-macOS), quit explicitly if no windows remain.
  if (process.platform !== 'darwin') app.quit()
})

app.on('will-quit', () => {
  // #86: stamp exit time here too — mainWindow.on('closed') writes it on the
  // normal path, but a quit that never destroys the window (or a crash-adjacent
  // teardown) would skip it, breaking the CoreAudio quick-relaunch safety gap
  // on the next boot. Later write wins = more accurate timestamp; duplicate is harmless.
  try {
    fs.writeFileSync(path.join(app.getPath('userData'), '.last-exit'), Date.now().toString())
  } catch(e) {}
  // Electron's natural shutdown — all child processes (audio service, GPU)
  // receive proper IPC shutdown and release CoreAudio before exiting.
  // Safety valve: 5s is generous enough that we never force-exit while
  // children are still cleanly releasing CoreAudio. .unref() means this
  // timer doesn't keep the event loop alive if Electron exits normally.
  //
  // IMPORTANT: app.exit(0) not process.exit(0). process.exit() kills only
  // the Node.js main process and orphans Electron's audio service child,
  // leaving it holding the CoreAudio device — which is why Spotify loses
  // audio after an Amadeus close on the paths where this valve fires.
  // app.exit() sends proper shutdown IPC to all Electron sub-processes
  // (audio service, GPU process) so CoreAudio is released before exit.
  const t = setTimeout(() => app.exit(0), 5000)
  if (t && t.unref) t.unref()
})
app.on('before-quit', (event) => {
  // Phase 3: catch Cmd+Q path. Allow quit ONLY when diary is fully done (handled AND not in flight).
  // Same reasoning as the 'close' handler — prevents a second quit attempt
  // during save from killing the in-flight diary work.
  // (stopServices is idempotent due to existing try/catch blocks — calling it from multiple paths is harmless.)
  if (diaryHandled && !diaryInProgress) {
    stopServices()
    return
  }
  // First pass — intercept, run diary, then re-quit
  event.preventDefault()
  if (!diaryHandled) runDiaryWithExit()
  // If already in progress, just block and let it finish
})
