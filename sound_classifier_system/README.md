# Acoustic AI — Sound Classifier System

A desktop application for environmental sound classification, direction-of-arrival (DOA)
estimation, Doppler velocity analysis, and frequency-band pre-classification.

**Frontend:** Electron + Vite + React + TypeScript  
**Backend:** Python FastAPI + scikit-learn + librosa  
**Database:** SQLite (local, embedded)

---

## Quick Start

### 1. Clone & set up Python backend

```bash
cd acoustic_ai
# Create venv, install deps, and set up alias:
source activate.sh
```

This creates a virtual environment, installs all Python dependencies, and
provides an `acoustic-ai-start` alias to launch the backend.

### 2. Start the backend

```bash
acoustic-ai-start
# → FastAPI running at http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### 3. Start the frontend

```bash
cd flow-pilot-web-ui
npm install
npm run dev
# → Vite dev server at http://localhost:5173
```

### 4. Run as Electron desktop app

```bash
cd flow-pilot-web-ui
npm run electron:dev
```

---

## Project Structure

```
acoustic_ai/
├── flow-pilot-web-ui/          # Electron + React frontend
│   ├── electron/               # Main process, preload, IPC
│   ├── src/components/         # UI components
│   ├── src/services/           # API client layer
│   └── tests/e2e/              # Playwright E2E tests
│
├── sound_classifier_system/    # Python backend
│   ├── api/                    # FastAPI server (main.py, endpoints.py)
│   ├── acquisitions/           # Data acquisition (HAL, datasets, YouTube)
│   ├── M2_processing/          # Audio processing pipeline
│   │   ├── augmentation/       # Pitch, volume, reverse, filter+augment
│   │   ├── dataset_preparation/# Feature extraction, homogenisation, splits
│   │   ├── segmentation/       # Chunking, sliding window
│   │   ├── frequency_filter.py # Hybrid pre-classifier
│   │   └── doa.py              # GCC-PHAT direction of arrival
│   ├── doppler/                # Doppler velocity estimation
│   ├── M3_modelling/           # ML model training
│   ├── cleanup/                # Audio validation
│   └── reports/                # Report generation
│
├── activate.sh                 # Venv setup + alias
├── setup.sh                    # Directory scaffolding
└── README.md
```

---

## API Endpoints

| Group | Method | Path | Description |
|-------|--------|------|-------------|
| Health | GET | `/api/health` | Liveness check |
| Hardware | GET | `/api/hardware/devices` | List audio input devices |
| Processing | POST | `/api/processing/extract-features` | Extract feature vector |
| Analysis | POST | `/api/analysis/doa` | Direction of Arrival |
| Analysis | POST | `/api/analysis/doppler` | Doppler velocity analysis |
| Analysis | POST | `/api/analysis/frequency-bands` | Frequency band energy |
| Analysis | POST | `/api/analysis/hybrid-classify` | Hybrid pre-classification |
| Data | POST | `/api/data/homogenise` | Dataset homogenisation |
| Data | POST | `/api/data/filter-augment` | Quality filter + augmentation |
| Visualise | POST | `/api/visualize/spectrogram` | Mel spectrogram plot |
| Visualise | POST | `/api/visualize/waveform` | Waveform plot |
| Visualise | POST | `/api/visualize/doppler` | Doppler analysis plot |
| Model | POST | `/api/model/train` | Train classifier |
| Model | POST | `/api/classify-audio/` | Classify audio file |
| Real-time | WS | `/api/ws/stream/{id}` | Live audio classification |

Full documentation available at `http://localhost:8000/docs` (Swagger UI).

---

## Installation Modes

### Development (Full Suite)

All features: acquisition, augmentation, training, inference, DOA, Doppler,
filtering, reports, admin panel.

```bash
INSTALL_MODE=development npm run electron:build
```

### Edge Device (Production Inference)

Inference-only: real-time classification, DOA/Doppler, calibration, configuration.
Hosts pre-trained models. Optimised for low-resource embedded devices.

```bash
INSTALL_MODE=edge npm run electron:build
```

---

## Running Tests

### Playwright E2E

```bash
cd flow-pilot-web-ui
npx playwright install --with-deps
npx playwright test
```

### Backend Import Check

```bash
cd sound_classifier_system
python -c "from api.endpoints import router; print('OK')"
```

---

## Dependencies

Python dependencies are listed in `sound_classifier_system/requirements.txt`.
Frontend dependencies are managed via `flow-pilot-web-ui/package.json`.

Key Python packages: `librosa`, `numpy`, `scipy`, `scikit-learn`, `fastapi`,
`uvicorn`, `soundfile`, `pydub`, `pyrubberband`, `noisereduce`, `matplotlib`.

---

## Architecture & Diagrams

- [architecture.md](architecture.md) — System overview, module map, data flow
- [sequence_diagrams.md](sequence_diagrams.md) — Sequence diagrams for all services
