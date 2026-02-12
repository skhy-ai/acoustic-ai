/**
 * ManualFilter.tsx
 * =================
 * Spectrogram-Based Audio File Keep/Delete Tool
 *
 * PURPOSE:
 *   Port of the AudioFilterGUI class from gui_workflow.py.
 *   Presents audio files one at a time, displaying a server-rendered
 *   mel spectrogram. The user decides to Keep ✓ or Delete ✗ each file.
 *   Kept files are moved to a "filtered" directory; deleted files are
 *   removed.
 *
 * ARCHITECTURE:
 *   ┌──────────────────────────────────────────────────────┐
 *   │  ManualFilter.tsx                                    │
 *   │    ├─ Progress bar "12 of 45 files"                  │
 *   │    ├─ Spectrogram viewer (Base64 PNG from backend)   │
 *   │    ├─ Filename & class label display                 │
 *   │    ├─ Audio playback <audio> element                 │
 *   │    └─ Keep / Delete / Skip buttons                   │
 *   │                                                      │
 *   │  API Calls:                                          │
 *   │    POST /api/data/list-chunks     → file list        │
 *   │    POST /api/visualize/spectrogram → Base64 PNG      │
 *   │    POST /api/data/keep-chunk      → move to filtered │
 *   │    POST /api/data/delete-chunk    → remove file      │
 *   └──────────────────────────────────────────────────────┘
 */

import React, { useState, useCallback, useEffect } from 'react';

/* ── Types ── */
interface ChunkFile {
    path: string;
    filename: string;
    class_name: string;
}

