"""
Organize Sound Samples into Train / Validation / Test Splits
==============================================================
Purpose:
    After ``sampled_data/<class>/`` has been populated (by either
    ``metadata_based_class_creation.py`` or ``rename_class.py``),
    this module splits the data into train / validation / test sets
    while preserving class balance.

Workflow position:
    sampled_data/<class>/                      ← flat per-class dirs
          │
          ▼  (optionally via filtering_augmentation.py)
          │
    **organize_sound_samples.py**
          │
          ▼
    sound_dataset/
        ├── train/<class>/
        ├── validation/<class>/
        └── test/<class>/

    After this step, ``feature_extraction.py`` can be run on each
    split independently.

LOGIC NOTES:
    • We use scikit-learn's ``train_test_split`` with stratification
      to ensure every class appears in every split.
    • Default split ratios: 70 % train, 15 % validation, 15 % test.
    • Files are **copied** (not moved) so the original ``sampled_data/``
      remains intact for re-splitting with different ratios.
    • Random seed is fixed (42) for reproducibility.
    • Classes with fewer than ~7 files may fail stratification.  We
      fall back to a simple sequential split in that case.
"""

import os
import shutil
import logging
from typing import Optional

from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


def organize_samples(
    input_dir: str,
    output_dir: str,
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42,
):
    """
    Split audio files from ``input_dir/<class>/`` into train / validation
    / test sets under ``output_dir/<split>/<class>/``.

    Parameters
    ----------
    input_dir : str  – e.g. ``../../sampled_data``
    output_dir : str – e.g. ``../../sound_dataset``
    test_size : float – fraction reserved for testing (0–1)
    val_size : float  – fraction reserved for validation (0–1)
    random_state : int – for reproducibility

    LOGIC NOTE on split order:
        We first split into train+val vs test, then split train+val
        into train vs val.  The second split must adjust its ratio:
            val_ratio_within_trainval = val_size / (1 - test_size)
        So for test_size=0.15, val_size=0.15:
            first split:  85 % trainval, 15 % test
            second split: val_ratio = 0.15 / 0.85 ≈ 0.176
            result:       ~70 % train, ~15 % val, ~15 % test  ✓
    """
    # Create split directories
    for split in ["train", "validation", "test"]:
        os.makedirs(os.path.join(output_dir, split), exist_ok=True)

    total_copied = 0

    for class_name in sorted(os.listdir(input_dir)):
        class_dir = os.path.join(input_dir, class_name)
        if not os.path.isdir(class_dir):
            continue

        # Collect audio files (case-insensitive extension matching)
        audio_files = [
            f for f in os.listdir(class_dir)
            if f.lower().endswith((".wav", ".mp3", ".flac", ".ogg"))
        ]

        if not audio_files:
            logger.warning("Skipping empty class: %s", class_name)
            continue

        # Minimum samples needed for stratified split is ~2 per split
        # With 3 splits, we need at least 6 files.  If fewer, fall
        # back to a simple serial assignment.
        if len(audio_files) < 6:
            logger.warning(
                "Class '%s' has only %d files – using sequential split "
                "instead of stratified random",
                class_name, len(audio_files),
            )
            # Assign 1 to test, 1 to val, rest to train
            test_files = audio_files[:1]
            val_files  = audio_files[1:2]
            train_files = audio_files[2:]
        else:
            # Two-stage stratified split
            combined_hold = test_size + val_size
            train_files, holdout = train_test_split(
                audio_files,
                test_size=combined_hold,
                random_state=random_state,
            )
            # Split holdout into val and test
            val_ratio = val_size / combined_hold
            val_files, test_files = train_test_split(
                holdout,
                test_size=(1 - val_ratio),
                random_state=random_state,
            )

        # Copy files into split directories
        for split_name, files in [
            ("train", train_files),
            ("validation", val_files),
            ("test", test_files),
        ]:
            split_class_dir = os.path.join(output_dir, split_name, class_name)
            os.makedirs(split_class_dir, exist_ok=True)
            for fname in files:
                src = os.path.join(class_dir, fname)
                dst = os.path.join(split_class_dir, fname)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    total_copied += 1

        logger.info(
            "%-20s  train=%d  val=%d  test=%d",
            class_name, len(train_files), len(val_files), len(test_files),
        )

    logger.info("Dataset organization complete! %d files copied.", total_copied)
    print("Dataset organization complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s  %(message)s")
    input_directory = "../../sampled_data"
    output_directory = "../../sound_dataset"
    organize_samples(input_directory, output_directory)
