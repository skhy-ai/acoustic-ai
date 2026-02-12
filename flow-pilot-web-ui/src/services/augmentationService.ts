/**
 * augmentationService.ts
 * ========================
 * Frontend service for M3 Audio Augmentation
 *
 * PURPOSE:
 *   Provides typed functions to call the backend /m3-augmentation/* API
 *   endpoints. These produce augmented copies of audio files to increase
 *   training sample size.
 *
 * AVAILABLE AUGMENTATIONS:
 *   ┌────────────────────┬────────────────────────────────────────────┐
 *   │ Function           │ What it does                               │
 *   ├────────────────────┼────────────────────────────────────────────┤
 *   │ applyPitchShift    │ Shift pitch ±N Hz (pyrubberband)           │
 *   │ injectNoise        │ Add Gaussian noise at various SNR levels   │
 *   │ applyTimeStretch   │ Speed up / slow down without pitch change  │
 *   │ adjustVolume       │ Create louder / quieter variants (dB)      │
 *   │ reverseAudio       │ Create time-reversed copies                │
 *   │ runPipeline        │ Unified class-balanced pipeline (best)     │
 *   └────────────────────┴────────────────────────────────────────────┘
 *
 * ARCHITECTURE NOTE:
 *   All augmentations operate on directories (not individual files).
 *   The backend processes all audio files in input_dir and writes
 *   augmented copies to output_dir. This is designed for batch
 *   operation during the data preparation workflow.
 *
 * PREVIOUS BUG:
 *   This service was pointing to the old Supabase Edge Functions URL
 *   (https://naovefbmlxpoeyymtpfp.supabase.co/functions/v1/m3-augmentation/...).
 *   Since the backend is now a local Python FastAPI server, all calls
 *   have been redirected to http://localhost:8000/api/m3-augmentation/*.
 */

const API_BASE = 'http://localhost:8000/api';

/* ── Types ── */

export interface PitchShiftParams {
  input_dir: string;
  output_dir: string;
  pitch_changes?: number[];         // Hz offsets, e.g. [-50, -100, ...]
  apply_noise_reduction?: boolean;
}

export interface NoiseInjectionParams {
  input_dir: string;
  output_dir: string;
  snr_db_levels?: number[];         // SNR dB, e.g. [20, 15, 10]
}

export interface TimeStretchParams {
  input_dir: string;
  output_dir: string;
  rates?: number[];                 // Speed multipliers, e.g. [0.8, 1.2]
}

export interface VolumeAdjustmentParams {
  input_dir: string;
  output_dir: string;
  decibel_changes?: number[];       // dB offsets, e.g. [10, -10]
}

export interface ReverseAudioParams {
  input_dir: string;
  output_dir: string;
}

export interface AugmentPipelineParams {
  input_dir: string;
  output_dir: string;
  enable_pitch_shift?: boolean;
  enable_time_stretch?: boolean;
  enable_noise_injection?: boolean;
  enable_volume_scale?: boolean;
  target_samples_per_class?: number;
}

export interface AugmentResult {
  status: string;
  output_dir: string;
  files_created: number;
}

export interface PipelineResult {
  status: string;
  augmentation_report: Record<string, number>;
}

/* ── Helper ── */
async function post<T>(path: string, body: unknown): Promise<T> {
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

/* ── Public API ── */

/**
 * Apply pitch shifting to all audio files in a directory.
 * Each file gets N variants (one per pitch_change value).
 */
export async function applyPitchShift(params: PitchShiftParams): Promise<AugmentResult> {
  return post('/m3-augmentation/pitch-shift', params);
}

/**
 * Inject Gaussian noise at various SNR levels.
 */
export async function injectNoise(params: NoiseInjectionParams): Promise<AugmentResult> {
  return post('/m3-augmentation/noise-injection', params);
}

/**
 * Time-stretch audio at given speed factors (without changing pitch).
 */
export async function applyTimeStretch(params: TimeStretchParams): Promise<AugmentResult> {
  return post('/m3-augmentation/time-stretch', params);
}

/**
 * Create volume-adjusted variants (louder + quieter).
 */
export async function adjustVolume(params: VolumeAdjustmentParams): Promise<AugmentResult> {
  return post('/m3-augmentation/volume-adjustment', params);
}

/**
 * Create time-reversed copies of all audio files.
 */
export async function reverseAudio(params: ReverseAudioParams): Promise<AugmentResult> {
  return post('/m3-augmentation/reverse', params);
}

/**
 * Run the unified class-balanced augmentation pipeline.
 *
 * This is the RECOMMENDED way to augment data. It automatically:
 *  1. Counts samples per class
 *  2. Calculates how many augmented copies are needed
 *  3. Applies pitch shift + time stretch + noise + volume scaling
 *  4. Stops when target_samples_per_class is reached
 *
 * Use individual functions above only when you need fine-grained control.
 */
export async function runPipeline(params: AugmentPipelineParams): Promise<PipelineResult> {
  return post('/m3-augmentation/pipeline', params);
}
