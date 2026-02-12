"""
Expanded FastAPI Endpoints
===========================
Covers the full workflow: hardware discovery, data acquisition,
feature extraction, DOA analysis, Doppler velocity estimation,
frequency-band pre-classification, data homogenisation,
filtering/augmentation pipeline, model training, visualisation,
and real-time streaming.

ARCHITECTURE NOTE:
    Each endpoint group corresponds to a stage in the acoustic AI pipeline:
    1. /hardware/*       → device discovery (HAL)
    2. /processing/*     → feature extraction
    3. /analysis/*       → DOA, Doppler, frequency bands, hybrid classify
    4. /data/*           → dataset homogenisation, filtering, augmentation
    5. /visualize/*      → server-side plots (Matplotlib → Base64 PNG)
    6. /model/*          → training & classification
    7. /ws/*             → real-time WebSocket streaming
"""

import os
import io
import json
import base64
import tempfile
import uuid
import logging
from typing import Optional, List
from pathlib import Path

import numpy as np
import librosa
import matplotlib
matplotlib.use("Agg")          # non-interactive backend for headless
import matplotlib.pyplot as plt

from fastapi import APIRouter, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---- internal imports ------------------------------------------------
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from M2_processing.dataset_preparation.feature_extraction import (
    extract_features, FeatureConfig
)
from M2_processing.doa import estimate_doa, gcc_phat, estimate_doa_array
from acquisitions.hal.hydrophone import HydrophoneSource

# Doppler & frequency-band analysis (new)
from doppler.doppler import (
    calculate_velocity as doppler_velocity,
    full_doppler_analysis,
)
from M2_processing.frequency_filter import (
    frequency_band_energy,
    hybrid_classify,
)
# Data homogenisation helpers
from M2_processing.dataset_preparation.metadata_based_class_creation import (
    homogenise_dataset,
)
# Filtering & augmentation
from M2_processing.augmentation.filtering_augmentation import (
    filter_dataset, augment_dataset, FilterConfig, AugmentConfig,
)
# Individual augmentation modules (called by frontend augmentationService.ts)
from M2_processing.augmentation.adjust_pitch import (
    adjust_pitch_and_volume as pitch_shift_files,
    process_all_files as pitch_shift_batch,
)
from M2_processing.augmentation.adjust_volume import (
    adjust_volume as volume_adjust_file,
    process_all_files as volume_adjust_batch,
)
from M2_processing.augmentation.reverse_audio import (
    reverse_audio as reverse_audio_file,
    process_all_files as reverse_batch,
)
# Segmentation & preprocessing
from M2_processing.segmentation.generate_chunks import (
    process_all_files as chunk_all_files,
)
from M2_processing.segmentation.sliding_window import sliding_window
from M2_processing.segmentation.source_separation import separate_sources
# Dataset management
from M2_processing.dataset_preparation.organize_sound_samples import (
    organize_samples,
)
from M2_processing.dataset_preparation.rename_class import (
    rename_and_copy, list_directories_with_audio,
)
# M5 Application models (anomaly detection, clustering, scene analysis)
from M3_modelling.application_models import (
    detect_anomalies, cluster_audio, analyze_scene,
)

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100
DATA_DIR = os.environ.get("ACOUSTIC_DATA_DIR",
                          os.path.expanduser("~/acoustic_ai_data"))
os.makedirs(DATA_DIR, exist_ok=True)

router = APIRouter()


# =====================================================================
#  Schemas
# =====================================================================
class FeatureConfigRequest(BaseModel):
    mfcc: bool = True
    n_mfcc: int = 40
    delta_mfcc: bool = True
    chroma: bool = True
    mel: bool = True
    contrast: bool = True
    tonnetz: bool = True
    zcr: bool = True
    rms: bool = True
    spectral_centroid: bool = True
    spectral_bandwidth: bool = True
    spectral_rolloff: bool = True
    spectral_flatness: bool = True
    spectral_flux: bool = False
    stats: List[str] = Field(default=["mean", "std"])


class TrainRequest(BaseModel):
    data_path: str
    model_type: str = "random_forest"  # random_forest | svm | knn
    feature_config: FeatureConfigRequest = FeatureConfigRequest()
    test_split: float = 0.2
    normalize: bool = True


class DOARequest(BaseModel):
    mic_distance: float = 0.05
    speed_of_sound: float = 343.0


class HardwareConfig(BaseModel):
    hw_type: str = "hydrophone"       # hydrophone | 7mems | 16mems
    device_id: Optional[int] = None
    host: Optional[str] = "0.0.0.0"
    port: Optional[int] = 5000
    sample_rate: int = 44100


# =====================================================================
#  Health / Info
# =====================================================================
@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/status")
async def server_status():
    """Return module availability, version, and uptime info."""
    import time
    modules = {
        "hardware_hal": True,
        "feature_extraction": True,
        "doa_analysis": True,
        "doppler_analysis": True,
        "frequency_filter": True,
        "data_homogenisation": True,
        "filtering_augmentation": True,
        "m3_augmentation": True,
        "model_training": True,
        "classification": True,
        "anomaly_detection": True,
        "clustering": True,
        "scene_analysis": True,
        "segmentation": True,
        "source_separation": True,
        "dataset_organisation": True,
        "websocket_streaming": True,
    }
    return {
        "modules": modules,
        "version": "1.0.0",
        "uptime": time.time(),
    }


