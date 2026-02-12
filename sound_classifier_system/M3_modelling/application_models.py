"""
Application Models — Anomaly Detection & Clustering
=====================================================
Purpose:
    Provides M5 application-level ML capabilities that operate on
    pre-extracted feature vectors. These are higher-level than the M3
    training pipeline: they use trained models or unsupervised methods
    to derive actionable intelligence from audio data.

Capabilities:
    1. **Anomaly Detection** — Train on "normal" ambient sounds, then
       flag deviations as anomalies. Use cases:
         • Ambient seafloor noise vs motorised vessel
         • Ambient jungle noise vs poacher (gunshot / fence cutting)
       The anomalies can then be classified by the trained model.

    2. **Audio Clustering** — Group unlabelled sound events by feature
       similarity using unsupervised learning. Use cases:
         • Discover new sound classes in field recordings
         • Label clusters → retrain classifier with new classes

    3. **Scene Analysis** — Combine frequency-band energy profiling
       with anomaly scoring and classification to produce a holistic
       acoustic scene report.

Architecture:
    Called by FastAPI endpoints in ``endpoints.py``:
        POST /m5-application/anomaly-detection → detect_anomalies()
        POST /m5-application/clustering        → cluster_audio()
        POST /m5-application/scene-analysis    → analyze_scene()
"""

import os
import logging
import pickle
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np
import joblib

logger = logging.getLogger(__name__)


# =====================================================================
#  Anomaly Detection
# =====================================================================

