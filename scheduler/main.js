'use strict'
const { app, BrowserWindow, ipcMain, protocol, net, Notification } = require('electron')
const path   = require('path')
const fs     = require('fs')
const os     = require('os')
const { exec, execSync } = require('child_process')
const { pathToFileURL }  = require('url')

// ── No GPU needed — call window is pure CSS/DOM, no WebGL ────────────────────
app.disableHardwareAcceleration()

// amadeus-asset:// must be registered before app is ready
protocol.registerSchemesAsPrivileged([{
  scheme: 'amadeus-asset',
  privileges: { bypassCSP: true, supportFetchAPI: true, stream: true, secure: true, standard: true }
}])

const AMADEUS_DIR    = path.join(os.homedir(), 'Documents', 'Amadeus')
const SCHEDULER_PATH = path.join(AMADEUS_DIR, 'amadeus_scheduler.json')

// ── Single-instance lock — only one scheduler at a time ──────────────────────
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', (_event, argv) => {
    // Terminal test trigger: open AmadeusCall.app --args --test-call
    if (argv.includes('--test-call')) {
      // Guard: BrowserWindow cannot be created before app is ready.
      // appReady is set true inside whenReady() — if a second instance somehow
      // connects before that point, silently drop the trigger rather than crash.
      if (appReady) fireIncomingCall()
    }
  })
}

// ── State ────────────────────────────────────────────────────────────────────
let callWindow   = null
let appReady     = false  // guards second-instance handler against pre-ready BrowserWindow creation
let callTimerSet = false  // prevents multiple setTimeout timers stacking for the same scheduled call

// ── Scheduler helpers ────────────────────────────────────────────────────────
function getTodayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function readScheduler() {
  try {
    const raw = fs.readFileSync(SCHEDULER_PATH, 'utf8')
    const p   = JSON.parse(raw)
    if (p && typeof p.lastCallDate === 'string' &&
        typeof p.scheduledTime === 'number' &&
        typeof p.callFired === 'boolean') return p
  } catch(e) {}
  return null
}

function writeScheduler(data) {
  try { fs.writeFileSync(SCHEDULER_PATH, JSON.stringify(data, null, 2)) } catch(e) {}
}

// Check whether the main Amadeus app is currently running
function isAmadeusRunning() {
  try { execSync('pgrep -x Amadeus', { stdio: 'pipe' }); return true } catch(e) { return false }
}

// Derive Amadeus.app path from our own executable location.
// Both apps sit in the same dist/mac-arm64/ directory.
// exe = .../dist/mac-arm64/AmadeusCall.app/Contents/MacOS/AmadeusCall
// 3 levels up from dirname(exe) → dist/mac-arm64/
function getAmadeusAppPath() {
  const exe     = app.getPath('exe')
  const distDir = path.resolve(path.dirname(exe), '..', '..', '..')
  return path.join(distDir, 'Amadeus.app')
}

// ── Call window ──────────────────────────────────────────────────────────────
function createCallWindow() {
  if (callWindow && !callWindow.isDestroyed()) { callWindow.focus(); return }
  callWindow = new BrowserWindow({
    width: 340, height: 580,
    alwaysOnTop: true,
    resizable: false,
    frame: false,
    backgroundColor: '#060404',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      // Load preload from AMADEUS_DIR so it doesn't need to be in the asar
      preload: path.join(AMADEUS_DIR, 'preload_call.js')
    }
  })
  // call-window.html and amadeus_logo.png are served from AMADEUS_DIR
  // via the amadeus-asset:// protocol registered below
  callWindow.loadURL('amadeus-asset://call-window.html')
  callWindow.on('closed', () => { callWindow = null })
}

function fireIncomingCall() {
  console.log('[scheduler] Firing incoming call')

  // Silent notification — supplementary UX, call window is always shown directly
  if (Notification.isSupported()) {
    try {
      const notif = new Notification({
        title: 'Amadeus',
        body:  'Kurisu wants to talk to you.',
        silent: true
      })
      notif.on('click', () => {
        callWindow && !callWindow.isDestroyed() ? callWindow.focus() : createCallWindow()
      })
      notif.show()
    } catch(e) {
      console.warn('[scheduler] Notification failed:', e.message)
    }
  }

  createCallWindow()
}

// ── IPC: call window → scheduler ─────────────────────────────────────────────
ipcMain.on('decline-call', () => {
  if (callWindow && !callWindow.isDestroyed()) callWindow.close()
})

ipcMain.on('accept-call', () => {
  if (callWindow && !callWindow.isDestroyed()) callWindow.close()

  setTimeout(() => {
    const amadeusPath = getAmadeusAppPath()
    console.log('[scheduler] Opening Amadeus at:', amadeusPath)
    // open -n forces a new OS-level launch even if Amadeus is already running.
    // If it IS running, Electron's single-instance lock kicks in: the new process
    // quits immediately and the running instance receives a 'second-instance'
    // event with --incoming-call in its argv — triggering the greeting without
    // re-booting. If it's NOT running, a fresh Amadeus boots with ?incomingCall=1.
    exec(`open -n "${amadeusPath}" --args --incoming-call`, (err) => {
      if (err) console.warn('[scheduler] Failed to open Amadeus.app:', err.message)
    })
  }, 150)
})

