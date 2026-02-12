/**
 * Data Acquisition Service – Local Python API
 * ==============================================
 * Points to http://localhost:8000 (the local FastAPI backend).
 * Replaces the previous Supabase Edge Function URLs.
 */

import axios from "axios";

const API_BASE = "http://localhost:8000/api";

export interface SensorConfig {
  index: number;
  name: string;
  channels: number;
  default_sr: number;
}

export interface HardwareConfig {
  hw_type: "hydrophone" | "7mems" | "16mems";
  device_id?: number;
  host?: string;
  port?: number;
  sample_rate?: number;
}

/**
 * List all available PortAudio input devices on the host machine.
 */
export async function getDevices(): Promise<SensorConfig[]> {
  const resp = await axios.get<SensorConfig[]>(`${API_BASE}/hardware/devices`);
  return resp.data;
}

/**
 * Upload an audio file and extract features.
 */
export async function extractFeatures(
  file: File,
  config: Record<string, any> = {}
): Promise<{ features: number[]; length: number }> {
  const form = new FormData();
  form.append("file", file);
  form.append("config_json", JSON.stringify(config));
  const resp = await axios.post(`${API_BASE}/processing/extract-features`, form);
  return resp.data;
}

/**
 * Upload a multi-channel audio file and estimate Direction of Arrival.
 */
export async function estimateDOA(
  file: File,
  micDistance: number = 0.05,
  channelA: number = 0,
  channelB: number = 1
): Promise<{ angle_deg: number; tdoa_seconds: number }> {
  const form = new FormData();
  form.append("file", file);
  form.append("mic_distance", String(micDistance));
  form.append("channel_a", String(channelA));
  form.append("channel_b", String(channelB));
  const resp = await axios.post(`${API_BASE}/analysis/doa`, form);
  return resp.data;
}

/**
 * Get a Mel spectrogram as a Base64 image.
 */
export async function getSpectrogram(
  file: File
): Promise<{ image_base64: string; content_type: string }> {
  const form = new FormData();
  form.append("file", file);
  const resp = await axios.post(`${API_BASE}/visualize/spectrogram`, form);
  return resp.data;
}

/**
 * Get a waveform plot as a Base64 image.
 */
export async function getWaveform(
  file: File
): Promise<{ image_base64: string; content_type: string }> {
  const form = new FormData();
  form.append("file", file);
  const resp = await axios.post(`${API_BASE}/visualize/waveform`, form);
  return resp.data;
}


/**
 * Train a model on extracted features.
 */
export async function trainModel(params: {
  data_path: string;
  model_type?: string;
  feature_config?: Record<string, any>;
  test_split?: number;
  normalize?: boolean;
}): Promise<{
  model_id: string;
  accuracy: number;
  classification_report: Record<string, any>;
}> {
  const resp = await axios.post(`${API_BASE}/model/train`, params);
  return resp.data;
}

/**
 * Health check for the Python backend.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const resp = await axios.get(`${API_BASE}/health`);
    return resp.data.status === "ok";
  } catch {
    return false;
  }
}

/**
 * Split a dataset into train / validation / test sets.
 */
export async function organizeDataset(params: {
  input_dir: string;
  output_dir: string;
  test_size?: number;
  val_size?: number;
}): Promise<{ status: string; output_dir: string; splits: Record<string, number> }> {
  const resp = await axios.post(`${API_BASE}/data/organize-splits`, params);
  return resp.data;
}

/**
 * List directories that contain audio files.
 */
export async function listAudioDirectories(
  basePath: string
): Promise<{ directories: Array<{ path: string; file_count: number }> }> {
  const resp = await axios.post(`${API_BASE}/data/list-audio-dirs`, {
    base_path: basePath,
  });
  return resp.data;
}

/**
 * Map directories to class names and copy audio files.
 */
export async function renameAndCopyClasses(
  directoryClassMap: Record<string, string>,
  outputBasePath: string
): Promise<{ status: string; classes: Record<string, number>; total_files: number }> {
  const resp = await axios.post(`${API_BASE}/data/rename-class`, {
    directory_class_map: directoryClassMap,
    output_base_path: outputBasePath,
  });
  return resp.data;
}
