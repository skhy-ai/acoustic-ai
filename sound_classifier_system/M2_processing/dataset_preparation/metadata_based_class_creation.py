"""
Metadata-Based Class Creation
===============================
Purpose:
    When external datasets (e.g. UrbanSound8K, ESC-50) are downloaded into
    ``external_sound_data/``, their folder structure and naming conventions
    differ from our canonical format.  This module *homogenises* the data by
    reading a CSV metadata file that maps each audio file to a class label
    and copying the files into ``sampled_data/<class_name>/``.

Workflow position:
    M1_acquisitions  →  external_sound_data/
                             │
                             ▼
                    **metadata_based_class_creation.py**
                             │
                             ▼
                        sampled_data/<class>/
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
           organize_sound_samples  filtering_augmentation
           (train/val/test split)  (SNR filter, augment)

Logic notes:
    • UrbanSound8K puts audio in ``fold1/``, ``fold2/``, … sub-directories
      with a ``UrbanSound8K.csv`` metadata file whose columns include
      ``slice_file_name`` and ``class``.
    • ESC-50 uses ``meta/esc50.csv`` with ``filename`` and ``category``.
    • This script auto-detects the column names and adapts.
    • Files that already exist in the target directory are skipped to
      allow incremental runs.
    • The function is also importable from the API layer so the Electron
      UI can trigger homogenisation without a terminal.
"""

import os
import shutil
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
#  Column-name detection heuristics
# ────────────────────────────────────────────────────────────────
#  Different datasets use different column names.  We maintain a
#  priority-ordered list for each concept and pick the first match.

_FILE_COLUMN_CANDIDATES  = ["slice_file_name", "filename", "fname", "file", "audio_filename"]
_CLASS_COLUMN_CANDIDATES = ["class", "category", "label", "classID", "class_name", "target"]