// ── Daily scheduler loop ─────────────────────────────────────────────────────
function scheduleCall() {
  const today          = getTodayStr()
  const now            = new Date()
  const currentMinutes = now.getHours() * 60 + now.getMinutes()

  let sched = readScheduler()

  // Already fired today — nothing to do until tomorrow
  if (sched && sched.lastCallDate === today && sched.callFired === true) {
    console.log('[scheduler] Already fired today — sleeping until tomorrow')
    return
  }

  let scheduledTime
  if (sched && sched.lastCallDate === today && sched.callFired === false) {
    // Same day, not yet fired — reuse the existing random pick
    scheduledTime = sched.scheduledTime
    console.log(`[scheduler] Reusing today's time: ${Math.floor(scheduledTime/60)}:${String(scheduledTime%60).padStart(2,'0')}`)
  } else {
    // New day (or missing/corrupt file) — pick a random time in [780, 1260] (13:00–21:00)
    scheduledTime = Math.floor(Math.random() * (1260 - 780 + 1)) + 780
    writeScheduler({ lastCallDate: today, scheduledTime, callFired: false })
    console.log(`[scheduler] New day — call at ${Math.floor(scheduledTime/60)}:${String(scheduledTime%60).padStart(2,'0')}`)
  }

  // If the scheduled time has already passed today, mark fired and do nothing
  if (currentMinutes >= scheduledTime) {
    console.log('[scheduler] Scheduled time already passed — marking fired')
    writeScheduler({ lastCallDate: today, scheduledTime, callFired: true })
    return
  }

  // Guard: if a timer is already counting down for today's call, don't add another.
  // Without this, repeated hourly scheduleCall() invocations (from the hourly loop)
  // would stack multiple timers all firing at the same scheduled time.
  if (callTimerSet) {
    console.log('[scheduler] Timer already armed — skipping duplicate')
    return
  }

  const delayMs = (scheduledTime - currentMinutes) * 60 * 1000
  const hh = String(Math.floor(scheduledTime / 60)).padStart(2, '0')
  const mm = String(scheduledTime % 60).padStart(2, '0')
  console.log(`[scheduler] Timer set for ${hh}:${mm} (in ${Math.round(delayMs / 60000)} min)`)

  callTimerSet = true
  // No .unref() — this timer MUST keep the process alive so the call fires
  setTimeout(() => {
    callTimerSet = false  // reset so tomorrow's scheduleCall() can arm a new timer
    // #151: re-read state — macOS delays timers across sleep, so the hourly
    // check may have already marked today fired before this timer got to run.
    // Without this re-check, a wake-up could pop a call already counted.
    const fireToday = getTodayStr()
    const cur = readScheduler()
    if (cur && cur.lastCallDate === fireToday && cur.callFired === true) {
      console.log('[scheduler] Timer fired but call already marked fired — skipping')
      return
    }
    // #152: a timer armed before midnight can fire after it. Stamping the OLD
    // captured date would leave the NEW day unfired → two calls in one day.
    // Discard the stale timer; the hourly loop schedules today's call properly.
    if (fireToday !== today) {
      console.log('[scheduler] Timer fired on a different day than armed — discarding')
      return
    }
    if (isAmadeusRunning()) {
      // User is already in a chat session — skip the call silently
      console.log('[scheduler] Amadeus is open at call time — skipping')
      writeScheduler({ lastCallDate: today, scheduledTime, callFired: true })
      return
    }
    // Mark fired before opening window (idempotent even if window creation fails)
    writeScheduler({ lastCallDate: today, scheduledTime, callFired: true })
    fireIncomingCall()
  }, delayMs)
}

// Run scheduleCall() every hour so the scheduler stays accurate after Mac sleep/wake.
// macOS pauses the monotonic clock during sleep, so a single long setTimeout can
// drift by however long the machine was asleep. An hourly wake-up limits drift to
// ≤1 hour. scheduleCall() is idempotent (callTimerSet guard + callFired check),
// so calling it repeatedly is safe — it only arms the call timer once per day.
function scheduleHourlyCheck() {
  setTimeout(() => {
    scheduleCall()
    scheduleHourlyCheck()   // keep the loop going indefinitely
  }, 60 * 60 * 1000)        // 1 hour
}

// ── Boot ─────────────────────────────────────────────────────────────────────
if (gotTheLock) {
  app.whenReady().then(() => {
    // Serve call-window.html, amadeus_logo.png directly from AMADEUS_DIR
    protocol.handle('amadeus-asset', (request) => {
      try {
        const url      = new URL(request.url)
        const filename = decodeURIComponent(url.host || url.pathname.replace(/^\//, ''))
        const filePath = path.join(AMADEUS_DIR, filename)
        const resolved = path.resolve(filePath)
        if (!resolved.startsWith(path.resolve(AMADEUS_DIR))) {
          return new Response('forbidden', { status: 403 })
        }
        return net.fetch(pathToFileURL(resolved).href, { bypassCustomProtocolHandlers: true })
      } catch(e) {
        return new Response('not found', { status: 404 })
      }
    })

    // Hide from dock — completely invisible to the user
    if (app.dock) app.dock.hide()

    // Register as a login item so AmadeusCall auto-launches after every reboot.
    // openAsHidden keeps it from stealing focus on login.
    // setLoginItemSettings is idempotent — safe to call on every launch.
    try {
      app.setLoginItemSettings({ openAtLogin: true, openAsHidden: true })
    } catch(e) {
      console.warn('[scheduler] setLoginItemSettings failed:', e.message)
    }

    // Mark ready — second-instance handler is now safe to create BrowserWindows
    appReady = true

    // --test-call: fire the call window immediately without touching scheduler quota
    if (process.argv.includes('--test-call')) {
      console.log('[scheduler] --test-call flag detected — firing immediately')
      fireIncomingCall()
    } else {
      scheduleCall()
    }

    // Hourly loop — keeps scheduler accurate after Mac sleep/wake cycles
    scheduleHourlyCheck()
  })
}

// Stay alive even when the call window is closed — the scheduler must keep running
app.on('window-all-closed', () => {
  // Intentionally empty
})
