/**
 * AdminPanel.tsx
 * ===============
 * Backend Service Control Panel
 *
 * PURPOSE:
 *   Provides a UI for starting, stopping, and monitoring the Python
 *   FastAPI backend process directly from the Electron desktop app.
 *
 * ARCHITECTURE:
 *   ┌──────────────────────────────────────────────────────┐
 *   │  AdminPanel.tsx                                      │
 *   │    ├─ Status indicator (green/red/yellow)            │
 *   │    ├─ Start / Stop / Restart buttons                 │
 *   │    ├─ Port configuration                             │
 *   │    ├─ PID & uptime display                           │
 *   │    ├─ Installation mode badge (Edge / Development)   │
 *   │    └─ Log viewer (last 100 lines stdout/stderr)      │
 *   │                                                      │
 *   │  Communication:                                      │
 *   │    Electron IPC (when in Electron)                   │
 *   │    OR HTTP polling (when in browser dev mode)         │
 *   └──────────────────────────────────────────────────────┘
 *
 * LOGIC NOTE:
 *   The component checks whether it's running inside Electron by
 *   testing for `window.electronAPI`. In pure browser mode (dev),
 *   it falls back to HTTP health polling only — start/stop won't work.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

/* ── Types ── */
interface BackendStatus {
    running: boolean;
    pid: number | null;
    port: number;
    uptime_s: number | null;
}

/* ── Electron API type guard ── */
const electron = (window as any).electronAPI;
const isElectron = typeof electron !== 'undefined';