def _detect_columns(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Auto-detect which CSV columns correspond to *file name* and *class label*.

    Returns (file_col, class_col).
    Raises ValueError when no match is found.
    """
    file_col = None
    for candidate in _FILE_COLUMN_CANDIDATES:
        if candidate in df.columns:
            file_col = candidate
            break
    class_col = None
    for candidate in _CLASS_COLUMN_CANDIDATES:
        if candidate in df.columns:
            class_col = candidate
            break

    if file_col is None:
        raise ValueError(
            f"Cannot detect file-name column.  Columns present: {list(df.columns)}.  "
            f"Expected one of: {_FILE_COLUMN_CANDIDATES}"
        )
    if class_col is None:
        raise ValueError(
            f"Cannot detect class column.  Columns present: {list(df.columns)}.  "
            f"Expected one of: {_CLASS_COLUMN_CANDIDATES}"
        )

    logger.info("Detected columns: file=%s  class=%s", file_col, class_col)
    return file_col, class_col


# ────────────────────────────────────────────────────────────────
#  Core helpers
# ────────────────────────────────────────────────────────────────

def find_audio_files(base_path: str,
                     extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Recursively walk ``base_path`` and return a dict mapping
    ``{basename: full_path}`` for every audio file found.

    Parameters
    ----------
    base_path : str
        Root directory to search.
    extensions : list of str, optional
        File extensions to include (with leading dot, e.g. ``['.wav', '.mp3']``).
        Defaults to ``['.wav', '.mp3', '.flac', '.ogg']``.

    Returns
    -------
    dict  –  ``{filename: absolute_path}``

    BUG-FIX NOTE:
        The original code used a flat list and matched by basename only.
        If two files in different sub-directories share the same name,
        only the *last* one found was used.  We now log a warning when
        this happens so the user can investigate.
    """
    if extensions is None:
        extensions = [".wav", ".mp3", ".flac", ".ogg"]

    file_map: Dict[str, str] = {}
    for root, _, files in os.walk(base_path):
        for f in files:
            if any(f.lower().endswith(ext) for ext in extensions):
                full = os.path.join(root, f)
                if f in file_map:
                    logger.warning(
                        "Duplicate basename '%s': keeping %s, ignoring %s",
                        f, file_map[f], full,
                    )
                else:
                    file_map[f] = full
    return file_map


def copy_files_to_class_directories(
    metadata_file: str,
    audio_files: Dict[str, str],
    output_base_path: str,
    *,
    file_col: Optional[str] = None,
    class_col: Optional[str] = None,
) -> Dict[str, int]:
    """
    Read a CSV metadata file, resolve each row's audio file via
    ``audio_files`` lookup, and copy it into ``output_base_path/<class>/``.

    Parameters
    ----------
    metadata_file : str
    audio_files : dict
        ``{basename: absolute_path}`` as returned by ``find_audio_files``.
    output_base_path : str
    file_col, class_col : str or None
        Override auto-detection of CSV column names.

    Returns
    -------
    dict  –  per-class count of files copied, e.g. ``{"siren": 42, "drill": 31}``.
    """
    metadata = pd.read_csv(metadata_file)

    # Auto-detect columns if not specified
    if file_col is None or class_col is None:
        file_col, class_col = _detect_columns(metadata)

    counts: Dict[str, int] = {}
    skipped = 0

    for _, row in metadata.iterrows():
        class_name = str(row[class_col]).strip()
        file_name  = str(row[file_col]).strip()

        source_file = audio_files.get(file_name)
        if source_file is None or not os.path.isfile(source_file):
            skipped += 1
            continue

        class_dir = os.path.join(output_base_path, class_name)
        dest_file = os.path.join(class_dir, file_name)

        # Skip if already copied (idempotent)
        if os.path.exists(dest_file):
            continue

        os.makedirs(class_dir, exist_ok=True)
        shutil.copy2(source_file, dest_file)
        counts[class_name] = counts.get(class_name, 0) + 1

    logger.info(
        "Copied %d files across %d classes  (%d skipped – not found)",
        sum(counts.values()), len(counts), skipped,
    )
    return counts


# ────────────────────────────────────────────────────────────────
#  Public API  (called from FastAPI endpoint or CLI)
# ────────────────────────────────────────────────────────────────

def homogenise_dataset(
    base_path: str = "../../external_sound_data",
    output_path: str = "../../sampled_data",
    metadata_file: Optional[str] = None,
    extensions: Optional[List[str]] = None,
) -> Dict[str, int]:
    """
    End-to-end: discover audio → read metadata → copy into class dirs.

    If ``metadata_file`` is ``None``, we auto-search for common names
    (``UrbanSound8K.csv``, ``esc50.csv``, ``meta.csv``, ``metadata.csv``).
    """
    # Auto-find metadata file
    if metadata_file is None:
        candidates = ["UrbanSound8K.csv", "esc50.csv", "meta.csv",
                       "metadata.csv", "meta/esc50.csv"]
        for c in candidates:
            path = os.path.join(base_path, c)
            if os.path.isfile(path):
                metadata_file = path
                logger.info("Auto-detected metadata: %s", path)
                break
        if metadata_file is None:
            raise FileNotFoundError(
                f"No metadata CSV found in {base_path}.  "
                f"Searched: {candidates}"
            )

    audio_files = find_audio_files(base_path, extensions)
    if not audio_files:
        raise FileNotFoundError(
            f"No audio files found in {base_path} with extensions {extensions}"
        )

    logger.info("Found %d audio files in %s", len(audio_files), base_path)
    return copy_files_to_class_directories(
        metadata_file, audio_files, output_path
    )


# ────────────────────────────────────────────────────────────────
#  CLI
# ────────────────────────────────────────────────────────────────

def main():
    """Interactive CLI wrapper."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s  %(message)s")

    base_path = input("Source path [../../external_sound_data]: ").strip()
    base_path = base_path or "../../external_sound_data"

    output_path = input("Output path [../../sampled_data]: ").strip()
    output_path = output_path or "../../sampled_data"

    metadata_file = input(
        "Metadata CSV (leave blank to auto-detect): "
    ).strip() or None

    counts = homogenise_dataset(base_path, output_path, metadata_file)
    print(f"\n✅  Done – {sum(counts.values())} files across {len(counts)} classes")
    for cls, n in sorted(counts.items()):
        print(f"   {cls}: {n}")


if __name__ == "__main__":
    main()
