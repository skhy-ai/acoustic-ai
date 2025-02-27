import os
import joblib
from dotenv import load_dotenv

load_dotenv()

MODEL_FILE = os.getenv("SOUND_MODEL")
if not MODEL_FILE:
    raise EnvironmentError("SOUND_MODEL environment variable not defined.")

def load_model():
    """Loads the ML model from disk."""
    print("Loading model...")
    model = joblib.load(MODEL_FILE)
    print("Model loaded successfully.")
    return model
