
import { contextBridge, ipcRenderer } from 'electron';

/**
 * Preload Script — Context Bridge
 * =================================
 * Exposes safe IPC methods to the renderer process.
 *
 * SECURITY NOTE:
 *   contextIsolation is enabled, so the renderer cannot access
 *   Node.js or Electron APIs directly. Only the methods exposed
 *   here are available via `window.electronAPI`.
 */

contextBridge.exposeInMainWorld('electronAPI', {
    // ── Database ──
    dbQuery: (sql: string, params?: any[]) =>
        ipcRenderer.invoke('db-query', sql, params),
    getAppPath: () =>
        ipcRenderer.invoke('get-app-path'),

    // ── Backend Process Management ──
    backendStart: (port?: number) =>
        ipcRenderer.invoke('backend:start', port),
    backendStop: () =>
        ipcRenderer.invoke('backend:stop'),
    backendStatus: () =>
        ipcRenderer.invoke('backend:status'),
    backendLogs: () =>
        ipcRenderer.invoke('backend:logs'),
});
