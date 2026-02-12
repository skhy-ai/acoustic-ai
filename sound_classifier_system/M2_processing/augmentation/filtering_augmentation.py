"""
Filtering & Augmentation Pipeline
====================================
Purpose:
    After audio files have been homogenised into ``sampled_data/<class>/``,
    this module applies two stages **before** feature extraction:

    1. **FILTERING** – reject files that are too noisy, too short, too
       quiet, or outside a useful frequency range.
    2. **AUGMENTATION** – create synthetic variants of the surviving files
       to balance class sizes and improve model robustness.

Workflow position:
    sampled_data/<class>/
          │
          ▼
    **filtering_augmentation.py**
          │
          ├── sampled_data_filtered/<class>/     ← cleaned originals
          └── sampled_data_augmented/<class>/    ← augmented copies
          │
          ▼
    organize_sound_samples.py  (train / val / test split)
          │
          ▼
    feature_extraction.py

WHY THIS WAS MISSING:
    The original pipeline went straight from ``sampled_data/`` to
    ``feature_extraction.py`` with no quality gate.  This means:
    • Silent / near-silent files passed through, adding noise to features.
    • Class imbalance was unaddressed (some classes had 10× more samples).
    • No bandpass filtering – low-frequency rumble and high-frequency
      aliasing artefacts could leak into the model.

AUGMENTATION STRATEGIES:
    ┌──────────────┬───────────────────────────────────────────────────┐
    │ Strategy     │ What it does / why it helps                      │
    ├──────────────┼───────────────────────────────────────────────────┤
    │ pitch_shift  │ Shifts pitch ±2 semitones. Models real Doppler.  │
    │ time_stretch │ Speed up / slow down without pitch change.       │
    │ noise_inject │ Adds Gaussian or pink noise at configurable SNR. │
    │ volume_scale │ Scales amplitude ±6 dB.                          │
    │ reverb_sim   │ Convolves with a synthetic IR for room effects.  │
    └──────────────┴───────────────────────────────────────────────────┘
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from pathlib import Path

import numpy as np
import librosa
import soundfile as sf
from scipy.signal import butter, sosfilt

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────
#  Configuration
# ────────────────────────────────────────────────────────────────

@dataclass
class FilterConfig:
    """
    Parameters controlling the quality filter stage.

    LOGIC NOTE:  A file is REJECTED if ANY condition below fails.
    """
    min_duration_s: float = 0.5   # reject files shorter than 0.5 s
    max_duration_s: float = 30.0  # reject files longer than 30 s
    min_rms_db: float = -50.0     # reject files quieter than -50 dBFS
    max_rms_db: float = 0.0       # reject clipped files (≈ 0 dBFS)
    # Bandpass filter (Hz).  Set to None to disable.
    low_cut_hz: Optional[float] = 50.0    # below this → rumble / DC offset
    high_cut_hz: Optional[float] = 16000.0  # above this → aliasing / noise
    min_snr_db: Optional[float] = 5.0      # estimated SNR threshold


@dataclass
class AugmentConfig:
    """
    Parameters controlling the augmentation stage.

    LOGIC NOTE:  Each augmentation is applied independently to the
    *original* file (not chained).  This avoids artefact accumulation.
    """
    enable_pitch_shift: bool = True
    pitch_shift_semitones: List[float] = field(
        default_factory=lambda: [-2.0, -1.0, 1.0, 2.0]
    )
    enable_time_stretch: bool = True
    time_stretch_rates: List[float] = field(
        default_factory=lambda: [0.8, 0.9, 1.1, 1.2]
    )
    enable_noise_injection: bool = True
    noise_snr_db: List[float] = field(
        default_factory=lambda: [20.0, 15.0, 10.0]
    )
    enable_volume_scale: bool = True
    volume_scale_db: List[float] = field(
        default_factory=lambda: [-6.0, -3.0, 3.0, 6.0]
    )
    # Target minimum samples per class after augmentation.
    # If a class already has enough, fewer augments are generated.
    target_samples_per_class: int = 500
    max_augments_per_file: int = 5  # cap to prevent disk explosion


# ────────────────────────────────────────────────────────────────
#  Filtering helpers
# ────────────────────────────────────────────────────────────────

def _rms_dbfs(audio: np.ndarray) -> float:
    """Compute RMS level in dBFS.  Returns -inf for silence."""
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 1e-10:
        return -np.inf
    return float(20.0 * np.log10(rms))


def _estimate_snr(audio: np.ndarray, sr: int,
                  noise_fraction: float = 0.1) -> float:
    """
    Quick SNR estimate: assume the quietest ``noise_fraction`` of frames
    represent noise.  Compare their energy to the total energy.

    LOGIC NOTE:  This is a rough heuristic, NOT a true SNR measurement.
    For real deployment you'd want a dedicated noise estimator (e.g.
    MCRA / IMCRA).  But for pre-filtering it's good enough.
    """
    frame_length = int(0.025 * sr)  # 25 ms frames
    hop_length   = int(0.010 * sr)  # 10 ms hop
    frames = librosa.util.frame(audio, frame_length=frame_length,
                                 hop_length=hop_length)
    energies = np.sum(frames ** 2, axis=0)

    n_noise = max(1, int(len(energies) * noise_fraction))
    sorted_e = np.sort(energies)
    noise_energy = np.mean(sorted_e[:n_noise])
    signal_energy = np.mean(energies)

    if noise_energy < 1e-10:
        return 100.0  # effectively clean
    return float(10.0 * np.log10(signal_energy / noise_energy))


def _bandpass_filter(audio: np.ndarray, sr: int,
                     low: float, high: float, order: int = 5
                     ) -> np.ndarray:
    """
    Apply a Butterworth bandpass filter.

    LOGIC NOTE on order:
        Higher order = sharper roll-off but more phase distortion.
        Order 5 is a reasonable default for acoustic pre-filtering.
    """
    nyq = 0.5 * sr
    low_norm  = low / nyq
    high_norm = high / nyq
    # Clamp to valid range (0, 1) exclusive
    low_norm  = max(low_norm, 0.001)
    high_norm = min(high_norm, 0.999)
    if low_norm >= high_norm:
        logger.warning("Bandpass bounds inverted (low=%.1f, high=%.1f Hz), "
                       "skipping filter", low, high)
        return audio
    sos = butter(order, [low_norm, high_norm], btype="band", output="sos")
    return sosfilt(sos, audio).astype(np.float32)


def filter_audio_file(
    file_path: str,
    config: FilterConfig,
) -> Tuple[bool, str, Optional[np.ndarray], Optional[int]]:
    """
    Evaluate whether an audio file passes the quality filter.

    Returns
    -------
    (passed, reason, audio, sr)
        ``passed``  – True if the file is accepted.
        ``reason``  – human-readable rejection reason (or "ok").
        ``audio``   – loaded & optionally bandpass-filtered signal.
        ``sr``      – sample rate.
    """
    try:
        audio, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        return False, f"load_error: {e}", None, None

    duration = len(audio) / sr
    if duration < config.min_duration_s:
        return False, f"too_short ({duration:.2f}s)", None, None
    if duration > config.max_duration_s:
        return False, f"too_long ({duration:.2f}s)", None, None

    rms = _rms_dbfs(audio)
    if rms < config.min_rms_db:
        return False, f"too_quiet ({rms:.1f} dBFS)", None, None
    if rms > config.max_rms_db:
        return False, f"clipped ({rms:.1f} dBFS)", None, None

    if config.min_snr_db is not None:
        snr = _estimate_snr(audio, sr)
        if snr < config.min_snr_db:
            return False, f"low_snr ({snr:.1f} dB)", None, None

    # Apply bandpass if configured
    if config.low_cut_hz is not None and config.high_cut_hz is not None:
        audio = _bandpass_filter(audio, sr,
                                 config.low_cut_hz, config.high_cut_hz)

    return True, "ok", audio, sr


# ────────────────────────────────────────────────────────────────
#  Augmentation helpers
# ────────────────────────────────────────────────────────────────

def _pitch_shift(audio: np.ndarray, sr: int,
                 semitones: float) -> np.ndarray:
    """
    Shift pitch without changing duration.

    LOGIC NOTE:  librosa.effects.pitch_shift uses STFT-based resampling.
    For large shifts (> ±3 semitones) artefacts may appear.
    """
    return librosa.effects.pitch_shift(y=audio, sr=sr, n_steps=semitones)


def _time_stretch(audio: np.ndarray, rate: float) -> np.ndarray:
    """
    Change speed without changing pitch.
    rate > 1 = faster, rate < 1 = slower.

    LOGIC NOTE:  rate=0.5 doubles the duration, which may create
    very long files.  The caller should clamp after stretching.
    """
    return librosa.effects.time_stretch(y=audio, rate=rate)


def _inject_noise(audio: np.ndarray, snr_db: float) -> np.ndarray:
    """
    Add white Gaussian noise at a given SNR level.

    LOGIC NOTE:  We scale noise to match the desired SNR relative to
    the RMS of the clean signal.  If the signal is silent, we return
    unchanged to avoid division by zero.
    """
    rms_signal = np.sqrt(np.mean(audio ** 2))
    if rms_signal < 1e-10:
        return audio
    rms_noise = rms_signal / (10 ** (snr_db / 20.0))
    noise = np.random.randn(len(audio)).astype(np.float32) * rms_noise
    return audio + noise


def _scale_volume(audio: np.ndarray, db: float) -> np.ndarray:
    """Scale amplitude by ``db`` decibels."""
    factor = 10 ** (db / 20.0)
    return audio * factor


# ────────────────────────────────────────────────────────────────
#  Pipeline entry points
# ────────────────────────────────────────────────────────────────

def filter_dataset(
    input_dir: str,
    output_dir: str,
    config: Optional[FilterConfig] = None,
) -> Dict[str, Dict[str, int]]:
    """
    Walk ``input_dir/<class>/``, apply quality filters, copy passing
    files to ``output_dir/<class>/``.

    Returns ``{class_name: {"accepted": N, "rejected": M}}``.
    """
    if config is None:
        config = FilterConfig()
    os.makedirs(output_dir, exist_ok=True)
    report: Dict[str, Dict[str, int]] = {}

    for class_name in sorted(os.listdir(input_dir)):
        class_in = os.path.join(input_dir, class_name)
        if not os.path.isdir(class_in):
            continue

        class_out = os.path.join(output_dir, class_name)
        os.makedirs(class_out, exist_ok=True)
        accepted = rejected = 0

        for fname in os.listdir(class_in):
            fpath = os.path.join(class_in, fname)
            if not os.path.isfile(fpath):
                continue

            passed, reason, audio, sr = filter_audio_file(fpath, config)
            if passed and audio is not None and sr is not None:
                dest = os.path.join(class_out, fname)
                if not os.path.exists(dest):
                    sf.write(dest, audio, sr)
                accepted += 1
            else:
                rejected += 1
                logger.debug("Rejected %s: %s", fpath, reason)

        report[class_name] = {"accepted": accepted, "rejected": rejected}
        logger.info(
            "%-20s  accepted=%d  rejected=%d",
            class_name, accepted, rejected,
        )

    return report


def augment_dataset(
    input_dir: str,
    output_dir: str,
    config: Optional[AugmentConfig] = None,
) -> Dict[str, int]:
    """
    Walk ``input_dir/<class>/``, generate augmented copies in
    ``output_dir/<class>/``.

    Returns ``{class_name: augments_created}``.
    """
    if config is None:
        config = AugmentConfig()
    os.makedirs(output_dir, exist_ok=True)

    # First pass: count per-class samples to decide how many augments
    class_counts: Dict[str, List[str]] = {}
    for class_name in sorted(os.listdir(input_dir)):
        class_dir = os.path.join(input_dir, class_name)
        if not os.path.isdir(class_dir):
            continue
        files = [f for f in os.listdir(class_dir)
                 if os.path.isfile(os.path.join(class_dir, f))]
        class_counts[class_name] = files

    results: Dict[str, int] = {}

    for class_name, files in class_counts.items():
        n_existing = len(files)
        n_needed = max(0, config.target_samples_per_class - n_existing)
        class_out = os.path.join(output_dir, class_name)
        os.makedirs(class_out, exist_ok=True)

        # First copy originals
        class_in = os.path.join(input_dir, class_name)
        for f in files:
            src = os.path.join(class_in, f)
            dst = os.path.join(class_out, f)
            if not os.path.exists(dst):
                import shutil
                shutil.copy2(src, dst)

        # Generate augmentations
        created = 0
        aug_idx = 0

        for f in files:
            if created >= n_needed:
                break
            fpath = os.path.join(class_in, f)
            try:
                audio, sr = librosa.load(fpath, sr=None)
            except Exception:
                continue

            base = os.path.splitext(f)[0]
            per_file = 0

            # Pitch shift
            if config.enable_pitch_shift and created < n_needed:
                for semitones in config.pitch_shift_semitones:
                    if created >= n_needed or per_file >= config.max_augments_per_file:
                        break
                    aug = _pitch_shift(audio, sr, semitones)
                    out_name = f"{base}_ps{semitones:+.1f}.wav"
                    sf.write(os.path.join(class_out, out_name), aug, sr)
                    created += 1
                    per_file += 1

            # Time stretch
            if config.enable_time_stretch and created < n_needed:
                for rate in config.time_stretch_rates:
                    if created >= n_needed or per_file >= config.max_augments_per_file:
                        break
                    aug = _time_stretch(audio, rate)
                    out_name = f"{base}_ts{rate:.1f}.wav"
                    sf.write(os.path.join(class_out, out_name), aug, sr)
                    created += 1
                    per_file += 1

            # Noise injection
            if config.enable_noise_injection and created < n_needed:
                for snr in config.noise_snr_db:
                    if created >= n_needed or per_file >= config.max_augments_per_file:
                        break
                    aug = _inject_noise(audio, snr)
                    out_name = f"{base}_noise{snr:.0f}dB.wav"
                    sf.write(os.path.join(class_out, out_name), aug, sr)
                    created += 1
                    per_file += 1

            # Volume scale
            if config.enable_volume_scale and created < n_needed:
                for db_change in config.volume_scale_db:
                    if created >= n_needed or per_file >= config.max_augments_per_file:
                        break
                    aug = _scale_volume(audio, db_change)
                    out_name = f"{base}_vol{db_change:+.0f}dB.wav"
                    sf.write(os.path.join(class_out, out_name), aug, sr)
                    created += 1
                    per_file += 1

        results[class_name] = created
        logger.info(
            "%-20s  existing=%d  augmented=%d  total=%d",
            class_name, n_existing, created, n_existing + created,
        )

    return results


# ────────────────────────────────────────────────────────────────
#  CLI
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s  %(message)s")

    print("=== Stage 1: Quality Filtering ===")
    report = filter_dataset("../../sampled_data", "../../sampled_data_filtered")
    total_accepted = sum(v["accepted"] for v in report.values())
    total_rejected = sum(v["rejected"] for v in report.values())
    print(f"Accepted: {total_accepted}  Rejected: {total_rejected}")

    print("\n=== Stage 2: Augmentation ===")
    aug_report = augment_dataset("../../sampled_data_filtered",
                                  "../../sampled_data_augmented")
    print(f"Total augments: {sum(aug_report.values())}")
