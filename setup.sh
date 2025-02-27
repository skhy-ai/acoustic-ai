#!/bin/bash
# Exit immediately if any command exits with a non-zero status.
set -e

# Define the root project directory
PROJECT_DIR="sound_classifier_system"

echo "Creating project structure in '$PROJECT_DIR'..."

# Create the root directory
mkdir -p "$PROJECT_DIR"

# Create main module directories
MODULE_DIRS=(
  "$PROJECT_DIR/acquisitions/dataset_download"
  "$PROJECT_DIR/acquisitions/youtube"
  "$PROJECT_DIR/api"
  "$PROJECT_DIR/cleanup"
  "$PROJECT_DIR/doppler"
  "$PROJECT_DIR/models"
  "$PROJECT_DIR/processing/augmentation"
  "$PROJECT_DIR/processing/segmentation"
  "$PROJECT_DIR/processing/cleanup"
  "$PROJECT_DIR/processing/dataset_preparation"
  "$PROJECT_DIR/reports"
)

for dir in "${MODULE_DIRS[@]}"; do
    mkdir -p "$dir"
    echo "Created directory: $dir"
done

# Create intermediate data directories
INTERMEDIATE_DIRS=(
  "$PROJECT_DIR/external_sound_data"           # Raw external datasets
  "$PROJECT_DIR/sound_data/raw"                  # Raw acquired audio files
  "$PROJECT_DIR/sound_data/filtered"             # Cleaned audio files after filtering
  "$PROJECT_DIR/sound_data/pitch_adjusted"       # Audio files after pitch shifting
  "$PROJECT_DIR/sound_data/volume_adjusted"      # Audio files after volume adjustments
  "$PROJECT_DIR/sound_data/filtered_reverse"     # Reversed audio files
  "$PROJECT_DIR/sound_data/chunked"              # Segmented audio chunks
  "$PROJECT_DIR/sampled_data"                    # Organized samples after metadata-based processing
  "$PROJECT_DIR/sound_dataset"                   # Final train/validation/test splits
  "$PROJECT_DIR/features"                        # Extracted audio features
)

for dir in "${INTERMEDIATE_DIRS[@]}"; do
    mkdir -p "$dir"
    echo "Created directory: $dir"
done

# Create __init__.py files in all Python package directories
INIT_FILES=(
  "$PROJECT_DIR/__init__.py"
  "$PROJECT_DIR/acquisitions/__init__.py"
  "$PROJECT_DIR/acquisitions/dataset_download/__init__.py"
  "$PROJECT_DIR/acquisitions/youtube/__init__.py"
  "$PROJECT_DIR/api/__init__.py"
  "$PROJECT_DIR/cleanup/__init__.py"
  "$PROJECT_DIR/doppler/__init__.py"
  "$PROJECT_DIR/models/__init__.py"
  "$PROJECT_DIR/processing/__init__.py"
  "$PROJECT_DIR/processing/augmentation/__init__.py"
  "$PROJECT_DIR/processing/segmentation/__init__.py"
  "$PROJECT_DIR/processing/cleanup/__init__.py"
  "$PROJECT_DIR/processing/dataset_preparation/__init__.py"
  "$PROJECT_DIR/reports/__init__.py"
)

for file in "${INIT_FILES[@]}"; do
    touch "$file"
    echo "Created file: $file"
done

# Create a basic README.md with initial content
README_FILE="$PROJECT_DIR/README.md"
cat > "$README_FILE" <<EOL
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

EOL

echo "Created $README_FILE"

# Create a basic requirements.txt with initial dependencies
REQ_FILE="$PROJECT_DIR/requirements.txt"
cat > "$REQ_FILE" <<EOL
librosa
numpy
sounddevice
joblib
python-dotenv
uvicorn
fastapi
yt_dlp
pytube
scipy
soundata
pydub
pyrubberband
noisereduce
pandas
scikit-learn
soundfile
tkinter
EOL

echo "Created $REQ_FILE"
echo "Project structure for '$PROJECT_DIR' created successfully."
