/**
 * Preprocessing Service – Local Python API
 * ==========================================
 * Points to http://localhost:8000 (the local FastAPI backend).
 *
 * PURPOSE:
 *   Pre-processing operations that prepare raw audio for training:
 *     • Spectrogram / waveform visualisation
 *     • Audio chunking (click/silence boundary splitting)
 *     • Sliding window segmentation
 *     • Noise reduction
 *     • Quality filtering (SNR, RMS, duration)
 *     • Source separation (NMF)
 */

const API_BASE = 'http://localhost:8000/api';

/* ── Types ── */

export interface ChunkingParams {
  input_dir: string;
  output_dir: string;
  min_duration_ms?: number;
}

export interface SlidingWindowResult {
  n_windows: number;
  window_size_seconds: number;
  step_seconds: number;
  sample_rate: number;
  samples_per_window: number;
}

export interface NoiseReductionParams {
  input_dir: string;
  output_dir: string;
}

export interface QualityFilterParams {
  input_dir: string;
  output_dir: string;
  snr_threshold?: number;
  min_duration?: number;
  max_duration?: number;
  min_rms?: number;
}

export interface SourceSeparationResult {
  n_sources: number;
  sample_rate: number;
  sources: Array<{
    index: number;
    audio_base64: string;
    samples: number;
  }>;
}

/* ── Helpers ── */
async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Visualisation ── */

/**
 * Get a Mel spectrogram as a Base64-encoded PNG image.
 */
export async function getSpectrogram(
  file: File
): Promise<{ image_base64: string; content_type: string }> {
  const form = new FormData();
  form.append('file', file);
  return postForm('/visualize/spectrogram', form);
}

/**
 * Get a waveform plot as a Base64-encoded PNG image.
 */
export async function getWaveform(
  file: File
): Promise<{ image_base64: string; content_type: string }> {
  const form = new FormData();
  form.append('file', file);
  return postForm('/visualize/waveform', form);
}

/* ── Chunking & Segmentation ── */

/**
 * Split audio files in a directory on click/silence boundaries.
 */
export async function chunkAudio(
  params: ChunkingParams
): Promise<{ status: string; output_dir: string; files_created: number }> {
  return postJson('/data/chunk-audio', params);
}

/**
 * Segment a single audio file into overlapping windows.
 */
export async function applySlidingWindow(
  file: File,
  windowSize: number = 1.0,
  step: number = 0.5,
): Promise<SlidingWindowResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('window_size', String(windowSize));
  form.append('step', String(step));
  return postForm('/data/sliding-window', form);
}

/* ── Noise & Quality ── */

/**
 * Apply noise reduction to all audio files in a directory.
 */
export async function reduceNoise(
  params: NoiseReductionParams
): Promise<{ status: string; output_dir: string; files_processed: number }> {
  return postJson('/data/noise-reduction', params);
}

/**
 * Run quality filtering on a dataset (without augmentation).
 * Filters on: duration range, RMS energy, SNR threshold.
 */
export async function qualityFilter(
  params: QualityFilterParams
): Promise<{ status: string; filter_report: Record<string, any> }> {
  return postJson('/data/quality-filter', params);
}

/* ── Source Separation ── */

/**
 * Separate mixed audio into N sources using NMF.
 */
export async function sourceSeparation(
  file: File,
  nComponents: number = 2,
): Promise<SourceSeparationResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('n_components', String(nComponents));
  return postForm('/processing/source-separation', form);
}
