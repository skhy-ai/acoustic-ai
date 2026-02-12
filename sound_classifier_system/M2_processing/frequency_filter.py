"""
Hybrid Frequency-Band Pre-Classifier
=======================================
Purpose:
    Before running a full ML classifier, we can make a *first-guess*
    at what kind of sound we're hearing by checking which frequency
    bands contain most of the energy.  Different sound sources have
    characteristic spectral signatures:

    ┌─────────────────────┬───────────────────┬──────────────────────────┐
    │ Sound Source         │ Dominant Band     │ Notes                    │
    ├─────────────────────┼───────────────────┼──────────────────────────┤
    │ Drone (multi-rotor) │   80 – 500 Hz     │ Motor hum + blade pass   │
    │ Fixed-wing aircraft │  100 – 2000 Hz    │ Engine + aero noise      │
    │ Helicopter          │   20 – 300 Hz     │ Low-frequency blade thump│
    │ Car / truck         │   50 – 1000 Hz    │ Engine + tyre noise      │
    │ Gunshot / explosion │ 500 – 8000 Hz     │ Broadband impulsive      │
    │ Siren / alarm       │ 500 – 4000 Hz     │ Tonal harmonics          │
    │ Human voice         │  80 – 3500 Hz     │ Formants                 │
    │ Bird / insect       │ 1000 – 10000 Hz   │ High-pitched chirps      │
    │ Marine vessel       │   10 – 500 Hz     │ Engine + cavitation      │
    │ Marine mammal       │  200 – 15000 Hz   │ Clicks and whistles      │
    └─────────────────────┴───────────────────┴──────────────────────────┘

How Doppler fits in:
    If we detect a frequency *shift* over time (via the Doppler module),
    the sound is likely from a *moving* source.  We combine:
        1. Frequency-band energy → candidate source type
        2. Doppler shift → moving vs stationary, velocity estimate
    This gives a **fast first-pass** classification that can run in
    real-time on each incoming audio chunk, before the heavier ML
    model produces its prediction.

Architecture:
    ┌───────────────────────────────────────────────────────────────┐
    │  Raw Audio Chunk                                              │
    │      │                                                        │
    │      ├──→ frequency_band_energy()   → energy per band         │
    │      │                                                        │
    │      ├──→ doppler.frequency_track() → freq shift / velocity   │
    │      │                                                        │
    │      └──→ hybrid_classify()                                   │
    │                │                                              │
    │                ├── first_guess_class  (from frequency bands)   │
    │                ├── is_moving          (from Doppler)           │
    │                ├── velocity           (from Doppler)           │
    │                └── confidence         (band energy ratio)      │
    └───────────────────────────────────────────────────────────────┘

LOGIC NOTES:
    • This is NOT a replacement for the ML classifier.  It runs alongside
      it as a fast heuristic.  When both agree, confidence is high.
      When they disagree, the ML result is preferred but the hybrid
      result is shown as context.
    • The frequency bands can be customised per deployment.  Underwater
      hydrophone deployments would use different bands than aerial ones.
    • The Doppler velocity is only meaningful for *sustained* sounds
      (drones, vehicles).  Impulsive sounds (gunshots) don't produce
      a useful Doppler shift and are instead identified by their
      broadband energy profile.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────
#  Frequency band definitions
# ────────────────────────────────────────────────────────────────

@dataclass
class FrequencyBand:
    """
    A named frequency range with associated candidate sound sources.
    """
    name: str
    low_hz: float
    high_hz: float
    candidate_sources: List[str] = field(default_factory=list)


# Default band definitions – customisable per deployment
DEFAULT_BANDS = [
    FrequencyBand("sub_bass",      10,    80, ["helicopter", "marine_vessel", "earthquake"]),
    FrequencyBand("bass",          80,   300, ["drone", "car_truck", "helicopter", "marine_vessel"]),
    FrequencyBand("low_mid",      300,  1000, ["drone", "car_truck", "fixed_wing", "human_voice"]),
    FrequencyBand("mid",         1000,  3500, ["siren", "human_voice", "fixed_wing", "bird"]),
    FrequencyBand("upper_mid",   3500,  8000, ["gunshot", "siren", "bird", "insect"]),
    FrequencyBand("high",        8000, 16000, ["bird", "insect", "marine_mammal"]),
]


# ────────────────────────────────────────────────────────────────
#  Energy computation
# ────────────────────────────────────────────────────────────────

def frequency_band_energy(
    audio: np.ndarray,
    sr: int,
    bands: Optional[List[FrequencyBand]] = None,
    n_fft: int = 4096,
) -> List[Dict]:
    """
    Compute normalised energy in each frequency band.

    Returns a list of dicts, one per band:
        { "name": str, "low_hz": float, "high_hz": float,
          "energy": float (0–1 normalised),
          "energy_db": float,
          "candidate_sources": [...] }

    LOGIC NOTE:
        Energy is normalised so that the sum across all bands = 1.0.
        This makes it comparable across recordings of different volumes.
        The raw dBFS energy is also provided for absolute reference.
    """
    if bands is None:
        bands = DEFAULT_BANDS

    # Compute power spectrum
    if len(audio) < n_fft:
        audio = np.pad(audio, (0, n_fft - len(audio)))

    window = np.hanning(n_fft)
    windowed = audio[:n_fft] * window
    spectrum = np.abs(np.fft.rfft(windowed)) ** 2
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

    results = []
    total_energy = 0.0

    for band in bands:
        mask = (freqs >= band.low_hz) & (freqs < band.high_hz)
        band_energy = float(np.sum(spectrum[mask])) if np.any(mask) else 0.0
        total_energy += band_energy
        results.append({
            "name": band.name,
            "low_hz": band.low_hz,
            "high_hz": band.high_hz,
            "energy_raw": band_energy,
            "candidate_sources": band.candidate_sources,
        })

    # Normalise + dBFS
    for r in results:
        r["energy"] = r["energy_raw"] / total_energy if total_energy > 0 else 0.0
        r["energy_db"] = float(10 * np.log10(r["energy_raw"] + 1e-10))
        del r["energy_raw"]  # don't expose unnormalised value

    return results


# ────────────────────────────────────────────────────────────────
#  Hybrid classification
# ────────────────────────────────────────────────────────────────

def hybrid_classify(
    audio: np.ndarray,
    sr: int,
    bands: Optional[List[FrequencyBand]] = None,
    doppler_result: Optional[Dict] = None,
    top_k: int = 3,
) -> Dict:
    """
    Produce a first-guess classification by combining frequency-band
    energy analysis with optional Doppler information.

    Parameters
    ----------
    audio : 1-D array
    sr : int
    bands : list of FrequencyBand (or None for defaults)
    doppler_result : dict or None
        Output of ``doppler.calculate_velocity()`` or
        ``doppler.full_doppler_analysis().summary``.  If provided,
        adds velocity and motion direction context.
    top_k : int
        Number of candidate classes to return.

    Returns
    -------
    dict with:
        first_guess     – most likely class name
        candidates      – list of top_k (class, confidence) tuples
        band_energies   – full band energy breakdown
        is_moving       – bool (from Doppler, or None)
        velocity_m_s    – float (from Doppler, or None)
        direction       – str (from Doppler, or None)
        method          – "frequency_band" or "frequency_band+doppler"

    LOGIC NOTE on confidence:
        Confidence here is the fraction of total energy in the dominant
        band, weighted by how many candidate sources that band suggests.
        It's NOT a probability – it's a heuristic score between 0 and 1.
    """
    band_energies = frequency_band_energy(audio, sr, bands)

    # Score each candidate source by accumulating band energies
    # where it appears as a candidate
    source_scores: Dict[str, float] = {}
    for be in band_energies:
        energy = be["energy"]
        for src in be["candidate_sources"]:
            # Weight by energy – a source in a high-energy band gets
            # a higher score than one in a low-energy band.
            source_scores[src] = source_scores.get(src, 0.0) + energy

    # Normalise scores to 0–1
    max_score = max(source_scores.values()) if source_scores else 1.0
    if max_score > 0:
        for k in source_scores:
            source_scores[k] /= max_score

    # Sort by descending score
    ranked = sorted(source_scores.items(), key=lambda x: x[1], reverse=True)
    top = ranked[:top_k] if ranked else [("unknown", 0.0)]

    result = {
        "first_guess": top[0][0],
        "candidates": [{"class": cls, "confidence": round(conf, 3)}
                        for cls, conf in top],
        "band_energies": band_energies,
        "is_moving": None,
        "velocity_m_s": None,
        "direction": None,
        "method": "frequency_band",
    }

    # Merge Doppler context if available
    if doppler_result is not None:
        result["is_moving"] = doppler_result.get("direction") != "stationary"
        result["velocity_m_s"] = doppler_result.get("velocity_m_s",
                                                      doppler_result.get("mean_velocity_m_s"))
        result["direction"] = doppler_result.get("direction",
                                                   doppler_result.get("dominant_direction"))
        result["method"] = "frequency_band+doppler"

        # Boost moving-source candidates if Doppler confirms motion
        # LOGIC NOTE: If Doppler says the source is approaching fast,
        # stationary sources (e.g. "earthquake") should be penalised.
        if result["is_moving"]:
            moving_sources = {"drone", "car_truck", "fixed_wing",
                              "helicopter", "marine_vessel"}
            for c in result["candidates"]:
                if c["class"] in moving_sources:
                    c["confidence"] = min(1.0, c["confidence"] * 1.3)
                else:
                    c["confidence"] *= 0.7

            # Re-sort after adjustment
            result["candidates"].sort(key=lambda x: x["confidence"],
                                       reverse=True)
            result["first_guess"] = result["candidates"][0]["class"]

    return result


# ────────────────────────────────────────────────────────────────
#  Convenience: analyse an entire file
# ────────────────────────────────────────────────────────────────

def analyse_file(
    file_path: str,
    sr: Optional[int] = None,
    speed_of_sound: float = 343.0,
    distance_m: Optional[float] = None,
) -> Dict:
    """
    Full analysis of an audio file: frequency bands + Doppler + hybrid
    classification.  Returns a combined dict suitable for JSON response.
    """
    import librosa
    from ..doppler.doppler import full_doppler_analysis

    audio, sr = librosa.load(file_path, sr=sr)

    doppler = full_doppler_analysis(audio, sr, speed_of_sound=speed_of_sound,
                                     distance_m=distance_m)
    hybrid = hybrid_classify(audio, sr, doppler_result=doppler["summary"])

    return {
        "hybrid_classification": hybrid,
        "doppler_analysis": doppler,
    }


if __name__ == "__main__":
    # Quick test with synthetic chirp
    sr = 16000
    t = np.arange(sr * 2) / sr
    # Simulate a 1000 Hz source approaching → dominant in low_mid band
    audio = np.sin(2 * np.pi * 1000 * t).astype(np.float32)

    result = hybrid_classify(audio, sr)
    print(f"First guess: {result['first_guess']}")
    for c in result["candidates"]:
        print(f"  {c['class']}: {c['confidence']:.3f}")
    print("\nBand energies:")
    for b in result["band_energies"]:
        bar = "█" * int(b["energy"] * 40)
        print(f"  {b['name']:>12s}  {b['energy']:.3f}  {bar}")
