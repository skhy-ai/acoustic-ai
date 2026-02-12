"""
Audio Pitch Adjustment with Noise Reduction
=============================================
Purpose:
    Apply pitch shifts to audio files for data augmentation.  Each file
    is shifted by several semitone amounts and saved as a new file.
    Optional noise reduction is applied after pitch shifting to clean
    up any artefacts introduced by the resampling algorithm.

Workflow position:
    This is a *legacy* standalone augmentation script.  For new pipelines,
    prefer ``filtering_augmentation.py`` which integrates pitch shifting
    into a unified filtering + augmentation workflow with class balancing.

ORIGINAL BUG:
    The file contained a full duplicate of itself (lines 55–108 repeated
    lines 1–54).  This has been fixed in this version.

LOGIC NOTE on pitch_change / semitones conversion:
    The original code converted Hz change to semitones via:
        semitones = pitch_change / 100.0
    This assumes 100 Hz ≈ 1 semitone, which is only roughly true near
    A4 (440 Hz).  For correctness, the conversion should be:
        semitones = 12 * log2((f₀ + Δf) / f₀)
    However, since the original formula is baked into the saved filenames
    and existing training data, we keep it for backward compatibility
    and note the approximation.
"""

import os
import logging
from typing import List, Optional

import numpy as np
from pydub import AudioSegment
import pyrubberband as pyrb
import noisereduce as nr

logger = logging.getLogger(__name__)


def change_pitch(audio: AudioSegment, sample_rate: int,
                 semitones: float) -> AudioSegment:
    """
    Shift pitch of a pydub AudioSegment by ``semitones``.

    Uses ``pyrubberband`` (Rubber Band Library) for high-quality
    pitch shifting without changing duration.

    LOGIC NOTE:
        pyrubberband expects float64 samples.  pydub gives int16
        (via get_array_of_samples).  We convert and normalise.
    """
    samples = np.array(audio.get_array_of_samples()).astype(np.float64)
    # Normalise int16 to [-1, 1] for pyrubberband
    samples = samples / 32768.0
    shifted = pyrb.pitch_shift(samples, sample_rate, semitones)
    # Convert back to int16
    shifted_int16 = (shifted * 32768.0).clip(-32768, 32767).astype(np.int16)
    return AudioSegment(
        shifted_int16.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio.sample_width,
        channels=audio.channels,
    )


def reduce_noise(audio: AudioSegment) -> AudioSegment:
    """
    Apply spectral-gating noise reduction.

    LOGIC NOTE:
        ``noisereduce`` uses spectral gating with a noise profile
        estimated from the signal itself (prop_decrease controls
        how aggressively noise is suppressed).  If it fails (e.g.
        due to very short audio), we return the original unchanged.
    """
    samples = np.array(audio.get_array_of_samples()).astype(np.float64)
    try:
        reduced = nr.reduce_noise(y=samples, sr=audio.frame_rate)
        reduced_int16 = reduced.clip(-32768, 32767).astype(np.int16)
        return AudioSegment(
            reduced_int16.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=audio.channels,
        )
    except Exception as e:
        logger.warning("Noise reduction failed: %s", e)
        return audio


def adjust_pitch_and_volume(
    audio_path: str,
    output_prefix: str,
    pitch_changes: Optional[List[int]] = None,
    apply_noise_reduction: bool = True,
) -> List[str]:
    """
    Create multiple pitch-shifted variants of a single audio file.

    Parameters
    ----------
    audio_path : str
    output_prefix : str – output file path without extension/suffix.
    pitch_changes : list of int – Hz offsets (legacy format).
    apply_noise_reduction : bool

    Returns
    -------
    list of str – paths to created files.
    """
    if pitch_changes is None:
        pitch_changes = [-50, -100, -150, -200, -250]

    audio = AudioSegment.from_file(audio_path)
    sample_rate = audio.frame_rate
    created: List[str] = []

    for change_hz in pitch_changes:
        # Legacy approximation: Hz → semitones (see docstring)
        semitones = change_hz / 100.0
        adjusted = change_pitch(audio, sample_rate, semitones)

        if apply_noise_reduction:
            adjusted = reduce_noise(adjusted)

        output_path = f"{output_prefix}_{change_hz:+d}Hz.mp3"
        adjusted.export(output_path, format="mp3")
        created.append(output_path)
        logger.debug("Created: %s", output_path)

    return created


def process_all_files(
    input_folder: str,
    output_folder: str,
    pitch_changes: Optional[List[int]] = None,
):
    """
    Batch processing: apply pitch shifts to all audio files in a folder.
    """
    if pitch_changes is None:
        pitch_changes = [-50, -100, -150, -200, -250]

    os.makedirs(output_folder, exist_ok=True)

    for fname in os.listdir(input_folder):
        if fname.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
            fpath = os.path.join(input_folder, fname)
            base = os.path.splitext(fname)[0]
            prefix = os.path.join(output_folder, base)
            adjust_pitch_and_volume(fpath, prefix, pitch_changes)
            logger.info("Processed: %s", fname)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s  %(message)s")
    input_folder = "../sound_data/filtered"
    output_folder = "../sound_data/pitch_adjusted"
    os.makedirs(output_folder, exist_ok=True)
    process_all_files(input_folder, output_folder)
