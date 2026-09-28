const { contextBridge, ipcRenderer } = require('electron')

// Minimal preload for the incoming call window.
// Exposes ONLY the two channels required — no other IPC surface.
contextBridge.exposeInMainWorld('callAPI', {
  accept:  () => ipcRenderer.send('accept-call'),
  decline: () => ipcRenderer.send('decline-call')
})
