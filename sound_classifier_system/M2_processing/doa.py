"""
Direction of Arrival (DOA) – GCC-PHAT
======================================
Estimates the angle of arrival of a sound source using the
Generalized Cross-Correlation with Phase Transform algorithm.

This works with any pair of microphone signals and requires:
    - The distance between the two microphones (metres)
    - The sampling frequency
    - The speed of sound (default 343 m/s for air)

For multi-channel arrays (7-MEMS, 16-MEMS) we compute pair-wise
TDOA and average the results, or use a specific pair.
"""

import numpy as np
from scipy import signal
from typing import Tuple, Optional, List


def gcc_phat(sig1: np.ndarray, sig2: np.ndarray,
             fs: int, max_tau: Optional[float] = None
             ) -> Tuple[float, np.ndarray]:
    """
    Compute GCC-PHAT between two signals.

    Parameters
    ----------
    sig1, sig2 : 1-D arrays
        Microphone signals (same length).
    fs : int
        Sampling frequency.
    max_tau : float or None
        Maximum expected delay (seconds).  Limits search window.

    Returns
    -------
    tau   : float  – estimated time delay in seconds
    cc    : 1-D array – the cross-correlation function
    """
    n = len(sig1) + len(sig2) - 1
    n_fft = 1 << int(np.ceil(np.log2(n)))  # next power of 2

    S1 = np.fft.rfft(sig1, n=n_fft)
    S2 = np.fft.rfft(sig2, n=n_fft)

    # Cross-power spectrum with PHAT weighting
    R = S1 * np.conj(S2)
    magnitude = np.abs(R)
    magnitude[magnitude < 1e-10] = 1e-10  # avoid division by zero
    R_phat = R / magnitude

    cc = np.fft.irfft(R_phat, n=n_fft)

    # Shift so that zero-lag is in the centre
    cc = np.fft.fftshift(cc)
    centre = len(cc) // 2

    # Limit search to physically plausible delays
    if max_tau is not None:
        max_shift = int(max_tau * fs)
    else:
        max_shift = centre

    search_start = max(centre - max_shift, 0)
    search_end = min(centre + max_shift + 1, len(cc))
    search_region = cc[search_start:search_end]

    peak_idx = np.argmax(np.abs(search_region))
    tau_samples = peak_idx - (centre - search_start)
    tau = tau_samples / fs

    return tau, cc


def estimate_doa(sig1: np.ndarray, sig2: np.ndarray,
                 fs: int, mic_distance: float,
                 speed_of_sound: float = 343.0) -> float:
    """
    Estimate Direction of Arrival in degrees.

    Parameters
    ----------
    sig1, sig2 : 1-D arrays
    fs : int
    mic_distance : float
        Distance between the two microphones (metres).
    speed_of_sound : float

    Returns
    -------
    angle : float – in degrees, 0° = broadside, ±90° = endfire
    """
    max_tau = mic_distance / speed_of_sound
    tau, _ = gcc_phat(sig1, sig2, fs, max_tau=max_tau)

    # Clamp to avoid arcsin domain error
    arg = (speed_of_sound * tau) / mic_distance
    arg = np.clip(arg, -1.0, 1.0)

    angle_rad = np.arcsin(arg)
    return float(np.degrees(angle_rad))


def estimate_doa_array(multi_channel: np.ndarray,
                       fs: int,
                       mic_positions: np.ndarray,
                       speed_of_sound: float = 343.0,
                       ref_channel: int = 0) -> List[dict]:
    """
    Estimate DOA from a multi-channel recording using pair-wise
    GCC-PHAT against a reference channel.

    Parameters
    ----------
    multi_channel : (N, C) array
    fs : int
    mic_positions : (C, 2) or (C, 3) array of microphone coordinates (metres).
    speed_of_sound : float
    ref_channel : int – index of the reference mic.

    Returns
    -------
    List of dicts with 'pair', 'tdoa', 'angle' for each pair.
    """
    n_channels = multi_channel.shape[1]
    ref_sig = multi_channel[:, ref_channel]
    results = []

    for ch in range(n_channels):
        if ch == ref_channel:
            continue
        sig = multi_channel[:, ch]
        dist = np.linalg.norm(mic_positions[ch] - mic_positions[ref_channel])
        if dist < 1e-6:
            continue

        max_tau = dist / speed_of_sound
        tau, _ = gcc_phat(ref_sig, sig, fs, max_tau=max_tau)
        arg = np.clip((speed_of_sound * tau) / dist, -1.0, 1.0)
        angle = float(np.degrees(np.arcsin(arg)))

        results.append({
            "pair": (ref_channel, ch),
            "distance_m": float(dist),
            "tdoa_s": float(tau),
            "angle_deg": angle,
        })

    return results


if __name__ == "__main__":
    # Quick test with synthetic data
    fs = 16000
    t = np.arange(fs) / fs
    src = np.sin(2 * np.pi * 1000 * t)

    delay_samples = 5
    sig1 = src.copy()
    sig2 = np.roll(src, delay_samples)

    tau, _ = gcc_phat(sig1, sig2, fs)
    print(f"Estimated delay: {tau*1000:.3f} ms "
          f"(expected: {delay_samples/fs*1000:.3f} ms)")

    angle = estimate_doa(sig1, sig2, fs, mic_distance=0.05)
    print(f"Estimated DOA: {angle:.1f}°")
