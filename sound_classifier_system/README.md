# Sound Classifier System

A comprehensive system for sound classification, acquisition, processing, model building, and API exposure. This project is modularized for scalability and maintainability.

## Directory Structure

- **acquisitions/**: Tools for acquiring sound data, including:
  - **dataset_download/**: Unified dataset download and custom dataset code.
  - **youtube/**: YouTube playlist and video audio extraction.
- **api/**: FastAPI endpoints for real-time processing and model serving.
- **cleanup/**: Global audio cleanup utilities.
- **doppler/**: Doppler velocity estimation functions.
- **models/**: Machine learning model management.
- **processing/**: Audio processing modules:
  - **feature_extraction.py**: Audio feature extraction code.
  - **source_separation.py** (optional): Source separation functions.
  - **sliding_window.py** (optional): Sliding window utilities.
  - **augmentation/**: Audio augmentation functions (pitch shifting, volume adjustment, reversal).
  - **segmentation/**: Audio segmentation (chunking) functions.
  - **cleanup/**: Audio file validation and cleanup.
  - **dataset_preparation/**: Organizing and sampling audio data using metadata.
- **reports/**: Reporting modules for sampled data and organized datasets.
- **external_sound_data/**: Raw external datasets.
- **sound_data/**: Intermediate audio files.
  - **raw/**: Acquired raw audio.
  - **filtered/**: Cleaned audio files.
  - **pitch_adjusted/**: Audio after pitch modifications.
  - **volume_adjusted/**: Audio after volume adjustments.
  - **filtered_reverse/**: Reversed audio files.
  - **chunked/**: Audio chunks from segmentation.
- **sampled_data/**: Organized samples from metadata-based processing.
- **sound_dataset/**: Final train/validation/test splits.
- **features/**: Extracted audio features.

**Directory_Structure**:

sound_classifier_system/
├── acquisitions/
│   ├── __init__.py
│   ├── dataset_download/
│   │   ├── __init__.py
│   │   ├── unified.py                  # Unified dataset download and custom dataset code
│   │   └── urbansound.py               # UrbanSound8K-specific download
│   └── youtube/
│       ├── __init__.py
│       ├── playlist.py                 # Save YouTube playlist URLs
│       ├── download.py                 # Single YouTube video audio download
│       └── bulk_download.py            # Bulk YouTube audio download
├── api/
│   ├── __init__.py
│   ├── endpoints.py                  # All REST and WebSocket endpoints
│   └── main.py                       # FastAPI application initialization
├── cleanup/
│   ├── __init__.py
│   └── audio_cleanup.py              # Audio decibel-level cleanup or other high-level cleanup tasks
├── doppler/
│   ├── __init__.py
│   └── doppler.py                    # Doppler velocity estimation functions
├── models/
│   ├── __init__.py
│   └── model_manager.py              # Code to load and manage ML models
├── processing/
│   ├── __init__.py
│   ├── feature_extraction.py         # Feature extraction code
│   ├── source_separation.py          # Optional: Source separation functions
│   ├── sliding_window.py             # Optional: Sliding window utilities
│   ├── augmentation/
│   │   ├── __init__.py
│   │   ├── adjust_pitch.py           # Combined pitch shifting (with noise reduction option) from adjust_pitch_noise_filtered.py and adjust_pitch_files.py
│   │   ├── adjust_volume.py          # Volume adjustment functions from adjust_volume_files.py
│   │   └── reverse_audio.py          # Audio reversal functionality from reverse_audio_files.py
│   ├── segmentation/
│   │   ├── __init__.py
│   │   ├── generate_chunks.py        # Audio chunking (click detection) from generate_chunks.py
│   │   └── generate_chunks_bulk.py   # Bulk audio chunking from generate_chunks_on_click_bulk.py
│   ├── cleanup/
│   │   ├── __init__.py
│   │   └── cleanup_invalid_files.py  # Remove invalid audio files (using librosa)
│   └── dataset_preparation/
│       ├── __init__.py
│       ├── metadata_based_class_creation.py   # Organizes files into class directories based on metadata
│       ├── organize_sound_samples.py          # Splits dataset into train/val/test splits
│       └── rename_class.py                    # Renames/reorganizes classes from external datasets
├── reports/
│   ├── __init__.py
│   ├── sampled_data_report.py        # Reports on sampled data
│   └── sound_dataset_report.py       # Reports on organized dataset
├── README.md                         # Project overview and usage instructions
└── requirements.txt                  # List of project dependencies


