from fastapi import APIRouter, UploadFile, File, Form, WebSocket, WebSocketDisconnect
import numpy as np
import librosa

from models.model_manager import load_model
from processing.feature_extraction import extract_features
from processing.source_separation import separate_sources
from cleanup.audio_cleanup import check_audio_level
from doppler.doppler import calculate_velocity
from acquisitions.audio_recorder import async_record_audio

SAMPLE_RATE = 44100
CHUNK_DURATION = 3

# Load the model globally for API endpoints
model = load_model()

router = APIRouter()

@router.post("/classify-audio/")
async def classify_audio(
    file: UploadFile = File(...),
    sensor_id: str = Form(...)
):
    """
    Classifies audio by first separating sound sources using NMF.
    Returns predictions for each separated source along with the sensor identifier.
    """
    audio_data, _ = librosa.load(file.file, sr=SAMPLE_RATE)
    if len(audio_data) < CHUNK_DURATION * SAMPLE_RATE:
        return {"error": "Audio chunk too short.", "sensor_id": sensor_id}
    
    # Separate mixed audio into distinct sources
    sources = separate_sources(audio_data)
    predictions = []
    for source in sources:
        if check_audio_level(source):
            features = extract_features(source, SAMPLE_RATE)
            prediction = model.predict(features.reshape(1, -1))[0]
            predictions.append(prediction)
    
    return {"sensor_id": sensor_id, "predictions": predictions}

@router.post("/calculate-velocity/")
async def velocity_analysis(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    sensor_id: str = Form(...),
    source_frequency: float = Form(1000.0)
):
    """
    Calculates object velocity using two audio chunks.
    Accepts a sensor_id for multi-sensor tracking.
    """
    chunk1, _ = librosa.load(file1.file, sr=SAMPLE_RATE)
    chunk2, _ = librosa.load(file2.file, sr=SAMPLE_RATE)
    
    if len(chunk1) != len(chunk2):
        return {"error": "Audio chunks must be of equal length.", "sensor_id": sensor_id}
    
    velocity = calculate_velocity(chunk1, chunk2, SAMPLE_RATE, source_frequency)
    return {"sensor_id": sensor_id, "velocity": velocity}

@router.websocket("/ws/audio/{sensor_id}")
async def websocket_audio(websocket, sensor_id: str):
    """
    WebSocket endpoint that receives audio bytes from a sensor,
    performs classification and, if possible, Doppler velocity estimation.
    """
    await websocket.accept()
    previous_audio = None
    SOURCE_FREQUENCY = 1000.0  # Default for Doppler estimation

    try:
        while True:
            # Expecting audio data as bytes (float32)
            audio_bytes = await websocket.receive_bytes()
            audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
            
            if check_audio_level(audio_data):
                features = extract_features(audio_data, SAMPLE_RATE)
                features_reshaped = features.reshape(1, -1)
                prediction = model.predict(features_reshaped)
                confidence = 1.0
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(features_reshaped)
                    confidence = float(np.max(proba))
                
                response = {
                    "sensor_id": sensor_id,
                    "prediction": prediction[0],
                    "confidence": confidence
                }
                
                # Calculate Doppler velocity if a previous chunk exists
                if previous_audio is not None and len(previous_audio) == len(audio_data):
                    velocity = calculate_velocity(previous_audio, audio_data, SAMPLE_RATE, SOURCE_FREQUENCY)
                    response["velocity"] = velocity
                else:
                    response["velocity"] = "Not enough data for velocity estimation"
                
                await websocket.send_json(response)
                previous_audio = audio_data
            else:
                await websocket.send_json({"sensor_id": sensor_id, "message": "Audio below threshold."})
    except WebSocketDisconnect:
        print(f"Sensor {sensor_id} disconnected.")
