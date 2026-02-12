/**
 * DopplerAnalysis.tsx
 * ====================
 * Doppler Velocity & Frequency-Band Analysis Visualisation
 *
 * PURPOSE:
 *   Displays Doppler shift analysis and frequency-band energy distribution
 *   for uploaded or streamed audio.  This provides a "first-guess" view
 *   of what kind of moving object is producing the sound, its velocity,
 *   and its direction (approaching / receding).
 *
 * ARCHITECTURE:
 *   ┌────────────────────────────────────────────────────────────┐
 *   │  User uploads audio file or selects a recording           │
 *   │      │                                                    │
 *   │      ├─→ POST /api/analysis/hybrid-classify               │
 *   │      │     → first_guess, candidates, band_energies       │
 *   │      │     → doppler_summary (velocity, direction)        │
 *   │      │                                                    │
 *   │      └─→ POST /api/visualize/doppler                      │
 *   │            → Base64 PNG plot (freq track + velocity +     │
 *   │              band energy bar chart)                       │
 *   │                                                           │
 *   │  Component renders:                                       │
 *   │    1. Hybrid classification card (first guess + conf.)    │
 *   │    2. Doppler summary card (velocity, direction)          │
 *   │    3. Full analysis plot (Base64 image)                   │
 *   │    4. Frequency band table (energy per band)              │
 *   └────────────────────────────────────────────────────────────┘
 *
 * LOGIC NOTE on the speed_of_sound parameter:
 *   - Air (20°C): 343 m/s  ← default
 *   - Water:     ~1500 m/s  ← for hydrophone/underwater deployments
 *   The user can toggle this based on their deployment environment.
 */

import React, { useState, useCallback } from 'react';

/* ── Constants ── */
const API_BASE = 'http://localhost:8000/api';

/* ── Types ── */
interface Candidate {
    class: string;
    confidence: number;
}

interface BandEnergy {
    name: string;
    low_hz: number;
    high_hz: number;
    energy: number;
    energy_db: number;
    candidate_sources: string[];
}

interface DopplerSummary {
    mean_velocity_m_s: number;
    max_velocity_m_s: number;
    dominant_direction: string;
    n_frames: number;
    duration_s: number;
    mean_travel_time_s?: number;
}