/* ── Constants ── */
const DEFAULT_PORT = 8000;
const HEALTH_POLL_MS = 5000;
const INSTALL_MODE = (import.meta as any).env?.VITE_INSTALL_MODE || 'development';

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
/*  Component                                                      */
/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
const AdminPanel: React.FC = () => {
    const [status, setStatus] = useState<BackendStatus>({
        running: false,
        pid: null,
        port: DEFAULT_PORT,
        uptime_s: null,
    });
    const [logs, setLogs] = useState<string[]>([]);
    const [port, setPort] = useState(DEFAULT_PORT);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const logEndRef = useRef<HTMLDivElement>(null);

    /* ── Health polling ── */
    const checkHealth = useCallback(async () => {
        try {
            const res = await fetch(`http://localhost:${port}/api/health`, {
                signal: AbortSignal.timeout(3000),
            });
            if (res.ok) {
                setStatus((prev) => ({ ...prev, running: true, port }));
                setError(null);
            } else {
                setStatus((prev) => ({ ...prev, running: false }));
            }
        } catch {
            setStatus((prev) => ({ ...prev, running: false, pid: null }));
        }
    }, [port]);

    useEffect(() => {
        checkHealth();
        const interval = setInterval(checkHealth, HEALTH_POLL_MS);
        return () => clearInterval(interval);
    }, [checkHealth]);

    /* ── IPC: Start backend ── */
    const handleStart = useCallback(async () => {
        if (!isElectron) {
            setError('Start/stop is only available in the Electron desktop app.');
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const result = await electron.backendStart(port);
            if (result.error) {
                setError(result.error);
            } else {
                setStatus({ running: true, pid: result.pid, port, uptime_s: 0 });
                setLogs((prev) => [...prev, `[INFO] Backend started (PID: ${result.pid})`]);
            }
        } catch (err: any) {
            setError(err.message || 'Failed to start backend');
        } finally {
            setLoading(false);
        }
    }, [port]);

    /* ── IPC: Stop backend ── */
    const handleStop = useCallback(async () => {
        if (!isElectron) return;
        setLoading(true);
        try {
            await electron.backendStop();
            setStatus({ running: false, pid: null, port, uptime_s: null });
            setLogs((prev) => [...prev, '[INFO] Backend stopped']);
        } catch (err: any) {
            setError(err.message || 'Failed to stop backend');
        } finally {
            setLoading(false);
        }
    }, [port]);

    /* ── IPC: Get logs ── */
    const fetchLogs = useCallback(async () => {
        if (!isElectron) return;
        try {
            const result = await electron.backendLogs();
            if (result && Array.isArray(result.lines)) {
                setLogs(result.lines);
            }
        } catch {
            // Silently ignore log fetch failures
        }
    }, []);

    useEffect(() => {
        if (status.running) {
            const interval = setInterval(fetchLogs, 3000);
            return () => clearInterval(interval);
        }
    }, [status.running, fetchLogs]);

    /* ── Auto-scroll logs ── */
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    /* ── Status indicator styles ── */
    const statusColor = status.running ? '#4CAF50' : loading ? '#FFC107' : '#F44336';
    const statusLabel = status.running ? 'Running' : loading ? 'Starting...' : 'Stopped';

    return (
        <div style={{ padding: '1.5rem', maxWidth: '900px', margin: '0 auto' }}>
            {/* ── Header ── */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                <h2 style={{ margin: 0, fontWeight: 700 }}>⚙️ Admin Panel</h2>
                <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
                    padding: '0.25rem 0.75rem', borderRadius: '12px',
                    background: INSTALL_MODE === 'edge' ? '#E3F2FD' : '#E8F5E9',
                    color: INSTALL_MODE === 'edge' ? '#1565C0' : '#2E7D32',
                    fontSize: '0.8rem', fontWeight: 600,
                }}>
                    {INSTALL_MODE === 'edge' ? '🔳 Edge' : '🛠️ Development'}
                </span>
            </div>

            {/* ── Status Card ── */}
            <div style={{
                display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem',
                marginBottom: '1.5rem',
            }}>
                <div style={{
                    padding: '1.25rem', borderRadius: '8px',
                    background: '#fafafa', border: '1px solid #e0e0e0',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                        <div style={{
                            width: '12px', height: '12px', borderRadius: '50%',
                            background: statusColor,
                            boxShadow: `0 0 6px ${statusColor}`,
                        }} />
                        <strong style={{ fontSize: '1.1rem' }}>{statusLabel}</strong>
                    </div>
                    {status.pid && <div><strong>PID:</strong> {status.pid}</div>}
                    <div><strong>Port:</strong> {status.port}</div>
                    {status.uptime_s !== null && status.running && (
                        <div><strong>Uptime:</strong> {Math.floor(status.uptime_s / 60)}m {status.uptime_s % 60}s</div>
                    )}
                </div>

                {/* ── Controls ── */}
                <div style={{
                    padding: '1.25rem', borderRadius: '8px',
                    background: '#fafafa', border: '1px solid #e0e0e0',
                }}>
                    <div style={{ marginBottom: '0.75rem' }}>
                        <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                            Port:
                            <input
                                type="number"
                                value={port}
                                onChange={(e) => setPort(Number(e.target.value))}
                                style={{ marginLeft: '0.5rem', width: '80px', padding: '0.2rem 0.4rem' }}
                                disabled={status.running}
                                id="admin-port-input"
                            />
                        </label>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                            onClick={handleStart}
                            disabled={status.running || loading}
                            style={{
                                padding: '0.4rem 1rem', border: 'none', borderRadius: '6px',
                                background: status.running ? '#ccc' : '#4CAF50', color: '#fff',
                                cursor: status.running ? 'not-allowed' : 'pointer', fontWeight: 600,
                            }}
                            id="admin-start-btn"
                        >
                            ▶ Start
                        </button>
                        <button
                            onClick={handleStop}
                            disabled={!status.running || loading}
                            style={{
                                padding: '0.4rem 1rem', border: 'none', borderRadius: '6px',
                                background: !status.running ? '#ccc' : '#F44336', color: '#fff',
                                cursor: !status.running ? 'not-allowed' : 'pointer', fontWeight: 600,
                            }}
                            id="admin-stop-btn"
                        >
                            ⏹ Stop
                        </button>
                        <button
                            onClick={async () => { await handleStop(); setTimeout(handleStart, 1000); }}
                            disabled={!status.running || loading}
                            style={{
                                padding: '0.4rem 1rem', border: 'none', borderRadius: '6px',
                                background: !status.running ? '#ccc' : '#FF9800', color: '#fff',
                                cursor: !status.running ? 'not-allowed' : 'pointer', fontWeight: 600,
                            }}
                            id="admin-restart-btn"
                        >
                            🔄 Restart
                        </button>
                    </div>
                    {!isElectron && (
                        <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#999' }}>
                            Start/stop requires the Electron desktop app.
                        </div>
                    )}
                </div>
            </div>

            {error && (
                <div style={{
                    padding: '0.75rem', background: '#ffebee', color: '#c62828',
                    borderRadius: '6px', marginBottom: '1rem',
                }}>
                    ❌ {error}
                </div>
            )}

            {/* ── API Quick Links ── */}
            <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ marginBottom: '0.5rem', fontSize: '0.95rem' }}>🔗 Quick Links</h3>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    {[
                        { label: 'API Docs', url: `http://localhost:${port}/docs` },
                        { label: 'Health', url: `http://localhost:${port}/api/health` },
                        { label: 'OpenAPI', url: `http://localhost:${port}/openapi.json` },
                    ].map((link) => (
                        <a
                            key={link.label}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                                padding: '0.3rem 0.8rem', borderRadius: '6px',
                                background: '#e3f2fd', color: '#1565c0', textDecoration: 'none',
                                fontSize: '0.85rem', fontWeight: 500,
                            }}
                        >
                            {link.label} ↗
                        </a>
                    ))}
                </div>
            </div>

            {/* ── Log Viewer ── */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '0.95rem' }}>📋 Backend Logs</h3>
                    <button
                        onClick={() => setLogs([])}
                        style={{
                            padding: '0.2rem 0.6rem', border: '1px solid #ccc',
                            borderRadius: '4px', background: '#fff', cursor: 'pointer',
                            fontSize: '0.8rem',
                        }}
                    >
                        Clear
                    </button>
                </div>
                <div style={{
                    height: '200px', overflowY: 'auto',
                    background: '#1e1e1e', color: '#d4d4d4',
                    fontFamily: '"Fira Code", "Cascadia Code", monospace',
                    fontSize: '0.8rem', padding: '0.75rem', borderRadius: '8px',
                    lineHeight: 1.6,
                }}>
                    {logs.length === 0 ? (
                        <span style={{ color: '#666' }}>No logs yet. Start the backend to see output.</span>
                    ) : (
                        logs.map((line, i) => (
                            <div key={i} style={{
                                color: line.includes('ERROR') ? '#f44336' :
                                    line.includes('WARNING') ? '#ff9800' :
                                        line.includes('INFO') ? '#81c784' : '#d4d4d4',
                            }}>
                                {line}
                            </div>
                        ))
                    )}
                    <div ref={logEndRef} />
                </div>
            </div>
        </div>
    );
};

export default AdminPanel;