# =====================================================================
#  Hardware Discovery
# =====================================================================
@router.get("/hardware/devices")
async def list_audio_devices():
    """Return all available PortAudio input devices."""
    return HydrophoneSource.list_devices()


# =====================================================================
#  Feature Extraction
# =====================================================================
@router.post("/processing/extract-features")
async def api_extract_features(
    file: UploadFile = File(...),
    config_json: str = Form("{}")
):
    """
    Extract features from a single uploaded audio file.
    ``config_json`` is a JSON string matching FeatureConfigRequest.
    """
    cfg_dict = json.loads(config_json)
    cfg = FeatureConfig(**cfg_dict)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        features = extract_features(tmp_path, config=cfg)
        if features is None:
            return JSONResponse(status_code=400,
                                content={"error": "Feature extraction failed"})
        return {"features": features.tolist(), "length": len(features)}
    finally:
        os.unlink(tmp_path)


# =====================================================================
#  DOA Analysis
# =====================================================================
@router.post("/analysis/doa")
async def api_doa(
    file: UploadFile = File(...),
    mic_distance: float = Form(0.05),
    speed_of_sound: float = Form(343.0),
    channel_a: int = Form(0),
    channel_b: int = Form(1),
):
    """
    Estimate Direction of Arrival from a multi-channel audio file.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        audio, sr = librosa.load(tmp_path, sr=None, mono=False)
        if audio.ndim == 1:
            return JSONResponse(status_code=400,
                                content={"error": "Need multi-channel audio"})

        sig1 = audio[channel_a]
        sig2 = audio[channel_b]

        angle = estimate_doa(sig1, sig2, sr, mic_distance, speed_of_sound)
        tau, cc = gcc_phat(sig1, sig2, sr, max_tau=mic_distance / speed_of_sound)

        return {
            "angle_deg": angle,
            "tdoa_seconds": tau,
            "sample_rate": sr,
            "channels_used": [channel_a, channel_b],
        }
    finally:
        os.unlink(tmp_path)


# =====================================================================
#  Doppler Velocity Analysis (NEW)
# =====================================================================
class DopplerRequest(BaseModel):
    source_frequency_hz: Optional[float] = None
    speed_of_sound: float = 343.0
    distance_m: Optional[float] = None
    frame_length_s: float = 0.1
    hop_length_s: float = 0.05


@router.post("/analysis/doppler")
async def api_doppler_analysis(
    file: UploadFile = File(...),
    config_json: str = Form("{}"),
):
    """
    Full Doppler analysis on an uploaded audio file.
    Returns per-frame frequency track, velocity estimates, direction
    labels, and travel-time estimates (if distance is provided).

    LOGIC NOTE:
        This endpoint returns all the data needed for the frontend
        Doppler visualisation: time-series data for plotting frequency
        vs time, velocity vs time, and a direction indicator.
    """
    cfg = json.loads(config_json)
    req = DopplerRequest(**cfg)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        audio, sr = librosa.load(tmp_path, sr=None)
        result = full_doppler_analysis(
            audio, sr,
            source_frequency=req.source_frequency_hz,
            speed_of_sound=req.speed_of_sound,
            distance_m=req.distance_m,
            frame_length_s=req.frame_length_s,
            hop_length_s=req.hop_length_s,
        )
        return result
    finally:
        os.unlink(tmp_path)


# =====================================================================
#  Frequency-Band Energy Analysis (NEW)
# =====================================================================
@router.post("/analysis/frequency-bands")
async def api_frequency_bands(file: UploadFile = File(...)):
    """
    Compute normalised energy per frequency band for a single audio file.
    Useful for understanding the spectral signature before classification.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        audio, sr = librosa.load(tmp_path, sr=None)
        bands = frequency_band_energy(audio, sr)
        return {"bands": bands, "sample_rate": sr}
    finally:
        os.unlink(tmp_path)


# =====================================================================
#  Hybrid Pre-Classification (Frequency + Doppler) (NEW)
# =====================================================================
@router.post("/analysis/hybrid-classify")
async def api_hybrid_classify(
    file: UploadFile = File(...),
    config_json: str = Form("{}"),
):
    """
    Fast first-guess classification using frequency-band energy patterns
    combined with optional Doppler motion analysis.

    LOGIC NOTE:
        This runs BEFORE the ML classifier and returns a heuristic
        class estimate.  The frontend shows this as a "quick estimate"
        while the ML model processes.
    """
    cfg = json.loads(config_json)
    doppler_cfg = DopplerRequest(**cfg)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        audio, sr = librosa.load(tmp_path, sr=None)

        # Run Doppler analysis to get motion context
        doppler_result = full_doppler_analysis(
            audio, sr,
            source_frequency=doppler_cfg.source_frequency_hz,
            speed_of_sound=doppler_cfg.speed_of_sound,
            distance_m=doppler_cfg.distance_m,
        )

        # Hybrid classification using frequency bands + Doppler context
        result = hybrid_classify(
            audio, sr,
            doppler_result=doppler_result["summary"],
        )
        result["doppler_summary"] = doppler_result["summary"]
        return result
    finally:
        os.unlink(tmp_path)


