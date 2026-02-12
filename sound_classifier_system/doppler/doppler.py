"""
Doppler Effect Analysis & Velocity Estimation
===============================================
Purpose:
    Estimate the velocity and direction of a moving sound source by
    analysing the frequency shift between consecutive audio chunks.

Physics background:
    When a source emitting frequency ``f₀`` moves toward a stationary
    observer at velocity ``v``, the observed frequency is:

        f_observed = f₀ × (v_sound / (v_sound − v))     (approaching)
        f_observed = f₀ × (v_sound / (v_sound + v))     (receding)

    Rearranging for velocity:

        v = v_sound × (Δf / f_observed)

    where Δf = f_observed − f₀.

Algorithm:
    1. Compute the Short-Time Fourier Transform (STFT) of each chunk.
    2. Find the dominant frequency in each chunk.
    3. Compute the frequency shift Δf between chunks.
    4. Convert Δf to velocity using the Doppler equation.
    5. Estimate direction (approaching / receding / stationary).
    6. Compute travel-time estimates for a given distance.

LOGIC NOTES:
    • The original implementation used cross-correlation delay, which
      actually measures *time delay* (TDOA), not *frequency shift*.
      That's useful for DOA (→ see doa.py), but NOT for Doppler velocity.
      This rewrite uses FFT-based dominant-frequency estimation instead.
    • For real-world accuracy, the source frequency ``f₀`` must be known
      or estimated from a stationary reference recording.  If not known,
      we estimate it from the first chunk (assuming it starts stationary).
    • Wind, temperature, and medium (air vs water) affect ``v_sound``.
      The default is 343 m/s (air, 20 °C).  For underwater acoustics,
      use ≈ 1500 m/s.

Visualisation data:
    Functions return dicts with all the data needed for frontend plots:
    • time-series of dominant frequencies
    • time-series of estimated velocities
    • approach / recede / stationary labels per frame
"""

import numpy as np
from scipy.signal import stft
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────
#  Core frequency analysis
# ────────────────────────────────────────────────────────────────

def dominant_frequency(audio: np.ndarray, sr: int,
                       n_fft: int = 4096,
                       low_hz: float = 20.0,
                       high_hz: float = 20000.0) -> float:
    """
    Find the dominant frequency in a mono audio signal using FFT.

    Parameters
    ----------
    audio : 1-D array
    sr : int – sample rate
    n_fft : int – FFT size (larger = finer frequency resolution)
    low_hz, high_hz : float – search band

    Returns
    -------
    float – dominant frequency in Hz

    LOGIC NOTE:
        We use a Hann window to reduce spectral leakage.
        The frequency resolution is ``sr / n_fft`` Hz.
        For a 44100 Hz signal with n_fft=4096, that's ≈ 10.8 Hz resolution.
    """
    # Zero-pad if audio is shorter than n_fft
    if len(audio) < n_fft:
        audio = np.pad(audio, (0, n_fft - len(audio)), mode="constant")

    # Apply Hann window to reduce spectral leakage
    window = np.hanning(n_fft)
    windowed = audio[:n_fft] * window

    # Compute magnitude spectrum
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

    # Restrict search to [low_hz, high_hz] band
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(mask):
        return 0.0

    masked_spectrum = spectrum[mask]
    masked_freqs = freqs[mask]

    # Parabolic interpolation around the peak for sub-bin accuracy
    peak_idx = np.argmax(masked_spectrum)
    if 0 < peak_idx < len(masked_spectrum) - 1:
        alpha = masked_spectrum[peak_idx - 1]
        beta  = masked_spectrum[peak_idx]
        gamma = masked_spectrum[peak_idx + 1]
        # Parabolic interpolation offset
        if (alpha - 2 * beta + gamma) != 0:
            p = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma)
        else:
            p = 0.0
        freq_resolution = masked_freqs[1] - masked_freqs[0] if len(masked_freqs) > 1 else sr / n_fft
        return float(masked_freqs[peak_idx] + p * freq_resolution)
    else:
        return float(masked_freqs[peak_idx])


