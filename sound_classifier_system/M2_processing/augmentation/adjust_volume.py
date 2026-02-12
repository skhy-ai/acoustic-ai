"""
Volume Adjustment Augmentation
================================
Purpose:
    Create louder and quieter variants of audio files to make the ML
    model robust to recording-level differences.  In real-world
    deployment, the same sound source may be captured at vastly
    different volumes depending on:
        • Distance from sensor to source
        • Sensor gain settings
        • Environmental attenuation (wind, walls, water)

Workflow position:
    This is a standalone augmentation script.  For new pipelines, prefer
    ``filtering_augmentation.py`` which includes volume scaling as part
    of a unified class-balanced augmentation workflow.

LOGIC NOTES:
    • pydub's ``+= dB`` adjusts amplitude linearly:
        adjusted = audio × 10^(dB/20)
      So +10 dB ≈ ×3.16, -10 dB ≈ ×0.316.
    • Increasing volume beyond 0 dBFS causes clipping.  We do NOT clip
      here because the training pipeline should learn to handle
      near-clipped signals.  If you want clean signals, set max_db to
      a conservative value (e.g. +3 dB).
"""

import os
import logging
from typing import List, Optional

from pydub import AudioSegment

logger = logging.getLogger(__name__)


def adjust_volume(
    audio_path: str,
    output_prefix: str,
    decibel_change: float,
) -> str:
    """
    Create a volume-adjusted copy of a single audio file.

    Returns the output file path.
    """
    audio = AudioSegment.from_file(audio_path)
    adjusted = audio + decibel_change
    output_path = f"{output_prefix}_{decibel_change:+.0f}dB.mp3"
    adjusted.export(output_path, format="mp3")
    return output_path


def process_all_files(
    input_folder: str,
    output_folder: str,
    decibel_changes: Optional[List[float]] = None,
):
    """
    Batch processing: create volume-adjusted variants for all audio
    files in ``input_folder``.

    LOGIC NOTE:
        Each dB value is applied independently to each file, so
        N files × M dB values = N×M output files.
    """
    if decibel_changes is None:
        decibel_changes = [+10, +20, -10, -20]

    os.makedirs(output_folder, exist_ok=True)

    for fname in os.listdir(input_folder):
        if fname.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
            fpath = os.path.join(input_folder, fname)
            base = os.path.splitext(fname)[0]
            for db in decibel_changes:
                prefix = os.path.join(output_folder, base)
                adjust_volume(fpath, prefix, db)
            logger.info("Processed: %s (%d variants)", fname, len(decibel_changes))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s  %(message)s")
    input_folder = "../sound_data/filtered"
    output_folder = "../sound_data/volume_adjusted"
    os.makedirs(output_folder, exist_ok=True)
    process_all_files(input_folder, output_folder)