# =====================================================================
#  Doppler Visualisation (server-side plot → Base64 PNG) (NEW)
# =====================================================================
@router.post("/visualize/doppler")
async def api_doppler_plot(
    file: UploadFile = File(...),
    config_json: str = Form("{}"),
):
    """
    Generate a Doppler analysis plot with three subplots:
    1. Dominant frequency vs time
    2. Estimated velocity vs time
    3. Frequency-band energy bar chart

    Returns a Base64-encoded PNG suitable for direct embedding in
    an <img> tag on the frontend.
    """
    cfg = json.loads(config_json)
    req = DopplerRequest(**cfg)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        audio, sr = librosa.load(tmp_path, sr=None)

        # Doppler analysis
        doppler = full_doppler_analysis(
            audio, sr,
            source_frequency=req.source_frequency_hz,
            speed_of_sound=req.speed_of_sound,
            distance_m=req.distance_m,
        )

        # Frequency bands
        bands = frequency_band_energy(audio, sr)

        # Create figure with 3 subplots
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle("Doppler & Frequency Analysis", fontsize=14, fontweight="bold")

        # 1. Frequency track
        ax1 = axes[0]
        times = doppler["times"]
        freqs = doppler["frequencies"]
        ax1.plot(times, freqs, color="#2196F3", linewidth=1.5)
        ax1.set_ylabel("Dominant Freq (Hz)")
        ax1.set_xlabel("Time (s)")
        ax1.set_title("Frequency Track")
        ax1.grid(True, alpha=0.3)

        # 2. Velocity
        ax2 = axes[1]
        vels = doppler["velocities"]
        colors = ["#4CAF50" if d == "approaching" else
                  "#F44336" if d == "receding" else "#9E9E9E"
                  for d in doppler["directions"]]
        ax2.bar(times, vels, width=req.hop_length_s * 0.8, color=colors, alpha=0.7)
        ax2.axhline(y=0, color="black", linewidth=0.5)
        ax2.set_ylabel("Velocity (m/s)")
        ax2.set_xlabel("Time (s)")
        ax2.set_title("Estimated Velocity (green=approaching, red=receding)")
        ax2.grid(True, alpha=0.3)

        # 3. Frequency band energy
        ax3 = axes[2]
        band_names = [b["name"] for b in bands]
        energies = [b["energy"] for b in bands]
        bar_colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(bands)))
        ax3.barh(band_names, energies, color=bar_colors)
        ax3.set_xlabel("Normalised Energy")
        ax3.set_title("Frequency Band Energy Distribution")

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
        plt.close(fig)
        buf.seek(0)

        return {
            "image_base64": base64.b64encode(buf.read()).decode("utf-8"),
            "content_type": "image/png",
            "doppler_summary": doppler["summary"],
        }
    finally:
        os.unlink(tmp_path)


# =====================================================================
#  Data Homogenisation (NEW)
# =====================================================================
class HomogeniseRequest(BaseModel):
    base_path: str = "../../external_sound_data"
    output_path: str = "../../sampled_data"
    metadata_file: Optional[str] = None


@router.post("/data/homogenise")
async def api_homogenise(req: HomogeniseRequest):
    """
    Trigger dataset homogenisation: read external data + metadata CSV
    and copy files into class-organised directories.
    """
    try:
        counts = homogenise_dataset(
            base_path=req.base_path,
            output_path=req.output_path,
            metadata_file=req.metadata_file,
        )
        return {
            "status": "success",
            "classes": counts,
            "total_files": sum(counts.values()),
        }
    except FileNotFoundError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# =====================================================================
#  Filter + Augment Pipeline (NEW)
# =====================================================================
class FilterAugmentRequest(BaseModel):
    input_dir: str = "../../sampled_data"
    filtered_dir: str = "../../sampled_data_filtered"
    augmented_dir: str = "../../sampled_data_augmented"
    # Filter config
    min_duration_s: float = 0.5
    max_duration_s: float = 30.0
    min_rms_db: float = -50.0
    low_cut_hz: Optional[float] = 50.0
    high_cut_hz: Optional[float] = 16000.0
    min_snr_db: Optional[float] = 5.0
    # Augment config
    target_samples_per_class: int = 500
    enable_pitch_shift: bool = True
    enable_noise_injection: bool = True


