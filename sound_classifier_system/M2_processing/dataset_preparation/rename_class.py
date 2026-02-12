"""
Rename Class – Manual Directory-to-Class Mapping
==================================================
Purpose:
    When external datasets (e.g. a collection of WAV files from a drone
    recording session) do NOT have a metadata CSV, the user manually maps
    directories → class labels.  This script walks ``external_sound_data/``,
    presents the top-level sub-directories, and lets the user assign a
    class name to each.  Files are then copied into ``sampled_data/<class>/``.

Workflow position:
    M1_acquisitions  →  external_sound_data/
                             │
                   [no metadata CSV available]
                             │
                             ▼
                       **rename_class.py**
                             │
                             ▼
                        sampled_data/<class>/

Logic notes:
    • The user selects which directories to include – not all directories
      may contain relevant audio.
    • Class names are normalised (lowered, spaces → underscores) to avoid
      file-system issues on Windows.
    • Files that already exist in the target are skipped (idempotent).
    • The ``rename_and_copy()`` function is importable from the API layer
      so the Electron UI can call it without a terminal.
    • We validate that at least one audio file exists in each selected
      directory before copying.

KNOWN EDGE CASES:
    - If a directory contains sub-directories (e.g. ``fold1/engine/``),
      those are NOT walked – only the top-level files are copied.  If deep
      walking is needed, use ``metadata_based_class_creation.py`` instead.
    - .flac and .ogg are now supported in addition to .wav and .mp3.
"""

import os
import shutil
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported audio extensions (without leading dot for matching convenience)
_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg"}


def list_directories_with_audio(
    base_path: str,
    extensions: Optional[List[str]] = None,
) -> List[Tuple[str, int]]:
    """
    Find all immediate sub-directories of ``base_path`` that contain
    at least one audio file.

    Returns
    -------
    list of (directory_path, file_count) tuples.

    NOTE: We intentionally do *not* recurse deeper than one level here.
    This keeps the UI simple (one directory = one class).  For nested
    structures, use ``metadata_based_class_creation.py``.
    """
    exts = set(extensions) if extensions else _AUDIO_EXTENSIONS
    results: List[Tuple[str, int]] = []

    for entry in sorted(os.listdir(base_path)):
        dir_path = os.path.join(base_path, entry)
        if not os.path.isdir(dir_path):
            continue    # skip loose files at the root level

        count = sum(
            1 for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f))
            and os.path.splitext(f)[1].lower() in exts
        )
        if count > 0:
            results.append((dir_path, count))

    return results


def _normalise_class_name(name: str) -> str:
    """
    Sanitise a user-provided class name for safe filesystem usage.
    e.g. " Air  Conditioner " → "air_conditioner"
    """
    return "_".join(name.lower().split())


def copy_directory_to_class(
    source_dir: str,
    dest_dir: str,
    extensions: Optional[List[str]] = None,
) -> int:
    """
    Copy all audio files from ``source_dir`` into ``dest_dir``.

    Returns the number of files actually copied (skips existing ones).
    """
    exts = set(extensions) if extensions else _AUDIO_EXTENSIONS
    os.makedirs(dest_dir, exist_ok=True)
    copied = 0

    for fname in os.listdir(source_dir):
        if os.path.splitext(fname)[1].lower() not in exts:
            continue
        src = os.path.join(source_dir, fname)
        dst = os.path.join(dest_dir, fname)
        if not os.path.isfile(src):
            continue
        if os.path.exists(dst):
            # Already copied in a previous run – skip for idempotency
            continue
        shutil.copy2(src, dst)
        copied += 1

    return copied


# ────────────────────────────────────────────────────────────────
#  Public API  (called from FastAPI endpoint or CLI)
# ────────────────────────────────────────────────────────────────

def rename_and_copy(
    directory_class_map: Dict[str, str],
    output_base_path: str = "../../sampled_data",
    extensions: Optional[List[str]] = None,
) -> Dict[str, int]:
    """
    Given a mapping ``{source_directory: class_name}``, copy each
    directory's audio files into ``output_base_path/<class_name>/``.

    Parameters
    ----------
    directory_class_map : dict
        ``{"/path/to/fold1": "siren", "/path/to/fold2": "drill", …}``
    output_base_path : str
    extensions : list of str, optional

    Returns
    -------
    dict  –  ``{class_name: files_copied}``
    """
    results: Dict[str, int] = {}

    for src_dir, raw_class in directory_class_map.items():
        cls = _normalise_class_name(raw_class)
        dest_dir = os.path.join(output_base_path, cls)
        n = copy_directory_to_class(src_dir, dest_dir, extensions)
        results[cls] = results.get(cls, 0) + n
        logger.info("Copied %d files from %s → %s", n, src_dir, dest_dir)

    logger.info(
        "Total: %d files across %d classes",
        sum(results.values()), len(results),
    )
    return results


# ────────────────────────────────────────────────────────────────
#  CLI
# ────────────────────────────────────────────────────────────────

def main():
    """Interactive CLI for directory → class mapping."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s  %(message)s")

    base_path = input("Source path [../../external_sound_data]: ").strip()
    base_path = base_path or "../../external_sound_data"

    output_base_path = input("Output path [../../sampled_data]: ").strip()
    output_base_path = output_base_path or "../../sampled_data"

    dirs = list_directories_with_audio(base_path)
    if not dirs:
        print(f"No directories with audio found in {base_path}")
        return

    print("\nAvailable directories:")
    for i, (d, count) in enumerate(dirs, 1):
        print(f"  {i}. {os.path.basename(d)}  ({count} files)")

    selected = input(
        "\nEnter numbers to include (comma-separated, or 'all'): "
    ).strip()

    if selected.lower() == "all":
        indices = list(range(len(dirs)))
    else:
        indices = [int(x.strip()) - 1 for x in selected.split(",")
                   if x.strip().isdigit()]
        indices = [i for i in indices if 0 <= i < len(dirs)]

    dir_class_map: Dict[str, str] = {}
    for idx in indices:
        d, count = dirs[idx]
        default = os.path.basename(d)
        cls = input(f"  Class name for '{default}' [{default}]: ").strip()
        cls = cls or default
        dir_class_map[d] = cls

    if not dir_class_map:
        print("Nothing selected.")
        return

    results = rename_and_copy(dir_class_map, output_base_path)
    print(f"\n✅  Done – {sum(results.values())} files, {len(results)} classes")


if __name__ == "__main__":
    main()