def frequency_track(audio: np.ndarray, sr: int,
                    frame_length_s: float = 0.1,
                    hop_length_s: float = 0.05,
                    low_hz: float = 20.0,
                    high_hz: float = 20000.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Track the dominant frequency over time using overlapping frames.

    Returns
    -------
    (times, frequencies) – 1-D arrays of frame centre times (s) and
    corresponding dominant frequencies (Hz).

    LOGIC NOTE:
        This is the backbone for Doppler velocity estimation.  Each frame
        gives one frequency sample.  The velocity is computed from the
        derivative of this frequency track.
    """
    frame_samples = int(frame_length_s * sr)
    hop_samples   = int(hop_length_s * sr)
    n_frames = max(1, (len(audio) - frame_samples) // hop_samples + 1)

    times = np.zeros(n_frames)
    freqs = np.zeros(n_frames)

    for i in range(n_frames):
        start = i * hop_samples
        end   = start + frame_samples
        frame = audio[start:end]
        times[i] = (start + end) / 2.0 / sr
        freqs[i] = dominant_frequency(frame, sr, n_fft=frame_samples,
                                       low_hz=low_hz, high_hz=high_hz)

    return times, freqs


# ────────────────────────────────────────────────────────────────
#  Doppler velocity estimation
# ────────────────────────────────────────────────────────────────

def calculate_velocity(
    chunk1: np.ndarray,
    chunk2: np.ndarray,
    sample_rate: int,
    source_frequency: Optional[float] = None,
    speed_of_sound: float = 343.0,
) -> Dict[str, float]:
    """
    Calculate object velocity from two consecutive audio chunks using
    FFT-based Doppler shift.

    Parameters
    ----------
    chunk1, chunk2 : 1-D arrays – consecutive audio recordings.
    sample_rate : int
    source_frequency : float or None
        Known emission frequency.  If None, estimated from chunk1.
    speed_of_sound : float – m/s (343 for air, ~1500 for water).

    Returns
    -------
    dict with:
        f1, f2      – dominant frequencies in each chunk (Hz)
        delta_f     – frequency shift (Hz)
        velocity    – estimated velocity (m/s, positive = approaching)
        direction   – "approaching" | "receding" | "stationary"

    LOGIC FIX vs original:
        The original used cross-correlation delay ÷ chunk length, which
        gives a *time delay*, not a frequency shift.  That formula is
        correct for TDOA-based DOA, but NOT for Doppler velocity.
    """
    f1 = dominant_frequency(chunk1, sample_rate)
    f2 = dominant_frequency(chunk2, sample_rate)

    # Use chunk1's frequency as the reference if source_frequency unknown
    if source_frequency is None:
        source_frequency = f1 if f1 > 0 else 1.0
        logger.info("source_frequency not provided, using f1=%.1f Hz", source_frequency)

    delta_f = f2 - f1

    # Doppler equation rearranged:
    #   v = speed_of_sound × (Δf / f_observed)
    # LOGIC NOTE:
    #   Positive Δf means frequency increased → source approaching.
    #   Negative Δf means frequency decreased → source receding.
    if f2 > 0:
        velocity = speed_of_sound * delta_f / f2
    else:
        velocity = 0.0

    # Direction classification with a tolerance band
    tolerance_hz = 2.0  # ±2 Hz is within measurement noise
    if abs(delta_f) < tolerance_hz:
        direction = "stationary"
    elif delta_f > 0:
        direction = "approaching"
    else:
        direction = "receding"

    return {
        "f1_hz": float(f1),
        "f2_hz": float(f2),
        "delta_f_hz": float(delta_f),
        "velocity_m_s": float(velocity),
        "direction": direction,
        "source_frequency_hz": float(source_frequency),
        "speed_of_sound_m_s": float(speed_of_sound),
    }


def full_doppler_analysis(
    audio: np.ndarray,
    sr: int,
    source_frequency: Optional[float] = None,
    speed_of_sound: float = 343.0,
    frame_length_s: float = 0.1,
    hop_length_s: float = 0.05,
    distance_m: Optional[float] = None,
) -> Dict:
    """
    Full Doppler analysis over an entire recording – produces visualisation
    data for the frontend.

    Parameters
    ----------
    audio : 1-D array
    sr : int
    source_frequency : float or None
    speed_of_sound : float
    frame_length_s, hop_length_s : float – frame parameters
    distance_m : float or None – if given, compute travel time at each
                 velocity estimate.

    Returns
    -------
    dict with:
        times         – list of frame centre times (s)
        frequencies   – list of dominant frequencies per frame (Hz)
        velocities    – list of velocity estimates per frame (m/s)
        directions    – list of "approaching" / "receding" / "stationary"
        travel_times  – list of estimated travel times (s) at each velocity
                        (None if distance_m not provided)
        summary       – dict with aggregate statistics

    LOGIC NOTE on travel time:
        travel_time = distance / |velocity|.
        This tells the user: "an object moving at this speed would
        traverse ``distance_m`` metres in ``travel_time`` seconds."
        This is a forward estimate, not a prediction – it shows the
        user what the current speed implies spatially.
    """
    times, freqs = frequency_track(audio, sr, frame_length_s, hop_length_s)

    # Use first frame as reference if source frequency unknown
    if source_frequency is None and len(freqs) > 0 and freqs[0] > 0:
        source_frequency = freqs[0]
    elif source_frequency is None:
        source_frequency = 1000.0  # fallback

    velocities = []
    directions = []
    travel_times = []

    tolerance_hz = 2.0

    for i in range(len(freqs)):
        delta_f = freqs[i] - source_frequency
        if freqs[i] > 0:
            v = speed_of_sound * delta_f / freqs[i]
        else:
            v = 0.0
        velocities.append(v)

        if abs(delta_f) < tolerance_hz:
            directions.append("stationary")
        elif delta_f > 0:
            directions.append("approaching")
        else:
            directions.append("receding")

        if distance_m is not None and abs(v) > 0.1:
            travel_times.append(distance_m / abs(v))
        else:
            travel_times.append(None)

    # Summary statistics
    vel_array = np.array(velocities)
    summary = {
        "mean_velocity_m_s": float(np.mean(vel_array)),
        "max_velocity_m_s": float(np.max(np.abs(vel_array))),
        "dominant_direction": max(set(directions), key=directions.count),
        "n_frames": len(times),
        "duration_s": float(len(audio) / sr),
    }
    if distance_m is not None:
        valid_tt = [t for t in travel_times if t is not None]
        if valid_tt:
            summary["mean_travel_time_s"] = float(np.mean(valid_tt))

    return {
        "times": times.tolist(),
        "frequencies": [float(f) for f in freqs],
        "velocities": [float(v) for v in velocities],
        "directions": directions,
        "travel_times": travel_times,
        "summary": summary,
    }


if __name__ == "__main__":
    # ── Synthetic test ──
    sr = 16000
    duration = 2.0
    t = np.arange(int(sr * duration)) / sr

    # Simulate a source approaching then receding (chirp)
    f0 = 1000.0
    freq_profile = f0 + 50 * np.sin(2 * np.pi * 0.5 * t)  # ±50 Hz swing
    phase = 2 * np.pi * np.cumsum(freq_profile) / sr
    audio = np.sin(phase).astype(np.float32)

    result = full_doppler_analysis(audio, sr, source_frequency=f0,
                                    distance_m=100.0)
    s = result["summary"]
    print(f"Duration: {s['duration_s']:.1f}s  "
          f"Max velocity: {s['max_velocity_m_s']:.1f} m/s  "
          f"Direction: {s['dominant_direction']}")
    print(f"Frames: {s['n_frames']}")
