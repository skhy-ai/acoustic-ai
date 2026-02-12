"""
Reverse Audio Augmentation
============================
Purpose:
    Create time-reversed copies of audio files.  This augmentation
    helps the model learn features that are time-invariant (e.g. spectral
    shape, frequency content) rather than relying on temporal order.

When this is useful:
    • Sounds with symmetric temporal profiles (e.g. engine hum, fan noise)
      sound similar reversed → model learns this invariance.
    • Sounds with asymmetric profiles (e.g. gunshot – sharp attack, long
      decay) sound very different reversed → model learns to distinguish
      temporal structure.
    • Either way, the model gains more diverse training data.

When this is NOT useful:
    • Speech recognition – reversed speech is meaningless.
    • Music classification – reversed music has different structure.
    • In general, avoid for tasks where temporal order carries class info.

Workflow position:
    Standalone script.  For integrated augmentation, use
    ``filtering_augmentation.py``.

LOGIC NOTE:
    pydub's ``.reverse()`` simply reverses the sample array.  This is
    a lossless operation (no quality degradation).  The output retains
    the same sample rate, bit depth, and channel count.
"""

import os
import logging
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def reverse_audio(audio_path: str, output_path: str) -> str:
    """
    Create a time-reversed copy of an audio file.

    Returns the output path.
    """
    audio = AudioSegment.from_file(audio_path)
    reversed_audio = audio.reverse()
    reversed_audio.export(output_path, format="mp3")
    return output_path


def process_all_files(input_folder: str, output_folder: str):
    """
    Batch reverse all audio files in ``input_folder``.
    """
    os.makedirs(output_folder, exist_ok=True)

    for fname in os.listdir(input_folder):
        if fname.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
            fpath = os.path.join(input_folder, fname)
            base = os.path.splitext(fname)[0]
            out_fname = f"{base}_reversed.mp3"
            out_path = os.path.join(output_folder, out_fname)

            if os.path.exists(out_path):
                continue  # idempotent

            reverse_audio(fpath, out_path)
            logger.debug("Reversed: %s", fname)

    logger.info("Reverse augmentation complete for %s", input_folder)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s  %(message)s")
    input_folder = "../sound_data/filtered"
    output_folder = "../sound_data/filtered_reverse"
    os.makedirs(output_folder, exist_ok=True)
    process_all_files(input_folder, output_folder)