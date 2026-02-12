/**
 * ML Processing Service – Local Python API
 * ==========================================
 * Points to http://localhost:8000 (the local FastAPI backend).
 * Replaces the previous Supabase Edge Function URLs.
 */

import axios from "axios";

const API_BASE = "http://localhost:8000/api";

export interface FeatureExtractionParams {
  mfcc: boolean;
  n_mfcc: number;
  delta_mfcc: boolean;
  chroma: boolean;
  mel: boolean;
  contrast: boolean;
  tonnetz: boolean;
  zcr: boolean;
  rms: boolean;
  spectral_centroid: boolean;
  spectral_bandwidth: boolean;
  spectral_rolloff: boolean;
  spectral_flatness: boolean;
  spectral_flux: boolean;
  stats: string[];
}

export interface ModelTrainingParams {
  data_path: string;
  model_type: "random_forest" | "svm" | "knn";
  feature_config: FeatureExtractionParams;
  test_split: number;
  normalize: boolean;
}

export interface ModelEvaluationResult {
  model_id: string;
  accuracy: number;
  classification_report: Record<string, any>;
  model_path: string;
}

/**
 * Extract features from uploaded audio files.
 */
export async function extractFeatures(
  file: File,
  params: Partial<FeatureExtractionParams> = {}
): Promise<{ features: number[]; length: number }> {
  const form = new FormData();
  form.append("file", file);
  form.append("config_json", JSON.stringify(params));
  const resp = await axios.post(`${API_BASE}/processing/extract-features`, form);
  return resp.data;
}

/**
 * Train a machine-learning model.
 */
export async function trainModel(
  params: ModelTrainingParams
): Promise<ModelEvaluationResult> {
  const resp = await axios.post(`${API_BASE}/model/train`, params);
  return resp.data;
}

/**
 * Classify a single audio file using the latest trained model.
 */
export async function classifyAudio(
  file: File,
  sensorId: string = "default"
): Promise<{ prediction: string; confidence: number }> {
  const form = new FormData();
  form.append("file", file);
  form.append("sensor_id", sensorId);
  const resp = await axios.post(`${API_BASE}/classify-audio/`, form);
  return resp.data;
}

/**
 * Get a Mel spectrogram visualisation (Base64 PNG).
 */
export async function getSpectrogram(
  file: File
): Promise<{ image_base64: string }> {
  const form = new FormData();
  form.append("file", file);
  const resp = await axios.post(`${API_BASE}/visualize/spectrogram`, form);
  return resp.data;
}

/**
 * Get feature default configuration.
 */
export function getDefaultFeatureConfig(): FeatureExtractionParams {
  return {
    mfcc: true,
    n_mfcc: 40,
    delta_mfcc: true,
    chroma: true,
    mel: true,
    contrast: true,
    tonnetz: true,
    zcr: true,
    rms: true,
    spectral_centroid: true,
    spectral_bandwidth: true,
    spectral_rolloff: true,
    spectral_flatness: true,
    spectral_flux: false,
    stats: ["mean", "std"],
  };
}
