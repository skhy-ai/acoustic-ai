/**
 * Application Service – Local Python API (M5 Layer)
 * ====================================================
 * Points to http://localhost:8000 (the local FastAPI backend).
 *
 * PURPOSE:
 *   M5 application-level operations that sit ABOVE training:
 *     • Classification   – classify audio using trained model
 *     • Anomaly Detection – IsolationForest / OneClassSVM on features
 *     • Clustering        – KMeans / DBSCAN / Hierarchical for labelling
 *     • Scene Analysis    – combined frequency + anomaly + event detection
 *     • Real-time         – WebSocket streaming for live classification
 *
 * USE CASES:
 *   Anomaly: ambient seafloor vs motorised vessel, jungle vs poacher
 *   Clustering: group unlabelled recordings → label → retrain
 */

const API_BASE = 'http://localhost:8000/api';

/* ── Types ── */

export interface ClassificationParams {
  threshold: number;
  classes: string[];
  multiLabel: boolean;
}

export interface SceneAnalysisParams {
  timeResolution: number; // seconds
  spatialAnalysis: boolean;
  eventDetection: boolean;
}

export interface AnomalyDetectionParams {
  threshold: number;
  method: 'isolation_forest' | 'one_class_svm';
  contamination: number;
  model_path?: string;
}

export interface ClusteringParams {
  method: 'kmeans' | 'dbscan' | 'hierarchical';
  numClusters?: number;
  parameters: Record<string, any>;
}

export interface RealTimeParams {
  bufferSize: number;
  processingInterval: number; // milliseconds
  outputFormat: 'json' | 'websocket' | 'mqtt';
}

export interface ClassificationResult {
  label: string;
  confidence: number;
  class_probabilities?: Record<string, number>;
}

export interface AnomalyResult {
  anomalies: number[];
  scores: number[];
  labels: number[];
  model_path: string;
  method: string;
  stats: {
    total_samples: number;
    anomaly_count: number;
    anomaly_ratio: number;
    mean_score: number;
    min_score: number;
  };
}

export interface ClusterResult {
  cluster_labels: number[];
  cluster_centers: number[][];
  n_clusters_found: number;
  silhouette_score: number;
  cluster_sizes: Record<number, number>;
}

export interface SceneResult {
  scene_labels: string[];
  events: Array<{
    time: number;
    duration: number;
    energy: number;
    type: string;
  }>;
  band_energies: any[];
  anomaly_score: number | null;
  duration_seconds: number;
  n_windows: number;
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

async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Public API ── */

/**
 * Classify audio content using the trained model.
 */
export async function classifyAudio(
  file: File,
  sensorId: string = 'default',
): Promise<{ classifications: ClassificationResult[]; sensor_id: string }> {
  const form = new FormData();
  form.append('file', file);
  form.append('sensor_id', sensorId);
  return postForm('/m5-application/classify', form);
}

/**
 * Perform acoustic scene analysis.
 * Combines frequency-band profiling, event detection, and optional anomaly scoring.
 */
export async function analyzeScene(
  file: File,
  params: SceneAnalysisParams,
): Promise<SceneResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('config_json', JSON.stringify(params));
  return postForm('/m5-application/scene-analysis', form);
}

/**
 * Detect acoustic anomalies using unsupervised methods.
 *
 * Use cases:
 *   - Ambient seafloor noise vs motorised vessel
 *   - Ambient jungle noise vs poacher (gunshot / fence cutting)
 *   - Train on "normal" → flag deviations → classify anomalies
 */
export async function detectAnomalies(
  features: number[][],
  params: AnomalyDetectionParams,
): Promise<AnomalyResult> {
  return post('/m5-application/anomaly-detection', {
    features,
    method: params.method,
    threshold: params.threshold,
    contamination: params.contamination,
    model_path: params.model_path,
  });
}

/**
 * Cluster audio data by feature similarity.
 *
 * Use case: Group unlabelled sound events → human labels clusters
 *           → retrain classifier with new classes.
 */
export async function clusterAudio(
  features: number[][],
  params: ClusteringParams,
): Promise<ClusterResult> {
  return post('/m5-application/clustering', {
    features,
    method: params.method,
    n_clusters: params.numClusters ?? 5,
    parameters: params.parameters,
  });
}

/**
 * Start real-time audio processing via WebSocket.
 * Returns the WebSocket URL to connect to.
 */
export function getRealTimeStreamUrl(sensorId: string): string {
  return `ws://localhost:8000/api/ws/stream/${sensorId}`;
}
