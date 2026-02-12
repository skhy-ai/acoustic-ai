
import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';
import Database from 'better-sqlite3';
import { spawn, ChildProcess } from 'child_process';

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
    app.quit();
}

let mainWindow: BrowserWindow | null = null;
let db: Database.Database | null = null;

// ── Backend Process Management ──
let backendProcess: ChildProcess | null = null;
let backendPid: number | null = null;
let backendStartTime: number | null = null;
const backendLogBuffer: string[] = [];
const MAX_LOG_LINES = 200;

const appendLog = (line: string) => {
    backendLogBuffer.push(line);
    if (backendLogBuffer.length > MAX_LOG_LINES) {
        backendLogBuffer.shift();
    }
};

const createWindow = () => {
    // Create the browser window.
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 900,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    // Load the index.html of the app.
    if (process.env.VITE_DEV_SERVER_URL) {
        mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    } else {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }

    // Open the DevTools.
    // mainWindow.webContents.openDevTools();
};

// Initialize SQLite Database
const initDatabase = () => {
    const dbPath = path.join(app.getPath('userData'), 'acoustic_ai.db');
    db = new Database(dbPath);

    // Create tables if they don't exist
    db.exec(`
    CREATE TABLE IF NOT EXISTS experiments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      status TEXT DEFAULT 'draft',
      config JSON
    );
    
    CREATE TABLE IF NOT EXISTS executions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      experiment_id INTEGER,
      started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      finished_at DATETIME,
      status TEXT,
      metrics JSON,
      FOREIGN KEY(experiment_id) REFERENCES experiments(id)
    );
  `);

    console.log('Database initialized at:', dbPath);
};

app.on('ready', () => {
    createWindow();
    initDatabase();
});

app.on('window-all-closed', () => {
    // Kill backend process on exit
    if (backendProcess) {
        backendProcess.kill();
        backendProcess = null;
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// =====================================================================
//  IPC Handlers — Database
// =====================================================================
ipcMain.handle('db-query', (event, sql, params) => {
    if (!db) return { error: 'Database not initialized' };
    try {
        const stmt = db.prepare(sql);
        if (sql.trim().toLowerCase().startsWith('select')) {
            return stmt.all(params || []);
        } else {
            return stmt.run(params || []);
        }
    } catch (err: any) {
        return { error: err.message };
    }
});

ipcMain.handle('get-app-path', () => {
    return app.getAppPath();
});

// =====================================================================
//  IPC Handlers — Backend Process Management
// =====================================================================

/**
 * backend:start — Spawn the Python FastAPI process.
 *
 * LOGIC NOTE:
 *   We resolve the backend directory relative to the app root.
 *   In development, this is the project directory.
 *   In production (packaged), it will be in the resources folder.
 */
ipcMain.handle('backend:start', (_event, port: number = 8000) => {
    if (backendProcess && backendProcess.exitCode === null) {
        return { error: 'Backend is already running', pid: backendPid };
    }

    try {
        // Resolve backend directory
        const appRoot = app.getAppPath();
        const backendDir = path.resolve(appRoot, '..', 'sound_classifier_system');

        // Try venv python first, fall back to system python
        const venvPython = path.resolve(appRoot, '..', '.venv', 'bin', 'python');
        const pythonCmd = require('fs').existsSync(venvPython) ? venvPython : 'python3';

        backendProcess = spawn(pythonCmd, ['-m', 'api.main'], {
            cwd: backendDir,
            env: { ...process.env, PORT: String(port) },
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        backendPid = backendProcess.pid ?? null;
        backendStartTime = Date.now();
        backendLogBuffer.length = 0;

        appendLog(`[INFO] Backend starting on port ${port} (PID: ${backendPid})`);

        backendProcess.stdout?.on('data', (data: Buffer) => {
            const lines = data.toString().split('\n').filter(Boolean);
            lines.forEach((line) => appendLog(`[STDOUT] ${line}`));
        });

        backendProcess.stderr?.on('data', (data: Buffer) => {
            const lines = data.toString().split('\n').filter(Boolean);
            lines.forEach((line) => appendLog(`[STDERR] ${line}`));
        });

        backendProcess.on('exit', (code) => {
            appendLog(`[INFO] Backend exited with code ${code}`);
            backendProcess = null;
            backendPid = null;
            backendStartTime = null;
        });

        return { pid: backendPid, port };
    } catch (err: any) {
        return { error: err.message };
    }
});

/**
 * backend:stop — Kill the running backend process.
 */
ipcMain.handle('backend:stop', () => {
    if (!backendProcess) {
        return { error: 'No backend process running' };
    }
    backendProcess.kill('SIGTERM');
    appendLog('[INFO] Backend stop signal sent');
    return { status: 'stopping' };
});

/**
 * backend:status — Return current backend process state.
 */
ipcMain.handle('backend:status', () => {
    const running = backendProcess !== null && backendProcess.exitCode === null;
    return {
        running,
        pid: backendPid,
        uptime_s: backendStartTime ? Math.floor((Date.now() - backendStartTime) / 1000) : null,
    };
});

/**
 * backend:logs — Return the last N log lines from the circular buffer.
 */
ipcMain.handle('backend:logs', () => {
    return { lines: [...backendLogBuffer] };
});