def detect_anomalies(
    features: np.ndarray,
    method: str = "isolation_forest",
    threshold: float = -0.5,
    contamination: float = 0.1,
    model_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detect anomalous audio samples using unsupervised methods.

    Parameters
    ----------
    features : np.ndarray
        2D array of shape (n_samples, n_features).
    method : str
        One of 'isolation_forest', 'one_class_svm', 'autoencoder'.
    threshold : float
        Decision threshold (for Isolation Forest: scores < threshold
        are anomalies; typical range -1 to 0).
    contamination : float
        Expected fraction of anomalies (0–0.5). Only used during
        fitting if no pre-trained model is supplied.
    model_path : str, optional
        Path to a pre-fitted anomaly model. If None, a new model is
        trained on the provided features (assumes mostly normal data).

    Returns
    -------
    dict with keys:
        anomalies      : list[int]    — indices of anomalous samples
        scores         : list[float]  — anomaly score per sample
        labels         : list[int]    — 1 = normal, -1 = anomaly
        model_path     : str          — where the model was saved
        method         : str
        stats          : dict         — summary statistics
    """
    X = np.asarray(features, dtype=np.float64)
    if X.ndim == 1:
        X = X.reshape(1, -1)

    # Normalise features for better anomaly separation
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Load or create model
    if model_path and os.path.exists(model_path):
        bundle = joblib.load(model_path)
        model = bundle["model"]
        scaler = bundle.get("scaler", scaler)
        X_scaled = scaler.transform(X)
        logger.info("Loaded pre-trained anomaly model from %s", model_path)
    else:
        if method == "one_class_svm":
            from sklearn.svm import OneClassSVM
            model = OneClassSVM(kernel="rbf", gamma="scale", nu=contamination)
        else:
            # Default: Isolation Forest (fast, robust, works well for audio)
            from sklearn.ensemble import IsolationForest
            model = IsolationForest(
                contamination=contamination,
                n_estimators=200,
                random_state=42,
            )
        model.fit(X_scaled)

        # Save model for reuse
        data_dir = os.environ.get(
            "ACOUSTIC_DATA_DIR", os.path.expanduser("~/acoustic_ai_data")
        )
        model_dir = os.path.join(data_dir, "models", "anomaly")
        os.makedirs(model_dir, exist_ok=True)
        import uuid
        save_path = os.path.join(model_dir, f"anomaly_{method}_{uuid.uuid4().hex[:8]}.joblib")
        joblib.dump({"model": model, "scaler": scaler, "method": method}, save_path)
        model_path = save_path
        logger.info("Trained new anomaly model → %s", save_path)

    # Predict
    labels = model.predict(X_scaled)           # 1 = normal, -1 = anomaly
    scores = model.decision_function(X_scaled)  # higher = more normal

    anomaly_indices = [int(i) for i, lbl in enumerate(labels) if lbl == -1]

    return {
        "anomalies": anomaly_indices,
        "scores": scores.tolist(),
        "labels": labels.tolist(),
        "model_path": model_path,
        "method": method,
        "stats": {
            "total_samples": len(X),
            "anomaly_count": len(anomaly_indices),
            "anomaly_ratio": len(anomaly_indices) / max(len(X), 1),
            "mean_score": float(np.mean(scores)),
            "min_score": float(np.min(scores)),
        },
    }


# =====================================================================
#  Audio Clustering
# =====================================================================

def cluster_audio(
    features: np.ndarray,
    method: str = "kmeans",
    n_clusters: int = 5,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Cluster audio samples by feature similarity.

    Parameters
    ----------
    features : np.ndarray
        2D array of shape (n_samples, n_features).
    method : str
        One of 'kmeans', 'dbscan', 'hierarchical'.
    n_clusters : int
        Number of clusters (ignored for DBSCAN which auto-detects).
    parameters : dict, optional
        Additional algorithm-specific params:
          - KMeans: max_iter, n_init
          - DBSCAN: eps, min_samples
          - Hierarchical: linkage

    Returns
    -------
    dict with keys:
        cluster_labels    : list[int]     — cluster id per sample
        cluster_centers   : list[list]    — centroid coordinates (KMeans only)
        n_clusters_found  : int
        silhouette_score  : float         — quality metric (-1 to 1)
        cluster_sizes     : dict[int,int] — samples per cluster
    """
    params = parameters or {}
    X = np.asarray(features, dtype=np.float64)
    if X.ndim == 1:
        X = X.reshape(1, -1)

    # Normalise
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if method == "dbscan":
        from sklearn.cluster import DBSCAN
        eps = params.get("eps", 0.5)
        min_samples = params.get("min_samples", 5)
        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(X_scaled)
        centers = []

    elif method == "hierarchical":
        from sklearn.cluster import AgglomerativeClustering
        linkage = params.get("linkage", "ward")
        model = AgglomerativeClustering(
            n_clusters=n_clusters, linkage=linkage,
        )
        labels = model.fit_predict(X_scaled)
        centers = []

    else:  # kmeans (default)
        from sklearn.cluster import KMeans
        model = KMeans(
            n_clusters=n_clusters,
            n_init=params.get("n_init", 10),
            max_iter=params.get("max_iter", 300),
            random_state=42,
        )
        labels = model.fit_predict(X_scaled)
        centers = model.cluster_centers_.tolist()

    # Compute quality metric
    unique_labels = set(labels)
    unique_labels.discard(-1)  # noise label for DBSCAN
    n_found = len(unique_labels)

    silhouette = -1.0
    if n_found >= 2 and n_found < len(X):
        from sklearn.metrics import silhouette_score
        silhouette = float(silhouette_score(X_scaled, labels))

    # Cluster sizes
    cluster_sizes = {}
    for lbl in labels:
        cluster_sizes[int(lbl)] = cluster_sizes.get(int(lbl), 0) + 1

    return {
        "cluster_labels": labels.tolist(),
        "cluster_centers": centers,
        "n_clusters_found": n_found,
        "silhouette_score": silhouette,
        "cluster_sizes": cluster_sizes,
    }


# =====================================================================
#  Scene Analysis (composite)
# =====================================================================

def analyze_scene(
    audio: np.ndarray,
    sr: int,
    model_bundle: Optional[Dict] = None,
    time_resolution: float = 1.0,
) -> Dict[str, Any]:
    """
    Holistic acoustic scene analysis combining:
      1. Frequency-band energy profiling
      2. Anomaly scoring (if a model is available)
      3. Event detection via energy thresholding

    Parameters
    ----------
    audio : np.ndarray
        1D audio time series.
    sr : int
        Sample rate.
    model_bundle : dict, optional
        Pre-loaded model bundle from joblib (with 'model', 'scaler', 'config').
    time_resolution : float
        Seconds per analysis window.

    Returns
    -------
    dict with scene_labels, events, band_energies, anomaly_score.
    """
    import librosa

    # Frequency band profiling
    try:
        from M2_processing.frequency_filter import frequency_band_energy
        bands = frequency_band_energy(audio, sr)
    except ImportError:
        bands = []

    # Segment into time windows and analyse each
    window_samples = int(time_resolution * sr)
    events: List[Dict] = []
    rms_values: List[float] = []

    for i in range(0, len(audio) - window_samples, window_samples):
        window = audio[i:i + window_samples]
        rms = float(np.sqrt(np.mean(window ** 2)))
        rms_values.append(rms)
        time_sec = i / sr

        # Simple event detection: energy significantly above average
        if len(rms_values) > 1:
            mean_rms = np.mean(rms_values[:-1])
            if rms > mean_rms * 2.0 and rms > 0.01:
                events.append({
                    "time": round(time_sec, 2),
                    "duration": time_resolution,
                    "energy": round(rms, 4),
                    "type": "energy_spike",
                })

    # Scene labelling based on dominant frequency bands
    scene_labels = []
    if bands:
        dominant = max(bands, key=lambda b: b.get("energy_ratio", 0))
        scene_labels.append(dominant.get("name", "unknown"))

    # Anomaly scoring if model available
    anomaly_score = None
    if model_bundle:
        try:
            from M2_processing.dataset_preparation.feature_extraction import (
                extract_features, FeatureConfig,
            )
            import tempfile
            import soundfile as sf

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio, sr)
                cfg = FeatureConfig(**model_bundle.get("config", {}))
                feat = extract_features(tmp.name, config=cfg)
                os.unlink(tmp.name)

            if feat is not None:
                clf = model_bundle["model"]
                scaler = model_bundle.get("scaler")
                X = feat.reshape(1, -1)
                if scaler:
                    X = scaler.transform(X)
                if hasattr(clf, "decision_function"):
                    anomaly_score = float(clf.decision_function(X)[0])
                elif hasattr(clf, "predict_proba"):
                    anomaly_score = float(np.max(clf.predict_proba(X)))
        except Exception as e:
            logger.warning("Scene anomaly scoring failed: %s", e)

    return {
        "scene_labels": scene_labels,
        "events": events,
        "band_energies": [b for b in bands] if bands else [],
        "anomaly_score": anomaly_score,
        "duration_seconds": round(len(audio) / sr, 2),
        "n_windows": len(rms_values),
    }
