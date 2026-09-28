const { contextBridge, ipcRenderer } = require('electron')

// Expose only specific channels — never the whole ipcRenderer object (security).
contextBridge.exposeInMainWorld('electronAPI', {
  // Existing platform info — preserve
  platform: process.platform,
  version: process.versions.electron,

  // Main → renderer: "give me the current conversation for diary"
  onRequestConversation: (callback) => {
    ipcRenderer.on('request-conversation', () => callback())
  },
  // Renderer → main: send conversation back (or null if none)
  sendConversation: (payload) => ipcRenderer.send('conversation-response', payload),

  // Main → renderer: "save this diary entry"
  onSaveDiaryEntry: (callback) => {
    ipcRenderer.on('save-diary-entry', (_event, entryText) => callback(entryText))
  },
  // Renderer → main: "I'm done saving, you can quit now"
  diarySaveComplete: () => ipcRenderer.send('diary-save-complete'),

  // Main → renderer: "show the saving overlay"
  onShowSavingOverlay: (callback) => {
    ipcRenderer.on('show-saving-overlay', () => callback())
  },

  // Stage 2 summary IPC
  // Main → renderer: "send me the full diary entries array + watermark"
  onRequestDiaryEntries: (callback) => {
    ipcRenderer.on('request-diary-entries', () => callback())
  },
  // Renderer → main: send entries array + watermark
  sendDiaryEntries: (payload) => ipcRenderer.send('diary-entries-response', payload),

  // Main → renderer: "save this long-term summary"
  onSaveDiarySummary: (callback) => {
    ipcRenderer.on('save-diary-summary', (_event, payload) => callback(payload))
  },
  // Renderer → main: "summary saved"
  diarySummarySaved: () => ipcRenderer.send('diary-summary-saved'),

  // Backlog #202 — main → renderer: "run the once-per-session facts pass now"
  onRunFactsExtraction: (callback) => {
    ipcRenderer.on('run-facts-extraction', () => callback())
  },
  // Renderer → main: "facts pass finished" (sent exactly once, every path)
  factsExtractionDone: () => ipcRenderer.send('facts-extraction-done'),

  // Main → renderer: "incoming call was accepted — trigger special greeting"
  // Fires when the user accepts a call and the main window already existed (show+focus path).
  // When the window is freshly created via ?incomingCall=1, boot() handles the greeting
  // directly from the URL param — this IPC is the already-booted-window path only.
  onIncomingCallAccepted: (callback) => {
    ipcRenderer.on('incoming-call-accepted', () => callback())
  },

  // Renderer → main: persist a synthesized greeting MP3 to the disk cache
  // (data/greeting_cache/). Read back via amadeus-asset://data/greeting_cache/<key>.mp3
  cacheGreetingAudio: (payload) => ipcRenderer.send('cache-greeting-audio', payload),

  // Main → renderer: window visibility changed (hide/show)
  // Used to pause/resume heavy rendering and BGM when window is hidden (e.g. Cmd+H).
  onWindowHidden: (callback) => {
    ipcRenderer.on('window-hidden', () => callback())
  },
  onWindowShown: (callback) => {
    ipcRenderer.on('window-shown', () => callback())
  }
})
