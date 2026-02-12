"""
Advanced Feature Extraction Pipeline
======================================
Configurable feature extraction that supports individual feature toggling
from the frontend.  Each feature is computed per-frame and then
aggregated with statistical moments (mean, std, skew, kurtosis).
"""

import numpy as np
import librosa
import pickle
import os
import gc
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from scipy import stats


@dataclass
class FeatureConfig:
    """Configuration object – mirrors the frontend checkboxes."""
    mfcc: bool = True
    n_mfcc: int = 40
    delta_mfcc: bool = True
    chroma: bool = True
    mel: bool = True
    contrast: bool = True
    tonnetz: bool = True
    zcr: bool = True
    rms: bool = True
    spectral_centroid: bool = True
    spectral_bandwidth: bool = True
    spectral_rolloff: bool = True
    spectral_flatness: bool = True
    spectral_flux: bool = False          # computed manually
    # Aggregation
    stats: List[str] = field(default_factory=lambda: ["mean", "std"])


def _aggregate(feature_matrix: np.ndarray, stat_funcs: List[str]) -> np.ndarray:
    """
    Collapse a (n_features, n_frames) matrix into a 1-D vector
    by computing statistical moments across the time axis.
    """
    parts: List[np.ndarray] = []
    for s in stat_funcs:
        if s == "mean":
            parts.append(np.mean(feature_matrix, axis=1))
        elif s == "std":
            parts.append(np.std(feature_matrix, axis=1))
        elif s == "skew":
            parts.append(stats.skew(feature_matrix, axis=1))
        elif s == "kurtosis":
            parts.append(stats.kurtosis(feature_matrix, axis=1))
        elif s == "median":
            parts.append(np.median(feature_matrix, axis=1))
    return np.hstack(parts)


def extract_features(file_path: str,
                     config: Optional[FeatureConfig] = None) -> Optional[np.ndarray]:
    """
    Extract audio features from a single file.

    Parameters
    ----------
    file_path : str
        Path to the audio file.
    config : FeatureConfig
        Which features to compute.  Defaults to all enabled.

    Returns
    -------
    1-D numpy array or None on error.
    """
    if config is None:
        config = FeatureConfig()

    try:
        audio, sr = librosa.load(file_path, res_type="kaiser_fast")
        n_fft = min(2048, len(audio))
        if n_fft < 64:
            return None

        parts: List[np.ndarray] = []

        # ---- Cepstral ------------------------------------------------
        if config.mfcc:
            mfccs = librosa.feature.mfcc(y=audio, sr=sr,
                                          n_mfcc=config.n_mfcc,
                                          n_fft=n_fft)
            parts.append(_aggregate(mfccs, config.stats))

            if config.delta_mfcc:
                delta = librosa.feature.delta(mfccs)
                delta2 = librosa.feature.delta(mfccs, order=2)
                parts.append(_aggregate(delta, config.stats))
                parts.append(_aggregate(delta2, config.stats))

        # ---- Chroma / Tonnetz ----------------------------------------
        if config.chroma:
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr,
                                                  n_fft=n_fft)
            parts.append(_aggregate(chroma, config.stats))

        if config.tonnetz:
            harmonic = librosa.effects.harmonic(audio)
            tonnetz = librosa.feature.tonnetz(y=harmonic, sr=sr)
            parts.append(_aggregate(tonnetz, config.stats))

        # ---- Mel spectrogram -----------------------------------------
        if config.mel:
            mel = librosa.feature.melspectrogram(y=audio, sr=sr,
                                                  n_fft=n_fft)
            parts.append(_aggregate(mel, config.stats))

        # ---- Spectral ------------------------------------------------
        if config.contrast:
            contrast = librosa.feature.spectral_contrast(y=audio, sr=sr,
                                                          n_fft=n_fft)
            parts.append(_aggregate(contrast, config.stats))

        if config.spectral_centroid:
            centroid = librosa.feature.spectral_centroid(y=audio, sr=sr,
                                                         n_fft=n_fft)
            parts.append(_aggregate(centroid, config.stats))

        if config.spectral_bandwidth:
            bw = librosa.feature.spectral_bandwidth(y=audio, sr=sr,
                                                      n_fft=n_fft)
            parts.append(_aggregate(bw, config.stats))

        if config.spectral_rolloff:
            rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr,
                                                        n_fft=n_fft)
            parts.append(_aggregate(rolloff, config.stats))

        if config.spectral_flatness:
            flatness = librosa.feature.spectral_flatness(y=audio)
            parts.append(_aggregate(flatness, config.stats))

        if config.spectral_flux:
            S = np.abs(librosa.stft(audio, n_fft=n_fft))
            flux = np.sqrt(np.sum(np.diff(S, axis=1) ** 2, axis=0))
            flux = flux.reshape(1, -1)
            parts.append(_aggregate(flux, config.stats))

        # ---- Temporal ------------------------------------------------
        if config.zcr:
            zcr = librosa.feature.zero_crossing_rate(audio)
            parts.append(_aggregate(zcr, config.stats))

        if config.rms:
            rms = librosa.feature.rms(y=audio)
            parts.append(_aggregate(rms, config.stats))

        if not parts:
            return None

        return np.hstack(parts)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def extract_and_save_features(data_path: str,
                              feature_folder: str = "../../features",
                              config: Optional[FeatureConfig] = None):
    """
    Batch extraction – processes each class subfolder and saves
    features as pickle files.
    """
    os.makedirs(feature_folder, exist_ok=True)
    if config is None:
        config = FeatureConfig()

    for label in os.listdir(data_path):
        label_path = os.path.join(data_path, label)
        feature_file = os.path.join(feature_folder, f"{label}.pkl")

        if os.path.exists(feature_file):
            print(f"Features for '{label}' already exist. Skipping.")
            continue

        if os.path.isdir(label_path):
            features = []
            for fname in os.listdir(label_path):
                fpath = os.path.join(label_path, fname)
                feat = extract_features(fpath, config)
                if feat is not None:
                    features.append(feat)

            with open(feature_file, "wb") as f:
                pickle.dump(features, f)
            print(f"Saved {len(features)} vectors for '{label}' → {feature_file}")
            del features
            gc.collect()


if __name__ == "__main__":
    data_path = "../../sampled_data/"
    extract_and_save_features(data_path)