/* ── Constants ── */
const API = 'http://localhost:8000/api';

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
const ManualFilter: React.FC = () => {
    const [sourceDir, setSourceDir] = useState('');
    const [destDir, setDestDir] = useState('');
    const [files, setFiles] = useState<ChunkFile[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [spectrogramBase64, setSpectrogramBase64] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [decisions, setDecisions] = useState({ kept: 0, deleted: 0, skipped: 0 });

    const currentFile = files[currentIndex] ?? null;
    const isFinished = files.length > 0 && currentIndex >= files.length;
    const totalFiles = files.length;

    /* ── Load file list from backend ── */
    const loadFiles = useCallback(async () => {
        if (!sourceDir.trim()) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API}/data/list-chunks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_dir: sourceDir }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setFiles(data.files || []);
            setCurrentIndex(0);
            setDecisions({ kept: 0, deleted: 0, skipped: 0 });
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [sourceDir]);

    /* ── Load spectrogram for current file ── */
    const loadSpectrogram = useCallback(async () => {
        if (!currentFile) { setSpectrogramBase64(null); return; }
        setSpectrogramBase64(null);
        try {
            const formData = new FormData();
            // Fetch the audio blob first, then send as file
            const audioRes = await fetch(`file://${currentFile.path}`).catch(() => null);
            if (!audioRes) {
                // Fallback: send file path for server-side loading
                formData.append('file_path', currentFile.path);
            }
            const res = await fetch(`${API}/visualize/spectrogram`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: currentFile.path }),
            });
            if (res.ok) {
                const data = await res.json();
                setSpectrogramBase64(data.image_base64 || null);
            }
        } catch {
            // Non-critical — spectrogram just won't show
        }
    }, [currentFile]);

    useEffect(() => { loadSpectrogram(); }, [loadSpectrogram]);

    /* ── Decision handlers ── */
    const advance = () => setCurrentIndex((prev) => prev + 1);

    const handleKeep = useCallback(async () => {
        if (!currentFile) return;
        setLoading(true);
        try {
            await fetch(`${API}/data/keep-chunk`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_path: currentFile.path,
                    dest_dir: destDir || `${sourceDir}_filtered`,
                    class_name: currentFile.class_name,
                }),
            });
            setDecisions((prev) => ({ ...prev, kept: prev.kept + 1 }));
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
            advance();
        }
    }, [currentFile, destDir, sourceDir]);

    const handleDelete = useCallback(async () => {
        if (!currentFile) return;
        setLoading(true);
        try {
            await fetch(`${API}/data/delete-chunk`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: currentFile.path }),
            });
            setDecisions((prev) => ({ ...prev, deleted: prev.deleted + 1 }));
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
            advance();
        }
    }, [currentFile]);

    const handleSkip = () => {
        setDecisions((prev) => ({ ...prev, skipped: prev.skipped + 1 }));
        advance();
    };

    /* ── Keyboard shortcuts ── */
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (isFinished) return;
            if (e.key === 'k' || e.key === 'K') handleKeep();
            else if (e.key === 'd' || e.key === 'D') handleDelete();
            else if (e.key === 's' || e.key === 'S') handleSkip();
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [handleKeep, handleDelete, handleSkip, isFinished]);

    return (
        <div style={{ padding: '1.5rem', maxWidth: '800px', margin: '0 auto' }}>
            <h2 style={{ fontWeight: 700, marginBottom: '1rem' }}>🔍 Manual Audio Filter</h2>
            <p style={{ color: '#666', marginBottom: '1.5rem' }}>
                Review audio files one by one. View spectrogram, play audio, then decide: <strong>Keep (K)</strong>, <strong>Delete (D)</strong>, or <strong>Skip (S)</strong>.
            </p>

            {/* ── Directory Config ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.75rem', marginBottom: '1.5rem' }}>
                <div>
                    <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Source Directory</label>
                    <input
                        type="text"
                        value={sourceDir}
                        onChange={(e) => setSourceDir(e.target.value)}
                        placeholder="/path/to/chunked/"
                        style={{ width: '100%', padding: '0.4rem', marginTop: '0.25rem' }}
                        id="manual-filter-source"
                    />
                </div>
                <div>
                    <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Destination Directory</label>
                    <input
                        type="text"
                        value={destDir}
                        onChange={(e) => setDestDir(e.target.value)}
                        placeholder="auto: <source>_filtered"
                        style={{ width: '100%', padding: '0.4rem', marginTop: '0.25rem' }}
                        id="manual-filter-dest"
                    />
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                    <button
                        onClick={loadFiles}
                        disabled={loading || !sourceDir.trim()}
                        style={{
                            padding: '0.4rem 1rem', border: 'none', borderRadius: '6px',
                            background: '#1976D2', color: '#fff', fontWeight: 600,
                            cursor: !sourceDir.trim() ? 'not-allowed' : 'pointer',
                        }}
                        id="manual-filter-load-btn"
                    >
                        Load
                    </button>
                </div>
            </div>

            {error && (
                <div style={{ padding: '0.75rem', background: '#ffebee', color: '#c62828', borderRadius: '6px', marginBottom: '1rem' }}>
                    ❌ {error}
                </div>
            )}

            {files.length > 0 && !isFinished && currentFile && (
                <>
                    {/* ── Progress ── */}
                    <div style={{ marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <span style={{ fontWeight: 600 }}>
                                File {currentIndex + 1} of {totalFiles}
                            </span>
                            <span style={{ fontSize: '0.85rem', color: '#666' }}>
                                ✅ {decisions.kept} kept · 🗑️ {decisions.deleted} deleted · ⏭️ {decisions.skipped} skipped
                            </span>
                        </div>
                        <div style={{ height: '6px', background: '#e0e0e0', borderRadius: '3px' }}>
                            <div style={{
                                height: '100%', borderRadius: '3px',
                                background: 'linear-gradient(90deg, #4CAF50, #8BC34A)',
                                width: `${((currentIndex) / totalFiles) * 100}%`,
                                transition: 'width 0.3s ease',
                            }} />
                        </div>
                    </div>

                    {/* ── File Info ── */}
                    <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#f5f5f5', borderRadius: '6px' }}>
                        <div><strong>File:</strong> {currentFile.filename}</div>
                        <div><strong>Class:</strong> {currentFile.class_name}</div>
                    </div>

                    {/* ── Spectrogram ── */}
                    <div style={{
                        marginBottom: '1rem', borderRadius: '8px', overflow: 'hidden',
                        background: '#000', minHeight: '200px', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                    }}>
                        {spectrogramBase64 ? (
                            <img
                                src={`data:image/png;base64,${spectrogramBase64}`}
                                alt="Mel Spectrogram"
                                style={{ width: '100%', height: 'auto' }}
                            />
                        ) : (
                            <span style={{ color: '#666' }}>Loading spectrogram...</span>
                        )}
                    </div>

                    {/* ── Audio Playback ── */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <audio
                            controls
                            src={`file://${currentFile.path}`}
                            style={{ width: '100%' }}
                        />
                    </div>

                    {/* ── Decision Buttons ── */}
                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                        <button
                            onClick={handleKeep}
                            disabled={loading}
                            style={{
                                padding: '0.75rem 2rem', border: 'none', borderRadius: '8px',
                                background: '#4CAF50', color: '#fff', fontWeight: 700,
                                fontSize: '1.1rem', cursor: 'pointer',
                            }}
                        >
                            ✅ Keep (K)
                        </button>
                        <button
                            onClick={handleSkip}
                            disabled={loading}
                            style={{
                                padding: '0.75rem 2rem', border: '2px solid #ccc', borderRadius: '8px',
                                background: '#fff', color: '#666', fontWeight: 700,
                                fontSize: '1.1rem', cursor: 'pointer',
                            }}
                        >
                            ⏭️ Skip (S)
                        </button>
                        <button
                            onClick={handleDelete}
                            disabled={loading}
                            style={{
                                padding: '0.75rem 2rem', border: 'none', borderRadius: '8px',
                                background: '#F44336', color: '#fff', fontWeight: 700,
                                fontSize: '1.1rem', cursor: 'pointer',
                            }}
                        >
                            🗑️ Delete (D)
                        </button>
                    </div>
                </>
            )}

            {/* ── Finished Summary ── */}
            {isFinished && (
                <div style={{
                    textAlign: 'center', padding: '2rem', background: '#E8F5E9',
                    borderRadius: '12px', marginTop: '1rem',
                }}>
                    <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>🎉 All files reviewed!</h3>
                    <div style={{ fontSize: '1.1rem' }}>
                        <span style={{ marginRight: '1.5rem' }}>✅ Kept: <strong>{decisions.kept}</strong></span>
                        <span style={{ marginRight: '1.5rem' }}>🗑️ Deleted: <strong>{decisions.deleted}</strong></span>
                        <span>⏭️ Skipped: <strong>{decisions.skipped}</strong></span>
                    </div>
                </div>
            )}

            {/* ── Empty state ── */}
            {files.length === 0 && !loading && sourceDir && (
                <div style={{ textAlign: 'center', color: '#999', padding: '2rem' }}>
                    No files loaded. Click <strong>Load</strong> to scan the source directory.
                </div>
            )}
        </div>
    );
};

export default ManualFilter;