interface HybridResult {
    first_guess: string;
    candidates: Candidate[];
    band_energies: BandEnergy[];
    is_moving: boolean | null;
    velocity_m_s: number | null;
    direction: string | null;
    method: string;
    doppler_summary?: DopplerSummary;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
/*  Component                                                      */
/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const DopplerAnalysis: React.FC = () => {
    /* ── State ── */
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Analysis results
    const [hybrid, setHybrid] = useState<HybridResult | null>(null);
    const [plotImage, setPlotImage] = useState<string | null>(null);

    // User-configurable parameters
    const [speedOfSound, setSpeedOfSound] = useState(343.0);
    const [distanceM, setDistanceM] = useState<number | null>(null);
    const [sourceFreqHz, setSourceFreqHz] = useState<number | null>(null);

    /* ── File selection ── */
    const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
            // Clear previous results
            setHybrid(null);
            setPlotImage(null);
            setError(null);
        }
    }, []);

    /* ── Run analysis ── */
    const runAnalysis = useCallback(async () => {
        if (!file) return;
        setLoading(true);
        setError(null);

        const configJson = JSON.stringify({
            speed_of_sound: speedOfSound,
            distance_m: distanceM,
            source_frequency_hz: sourceFreqHz,
        });

        try {
            /* 1. Hybrid classification (frequency bands + Doppler) */
            const classifyForm = new FormData();
            classifyForm.append('file', file);
            classifyForm.append('config_json', configJson);

            const classifyRes = await fetch(`${API_BASE}/analysis/hybrid-classify`, {
                method: 'POST',
                body: classifyForm,
            });
            if (!classifyRes.ok) throw new Error('Hybrid classification failed');
            const classifyData: HybridResult = await classifyRes.json();
            setHybrid(classifyData);

            /* 2. Doppler visualisation plot */
            const plotForm = new FormData();
            plotForm.append('file', file);
            plotForm.append('config_json', configJson);

            const plotRes = await fetch(`${API_BASE}/visualize/doppler`, {
                method: 'POST',
                body: plotForm,
            });
            if (!plotRes.ok) throw new Error('Doppler visualisation failed');
            const plotData = await plotRes.json();
            setPlotImage(plotData.image_base64);
        } catch (err: any) {
            setError(err.message || 'Analysis failed');
        } finally {
            setLoading(false);
        }
    }, [file, speedOfSound, distanceM, sourceFreqHz]);

    /* ── Direction badge colour ── */
    const directionColor = (dir: string | null) => {
        if (dir === 'approaching') return '#4CAF50';
        if (dir === 'receding') return '#F44336';
        return '#9E9E9E';
    };

    /* ── Render ── */
    return (
        <div style={{ padding: '1.5rem', maxWidth: '960px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '1rem', fontWeight: 700 }}>
                🎯 Doppler & Frequency Analysis
            </h2>

            {/* ── File Upload ── */}
            <div style={{
                display: 'flex', gap: '1rem', alignItems: 'center',
                marginBottom: '1.5rem', flexWrap: 'wrap',
            }}>
                <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileChange}
                    style={{ flex: 1 }}
                    id="doppler-file-input"
                />
                <button
                    onClick={runAnalysis}
                    disabled={!file || loading}
                    style={{
                        padding: '0.5rem 1.5rem',
                        background: loading ? '#9E9E9E' : '#2196F3',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: loading ? 'wait' : 'pointer',
                        fontWeight: 600,
                    }}
                    id="doppler-run-btn"
                >
                    {loading ? 'Analysing…' : 'Run Analysis'}
                </button>
            </div>

            {/* ── Parameters ── */}
            <details style={{ marginBottom: '1.5rem' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 600 }}>
                    ⚙️ Parameters
                </summary>
                <div style={{
                    display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '1rem', marginTop: '0.75rem', padding: '1rem',
                    background: '#f5f5f5', borderRadius: '8px',
                }}>
                    <label>
                        Speed of Sound (m/s)
                        <input
                            type="number"
                            value={speedOfSound}
                            onChange={(e) => setSpeedOfSound(Number(e.target.value))}
                            style={{ width: '100%', padding: '0.3rem' }}
                            id="doppler-speed-input"
                        />
                        <small style={{ color: '#666' }}>343=air, 1500=water</small>
                    </label>
                    <label>
                        Distance (m) – optional
                        <input
                            type="number"
                            placeholder="e.g. 100"
                            value={distanceM ?? ''}
                            onChange={(e) => setDistanceM(e.target.value ? Number(e.target.value) : null)}
                            style={{ width: '100%', padding: '0.3rem' }}
                            id="doppler-distance-input"
                        />
                        <small style={{ color: '#666' }}>For travel-time estimate</small>
                    </label>
                    <label>
                        Source Freq (Hz) – optional
                        <input
                            type="number"
                            placeholder="auto-detect"
                            value={sourceFreqHz ?? ''}
                            onChange={(e) => setSourceFreqHz(e.target.value ? Number(e.target.value) : null)}
                            style={{ width: '100%', padding: '0.3rem' }}
                            id="doppler-freq-input"
                        />
                        <small style={{ color: '#666' }}>Leave blank for auto</small>
                    </label>
                </div>
            </details>

            {error && (
                <div style={{
                    padding: '0.75rem', background: '#ffebee', color: '#c62828',
                    borderRadius: '6px', marginBottom: '1rem',
                }}>
                    ❌ {error}
                </div>
            )}

            {/* ── Results ── */}
            {hybrid && (
                <>
                    {/* Classification + Doppler summary cards */}
                    <div style={{
                        display: 'grid', gridTemplateColumns: '1fr 1fr',
                        gap: '1rem', marginBottom: '1.5rem',
                    }}>
                        {/* First-guess card */}
                        <div style={{
                            padding: '1.25rem', background: '#e8f5e9', borderRadius: '8px',
                            border: '1px solid #c8e6c9',
                        }}>
                            <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.9rem', color: '#388E3C' }}>
                                🏷️ First Guess ({hybrid.method})
                            </h3>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                                {hybrid.first_guess}
                            </div>
                            <div style={{ marginTop: '0.5rem' }}>
                                {hybrid.candidates.map((c, i) => (
                                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span>{c.class}</span>
                                        <span style={{ fontWeight: 600 }}>
                                            {(c.confidence * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Doppler card */}
                        <div style={{
                            padding: '1.25rem', background: '#e3f2fd', borderRadius: '8px',
                            border: '1px solid #bbdefb',
                        }}>
                            <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.9rem', color: '#1565C0' }}>
                                📡 Doppler Analysis
                            </h3>
                            {hybrid.doppler_summary && (
                                <>
                                    <div style={{ marginBottom: '0.3rem' }}>
                                        <strong>Direction: </strong>
                                        <span style={{
                                            color: directionColor(hybrid.doppler_summary.dominant_direction),
                                            fontWeight: 700,
                                        }}>
                                            {hybrid.doppler_summary.dominant_direction}
                                        </span>
                                    </div>
                                    <div style={{ marginBottom: '0.3rem' }}>
                                        <strong>Max Velocity: </strong>
                                        {hybrid.doppler_summary.max_velocity_m_s.toFixed(2)} m/s
                                    </div>
                                    <div style={{ marginBottom: '0.3rem' }}>
                                        <strong>Mean Velocity: </strong>
                                        {hybrid.doppler_summary.mean_velocity_m_s.toFixed(2)} m/s
                                    </div>
                                    <div>
                                        <strong>Duration: </strong>
                                        {hybrid.doppler_summary.duration_s.toFixed(1)}s
                                        ({hybrid.doppler_summary.n_frames} frames)
                                    </div>
                                    {hybrid.doppler_summary.mean_travel_time_s && (
                                        <div style={{ marginTop: '0.3rem' }}>
                                            <strong>Est. Travel Time: </strong>
                                            {hybrid.doppler_summary.mean_travel_time_s.toFixed(1)}s
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>

                    {/* ── Full plot ── */}
                    {plotImage && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h3 style={{ marginBottom: '0.5rem' }}>📊 Doppler & Frequency Plot</h3>
                            <img
                                src={`data:image/png;base64,${plotImage}`}
                                alt="Doppler analysis plot"
                                style={{ width: '100%', borderRadius: '8px', border: '1px solid #e0e0e0' }}
                            />
                        </div>
                    )}

                    {/* ── Frequency band table ── */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <h3 style={{ marginBottom: '0.5rem' }}>📈 Frequency Band Breakdown</h3>
                        <table style={{
                            width: '100%', borderCollapse: 'collapse',
                            fontSize: '0.85rem',
                        }}>
                            <thead>
                                <tr style={{ background: '#f5f5f5' }}>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Band</th>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Range</th>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Energy</th>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Bar</th>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Candidates</th>
                                </tr>
                            </thead>
                            <tbody>
                                {hybrid.band_energies.map((b, i) => (
                                    <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '0.4rem 0.5rem', fontWeight: 600 }}>
                                            {b.name}
                                        </td>
                                        <td style={{ padding: '0.4rem 0.5rem' }}>
                                            {b.low_hz}–{b.high_hz} Hz
                                        </td>
                                        <td style={{ padding: '0.4rem 0.5rem' }}>
                                            {(b.energy * 100).toFixed(1)}%
                                        </td>
                                        <td style={{ padding: '0.4rem 0.5rem' }}>
                                            <div style={{
                                                height: '10px',
                                                width: `${Math.max(2, b.energy * 200)}px`,
                                                background: `hsl(${200 - b.energy * 200}, 70%, 50%)`,
                                                borderRadius: '3px',
                                            }} />
                                        </td>
                                        <td style={{ padding: '0.4rem 0.5rem', fontSize: '0.8rem', color: '#666' }}>
                                            {b.candidate_sources.join(', ')}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
};

export default DopplerAnalysis;