@router.post("/data/filter-augment")
async def api_filter_augment(req: FilterAugmentRequest):
    """
    Run the two-stage quality filter + augmentation pipeline.
    Stage 1: Remove files that fail quality checks.
    Stage 2: Generate augmented samples to balance class sizes.
    """
    filt_cfg = FilterConfig(
        min_duration_s=req.min_duration_s,
        max_duration_s=req.max_duration_s,
        min_rms_db=req.min_rms_db,
        low_cut_hz=req.low_cut_hz,
        high_cut_hz=req.high_cut_hz,
        min_snr_db=req.min_snr_db,
    )
    aug_cfg = AugmentConfig(
        target_samples_per_class=req.target_samples_per_class,
        enable_pitch_shift=req.enable_pitch_shift,
        enable_noise_injection=req.enable_noise_injection,
    )

    try:
        filter_report = filter_dataset(req.input_dir, req.filtered_dir, filt_cfg)
        augment_report = augment_dataset(req.filtered_dir, req.augmented_dir, aug_cfg)
        return {
            "status": "success",
            "filter_report": filter_report,
            "augment_report": augment_report,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# =====================================================================
#  M3 Augmentation — Individual Endpoints
#  Called by frontend augmentationService.ts to increase sample size.
#
#  ARCHITECTURE NOTE:
#    The frontend service has 6 methods (pitch-shift, noise-injection,
#    time-stretch, volume-adjustment, spectral-augmentation, pipeline).
#    Below we expose each as a POST endpoint backed by the corresponding
#    Python augmentation module:
#      adjust_pitch.py    → /m3-augmentation/pitch-shift
#      adjust_volume.py   → /m3-augmentation/volume-adjustment
#      reverse_audio.py   → /m3-augmentation/reverse
#      filtering_augmentation._inject_noise → noise-injection
#      filtering_augmentation._time_stretch → time-stretch
#      filtering_augmentation.augment_dataset → pipeline (class-balanced)
# =====================================================================

class PitchShiftRequest(BaseModel):
    input_dir: str
    output_dir: str
    pitch_changes: List[int] = [-50, -100, -150, -200, -250]
    apply_noise_reduction: bool = True

class VolumeAdjustRequest(BaseModel):
    input_dir: str
    output_dir: str
    decibel_changes: List[float] = [10, 20, -10, -20]

class ReverseAudioRequest(BaseModel):
    input_dir: str
    output_dir: str

class NoiseInjectionRequest(BaseModel):
    input_dir: str
    output_dir: str
    snr_db_levels: List[float] = [20.0, 15.0, 10.0]

class TimeStretchRequest(BaseModel):
    input_dir: str
    output_dir: str
    rates: List[float] = [0.8, 0.9, 1.1, 1.2]

class AugPipelineRequest(BaseModel):
    """Run the unified class-balanced augmentation pipeline."""
    input_dir: str
    output_dir: str
    enable_pitch_shift: bool = True
    enable_time_stretch: bool = True
    enable_noise_injection: bool = True
    enable_volume_scale: bool = True
    target_samples_per_class: int = 500


@router.post("/m3-augmentation/pitch-shift")
async def api_pitch_shift(req: PitchShiftRequest):
    """Apply pitch shifts to all audio files in input_dir."""
    try:
        os.makedirs(req.output_dir, exist_ok=True)
        pitch_shift_batch(req.input_dir, req.output_dir, req.pitch_changes)
        count = sum(1 for f in Path(req.output_dir).rglob("*") if f.is_file())
        return {"status": "success", "output_dir": req.output_dir,
                "files_created": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/m3-augmentation/volume-adjustment")
async def api_volume_adjust(req: VolumeAdjustRequest):
    """Create volume-adjusted variants (louder + quieter) of all files."""
    try:
        os.makedirs(req.output_dir, exist_ok=True)
        volume_adjust_batch(req.input_dir, req.output_dir, req.decibel_changes)
        count = sum(1 for f in Path(req.output_dir).rglob("*") if f.is_file())
        return {"status": "success", "output_dir": req.output_dir,
                "files_created": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/m3-augmentation/reverse")
async def api_reverse_audio(req: ReverseAudioRequest):
    """Create time-reversed copies of all audio files."""
    try:
        os.makedirs(req.output_dir, exist_ok=True)
        reverse_batch(req.input_dir, req.output_dir)
        count = sum(1 for f in Path(req.output_dir).rglob("*") if f.is_file())
        return {"status": "success", "output_dir": req.output_dir,
                "files_created": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/m3-augmentation/noise-injection")
async def api_noise_inject(req: NoiseInjectionRequest):
    """Inject Gaussian noise at various SNR levels into all audio files."""
    try:
        from M2_processing.augmentation.filtering_augmentation import _inject_noise
        import soundfile as sf

        src = Path(req.input_dir)
        dst = Path(req.output_dir)
        dst.mkdir(parents=True, exist_ok=True)
        created = 0
        audio_exts = {".wav", ".mp3", ".flac", ".ogg"}

        for f in src.rglob("*"):
            if f.suffix.lower() not in audio_exts:
                continue
            audio, sr = librosa.load(str(f), sr=None)
            base = f.stem
            for snr in req.snr_db_levels:
                aug = _inject_noise(audio, snr)
                out_name = f"{base}_noise{snr:.0f}dB.wav"
                sf.write(str(dst / out_name), aug, sr)
                created += 1

        return {"status": "success", "output_dir": req.output_dir,
                "files_created": created}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/m3-augmentation/time-stretch")
async def api_time_stretch(req: TimeStretchRequest):
    """Time-stretch all audio files at given rate factors."""
    try:
        from M2_processing.augmentation.filtering_augmentation import _time_stretch
        import soundfile as sf

        src = Path(req.input_dir)
        dst = Path(req.output_dir)
        dst.mkdir(parents=True, exist_ok=True)
        created = 0
        audio_exts = {".wav", ".mp3", ".flac", ".ogg"}

        for f in src.rglob("*"):
            if f.suffix.lower() not in audio_exts:
                continue
            audio, sr = librosa.load(str(f), sr=None)
            base = f.stem
            for rate in req.rates:
                aug = _time_stretch(audio, rate)
                out_name = f"{base}_ts{rate:.1f}.wav"
                sf.write(str(dst / out_name), aug, sr)
                created += 1

        return {"status": "success", "output_dir": req.output_dir,
                "files_created": created}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/m3-augmentation/pipeline")
async def api_augmentation_pipeline(req: AugPipelineRequest):
    """
    Run the unified class-balanced augmentation pipeline.
    RECOMMENDED: automatically balances class sizes up to
    target_samples_per_class using all enabled augmentation strategies.
    """
    try:
        aug_cfg = AugmentConfig(
            enable_pitch_shift=req.enable_pitch_shift,
            enable_time_stretch=req.enable_time_stretch,
            enable_noise_injection=req.enable_noise_injection,
            enable_volume_scale=req.enable_volume_scale,
            target_samples_per_class=req.target_samples_per_class,
        )
        report = augment_dataset(req.input_dir, req.output_dir, aug_cfg)
        return {"status": "success", "augmentation_report": report}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# =====================================================================
#  Manual Audio Filtering (spectrogram-based keep/delete)
# =====================================================================
class ListChunksRequest(BaseModel):
    source_dir: str

class KeepChunkRequest(BaseModel):
    source_path: str
    dest_dir: str
    class_name: str = ""

class DeleteChunkRequest(BaseModel):
    file_path: str


@router.post("/data/list-chunks")
async def api_list_chunks(req: ListChunksRequest):
    """
    List all audio files in a directory, grouped by class (subfolder).
    Returns a flat list of {path, filename, class_name} objects.
    Used by the ManualFilter frontend component.
    """
    import glob

    source = Path(req.source_dir)
    if not source.is_dir():
        return JSONResponse(status_code=400,
                            content={"error": f"Directory not found: {req.source_dir}"})

    audio_exts = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
    files = []

    # Scan subdirectories (each subfolder = class name)
    for class_dir in sorted(source.iterdir()):
        if class_dir.is_dir():
            for f in sorted(class_dir.iterdir()):
                if f.suffix.lower() in audio_exts:
                    files.append({
                        "path": str(f),
                        "filename": f.name,
                        "class_name": class_dir.name,
                    })

    # Also scan top-level files (unclassified)
    for f in sorted(source.iterdir()):
        if f.is_file() and f.suffix.lower() in audio_exts:
            files.append({
                "path": str(f),
                "filename": f.name,
                "class_name": "unclassified",
            })

    return {"files": files, "total": len(files)}


@router.post("/data/keep-chunk")
async def api_keep_chunk(req: KeepChunkRequest):
    """
    Keep an audio chunk: copy it from the source path to the
    destination directory, preserving class structure.
    """
    import shutil

    src = Path(req.source_path)
    if not src.is_file():
        return JSONResponse(status_code=404,
                            content={"error": f"File not found: {req.source_path}"})

    dest_base = Path(req.dest_dir)
    if req.class_name:
        dest_dir = dest_base / req.class_name
    else:
        dest_dir = dest_base

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / src.name

    shutil.copy2(str(src), str(dest_path))
    return {"status": "kept", "destination": str(dest_path)}


@router.post("/data/delete-chunk")
async def api_delete_chunk(req: DeleteChunkRequest):
    """
    Delete an audio chunk permanently.
    """
    fp = Path(req.file_path)
    if not fp.is_file():
        return JSONResponse(status_code=404,
                            content={"error": f"File not found: {req.file_path}"})

    fp.unlink()
    return {"status": "deleted", "file": req.file_path}


# =====================================================================
#  Visualisation (server-side Matplotlib → Base64)
# =====================================================================
@router.post("/visualize/spectrogram")
async def api_spectrogram(
    file: UploadFile = File(...),
    n_fft: int = Form(2048),
    hop_length: int = Form(512),
):
    """Return a Mel spectrogram as a Base64-encoded PNG image."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        audio, sr = librosa.load(tmp_path, sr=None)
        S = librosa.feature.melspectrogram(y=audio, sr=sr,
                                           n_fft=n_fft,
                                           hop_length=hop_length)
        S_dB = librosa.power_to_db(S, ref=np.max)

        fig, ax = plt.subplots(figsize=(10, 4))
        img = librosa.display.specshow(S_dB, sr=sr, hop_length=hop_length,
                                        x_axis="time", y_axis="mel", ax=ax)
        fig.colorbar(img, ax=ax, format="%+2.0f dB")
        ax.set_title("Mel Spectrogram")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)
        buf.seek(0)

        return {
            "image_base64": base64.b64encode(buf.read()).decode("utf-8"),
            "content_type": "image/png",
        }
    finally:
        os.unlink(tmp_path)


@router.post("/visualize/waveform")
async def api_waveform(file: UploadFile = File(...)):
    """Return a waveform plot as a Base64-encoded PNG image."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        audio, sr = librosa.load(tmp_path, sr=None)
        fig, ax = plt.subplots(figsize=(10, 3))
        librosa.display.waveshow(audio, sr=sr, ax=ax)
        ax.set_title("Waveform")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)
        buf.seek(0)

        return {
            "image_base64": base64.b64encode(buf.read()).decode("utf-8"),
            "content_type": "image/png",
        }
    finally:
        os.unlink(tmp_path)


# =====================================================================
#  Model Training  (simplified – full pipeline)
# =====================================================================
@router.post("/model/train")
async def api_train_model(req: TrainRequest):
    """
    Train a scikit-learn model on pre-extracted features.
    """
    import pickle
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.metrics import accuracy_score, classification_report

    data_path = req.data_path
    cfg = FeatureConfig(**req.feature_config.dict())

    # Load pre-extracted features
    feature_dir = os.path.join(data_path, "features")
    X, y = [], []
    for pkl_file in os.listdir(feature_dir):
        if pkl_file.endswith(".pkl"):
            label = os.path.splitext(pkl_file)[0]
            with open(os.path.join(feature_dir, pkl_file), "rb") as f:
                feats = pickle.load(f)
            X.extend(feats)
            y.extend([label] * len(feats))

    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=req.test_split, random_state=42, stratify=y
    )

    if req.normalize:
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

    # Select classifier
    if req.model_type == "svm":
        clf = SVC(kernel="rbf", probability=True)
    elif req.model_type == "knn":
        clf = KNeighborsClassifier(n_neighbors=5)
    else:
        clf = RandomForestClassifier(n_estimators=100, random_state=42)

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    # Save model
    model_id = str(uuid.uuid4())[:8]
    model_dir = os.path.join(DATA_DIR, "models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, f"model_{model_id}.joblib")

    import joblib
    joblib.dump({"model": clf, "scaler": scaler if req.normalize else None,
                 "config": cfg.__dict__}, model_path)

    return {
        "model_id": model_id,
        "model_path": model_path,
        "accuracy": acc,
        "classification_report": report,
    }


# =====================================================================
#  Classify Audio (preserved from original)
# =====================================================================
@router.post("/classify-audio/")
async def classify_audio(
    file: UploadFile = File(...),
    sensor_id: str = Form("default"),
):
    """Classify a single audio file using the latest model."""
    import joblib
    model_dir = os.path.join(DATA_DIR, "models")
    if not os.path.exists(model_dir):
        return JSONResponse(status_code=400,
                            content={"error": "No trained model found"})

    # Load latest model
    models = sorted(Path(model_dir).glob("model_*.joblib"))
    if not models:
        return JSONResponse(status_code=400,
                            content={"error": "No trained model found"})

    bundle = joblib.load(models[-1])
    clf = bundle["model"]
    scaler = bundle.get("scaler")
    cfg_dict = bundle.get("config", {})
    cfg = FeatureConfig(**cfg_dict)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        features = extract_features(tmp_path, config=cfg)
        if features is None:
            return JSONResponse(status_code=400,
                                content={"error": "Feature extraction failed"})
        X = features.reshape(1, -1)
        if scaler is not None:
            X = scaler.transform(X)

        prediction = clf.predict(X)[0]
        confidence = 1.0
        if hasattr(clf, "predict_proba"):
            confidence = float(np.max(clf.predict_proba(X)))

        return {
            "sensor_id": sensor_id,
            "prediction": prediction,
            "confidence": confidence,
        }
    finally:
        os.unlink(tmp_path)


# =====================================================================
#  M5 Application Layer — Anomaly Detection, Clustering, Scene Analysis
# =====================================================================

class AnomalyDetectionRequest(BaseModel):
    """Detect anomalous audio samples from pre-extracted features."""
    features: List[List[float]]
    method: str = "isolation_forest"   # 'isolation_forest' | 'one_class_svm'
    threshold: float = -0.5
    contamination: float = 0.1
    model_path: Optional[str] = None

class ClusteringRequest(BaseModel):
    """Cluster audio samples by feature similarity."""
    features: List[List[float]]
    method: str = "kmeans"  # 'kmeans' | 'dbscan' | 'hierarchical'
    n_clusters: int = 5
    parameters: Optional[dict] = None

class SceneAnalysisRequest(BaseModel):
    time_resolution: float = 1.0
    spatial_analysis: bool = False
    event_detection: bool = True


@router.post("/m5-application/classify")
async def api_m5_classify(
    file: UploadFile = File(...),
    sensor_id: str = Form("default"),
):
    """
    M5 application-level audio classification.
    Wraps the classify-audio logic for the applicationService.ts frontend.
    """
    import joblib as jl
    model_dir = os.path.join(DATA_DIR, "models")
    if not os.path.exists(model_dir):
        return JSONResponse(status_code=400,
                            content={"error": "No trained model found"})
    models = sorted(Path(model_dir).glob("model_*.joblib"))
    if not models:
        return JSONResponse(status_code=400,
                            content={"error": "No trained model found"})

    bundle = jl.load(models[-1])
    clf = bundle["model"]
    scaler = bundle.get("scaler")
    cfg_dict = bundle.get("config", {})
    cfg = FeatureConfig(**cfg_dict)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        features = extract_features(tmp_path, config=cfg)
        if features is None:
            return JSONResponse(status_code=400,
                                content={"error": "Feature extraction failed"})
        X = features.reshape(1, -1)
        if scaler is not None:
            X = scaler.transform(X)

        prediction = clf.predict(X)[0]
        confidence = 1.0
        if hasattr(clf, "predict_proba"):
            confidence = float(np.max(clf.predict_proba(X)))

        # Get all class probabilities if available
        class_probs = {}
        if hasattr(clf, "predict_proba") and hasattr(clf, "classes_"):
            probs = clf.predict_proba(X)[0]
            class_probs = {str(c): float(p) for c, p in zip(clf.classes_, probs)}

        return {
            "classifications": [{
                "label": prediction,
                "confidence": confidence,
                "class_probabilities": class_probs,
            }],
            "sensor_id": sensor_id,
        }
    finally:
        os.unlink(tmp_path)


@router.post("/m5-application/anomaly-detection")
async def api_anomaly_detection(req: AnomalyDetectionRequest):
    """Detect anomalous audio samples using unsupervised methods."""
    try:
        X = np.array(req.features)
        result = detect_anomalies(
            X,
            method=req.method,
            threshold=req.threshold,
            contamination=req.contamination,
            model_path=req.model_path,
        )
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/m5-application/clustering")
async def api_clustering(req: ClusteringRequest):
    """Cluster audio samples by feature similarity."""
    try:
        X = np.array(req.features)
        result = cluster_audio(
            X,
            method=req.method,
            n_clusters=req.n_clusters,
            parameters=req.parameters,
        )
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/m5-application/scene-analysis")
async def api_scene_analysis(
    file: UploadFile = File(...),
    config_json: str = Form("{}"),
):
    """Combined scene analysis: frequency bands + anomaly + event detection."""
    try:
        params = json.loads(config_json)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        audio, sr = librosa.load(tmp_path, sr=None)
        os.unlink(tmp_path)

        result = analyze_scene(
            audio, sr,
            time_resolution=params.get("time_resolution", 1.0),
        )
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# =====================================================================
#  Preprocessing — Chunking, Sliding Window, Noise Reduction
# =====================================================================

class ChunkAudioRequest(BaseModel):
    input_dir: str
    output_dir: str
    min_duration_ms: int = 3000

class SlidingWindowRequest(BaseModel):
    window_size: float = 1.0   # seconds
    step: float = 0.5          # seconds

class NoiseReductionRequest(BaseModel):
    input_dir: str
    output_dir: str

class QualityFilterRequest(BaseModel):
    input_dir: str
    output_dir: str
    min_duration: float = 0.5
    max_duration: float = 10.0
    min_rms: float = 0.001
    snr_threshold: float = 5.0


@router.post("/data/chunk-audio")
async def api_chunk_audio(req: ChunkAudioRequest):
    """Split audio files on click/silence boundaries."""
    try:
        os.makedirs(req.output_dir, exist_ok=True)
        chunk_all_files(req.input_dir, req.output_dir)
        count = sum(1 for f in Path(req.output_dir).rglob("*") if f.is_file())
        return {"status": "success", "output_dir": req.output_dir,
                "files_created": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/data/sliding-window")
async def api_sliding_window(
    file: UploadFile = File(...),
    window_size: float = Form(1.0),
    step: float = Form(0.5),
):
    """Segment a single audio file into overlapping windows."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        audio, sr = librosa.load(tmp_path, sr=SAMPLE_RATE)
        os.unlink(tmp_path)

        windows = list(sliding_window(audio, window_size=window_size, step=step))
        return {
            "n_windows": len(windows),
            "window_size_seconds": window_size,
            "step_seconds": step,
            "sample_rate": SAMPLE_RATE,
            "samples_per_window": int(window_size * SAMPLE_RATE),
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/data/noise-reduction")
async def api_noise_reduction(req: NoiseReductionRequest):
    """Apply noise reduction to all audio files in a directory."""
    try:
        from M2_processing.augmentation.adjust_pitch import reduce_strong_noise
        import soundfile as sf

        src = Path(req.input_dir)
        dst = Path(req.output_dir)
        dst.mkdir(parents=True, exist_ok=True)
        processed = 0
        audio_exts = {".wav", ".mp3", ".flac", ".ogg"}

        for f in src.rglob("*"):
            if f.suffix.lower() not in audio_exts:
                continue
            audio, sr = librosa.load(str(f), sr=None)
            cleaned = reduce_strong_noise(audio, sr)
            out_path = dst / f.name
            sf.write(str(out_path), cleaned, sr)
            processed += 1

        return {"status": "success", "output_dir": req.output_dir,
                "files_processed": processed}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/data/quality-filter")
async def api_quality_filter(req: QualityFilterRequest):
    """Run quality filtering (without augmentation) on a dataset."""
    try:
        cfg = FilterConfig(
            min_duration=req.min_duration,
            max_duration=req.max_duration,
            min_rms=req.min_rms,
            snr_threshold=req.snr_threshold,
        )
        report = filter_dataset(req.input_dir, req.output_dir, cfg)
        return {"status": "success", "filter_report": report}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# =====================================================================
#  Dataset Management — Splits, Rename, Source Separation
# =====================================================================

class OrganizeSplitsRequest(BaseModel):
    input_dir: str
    output_dir: str
    test_size: float = 0.15
    val_size: float = 0.15
    random_state: int = 42

class RenameClassRequest(BaseModel):
    directory_class_map: dict        # {source_dir: class_name}
    output_base_path: str

class ListAudioDirsRequest(BaseModel):
    base_path: str


@router.post("/data/organize-splits")
async def api_organize_splits(req: OrganizeSplitsRequest):
    """Split dataset into train/validation/test sets."""
    try:
        organize_samples(
            req.input_dir, req.output_dir,
            test_size=req.test_size,
            val_size=req.val_size,
            random_state=req.random_state,
        )
        # Count files per split
        splits = {}
        for split in ["train", "validation", "test"]:
            split_dir = os.path.join(req.output_dir, split)
            if os.path.exists(split_dir):
                count = sum(1 for f in Path(split_dir).rglob("*") if f.is_file())
                splits[split] = count
        return {"status": "success", "output_dir": req.output_dir,
                "splits": splits}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/data/rename-class")
async def api_rename_class(req: RenameClassRequest):
    """Map directories to class names and copy audio files."""
    try:
        result = rename_and_copy(req.directory_class_map, req.output_base_path)
        return {"status": "success", "classes": result,
                "total_files": sum(result.values())}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/data/list-audio-dirs")
async def api_list_audio_dirs(req: ListAudioDirsRequest):
    """List directories containing audio files."""
    try:
        dirs = list_directories_with_audio(req.base_path)
        return {
            "directories": [
                {"path": d, "file_count": c} for d, c in dirs
            ]
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/processing/source-separation")
async def api_source_separation(
    file: UploadFile = File(...),
    n_components: int = Form(2),
):
    """Separate mixed audio into N sources using NMF."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        audio, sr = librosa.load(tmp_path, sr=None)
        os.unlink(tmp_path)

        sources = separate_sources(audio, n_components=n_components)

        # Return sources as base64-encoded WAV files
        import soundfile as sf
        encoded_sources = []
        for i, src_audio in enumerate(sources):
            buf = io.BytesIO()
            sf.write(buf, src_audio, sr, format="WAV")
            buf.seek(0)
            encoded_sources.append({
                "index": i,
                "audio_base64": base64.b64encode(buf.read()).decode(),
                "samples": len(src_audio),
            })

        return {
            "n_sources": len(sources),
            "sample_rate": sr,
            "sources": encoded_sources,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# =====================================================================
#  WebSocket – Real-time stream
# =====================================================================
@router.websocket("/ws/stream/{sensor_id}")
async def ws_stream(websocket: WebSocket, sensor_id: str):
    """
    Real-time WebSocket for audio classification and DOA.
    Client sends raw float32 audio bytes; server responds with
    classification and optional DOA results.
    """
    await websocket.accept()
    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            audio = np.frombuffer(audio_bytes, dtype=np.float32)

            if len(audio) < 1024:
                await websocket.send_json({
                    "sensor_id": sensor_id,
                    "message": "Audio chunk too short",
                })
                continue

            # Quick feature extraction (default config)
            with tempfile.NamedTemporaryFile(suffix=".wav",
                                             delete=False) as tmp:
                import soundfile as sf
                sf.write(tmp.name, audio, SAMPLE_RATE)
                features = extract_features(tmp.name)
                os.unlink(tmp.name)

            if features is not None:
                await websocket.send_json({
                    "sensor_id": sensor_id,
                    "features_length": len(features),
                    "message": "Features extracted (no model loaded)",
                })
            else:
                await websocket.send_json({
                    "sensor_id": sensor_id,
                    "message": "Audio below threshold or extraction failed",
                })
    except WebSocketDisconnect:
        print(f"[WS] Sensor {sensor_id} disconnected")
