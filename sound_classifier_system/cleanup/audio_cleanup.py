import numpy as np

DECIBEL_THRESHOLD = -110  # dB threshold

def check_audio_level(audio_data, threshold=DECIBEL_THRESHOLD):
    """
    Checks if the audio's RMS (converted to decibels) is above the threshold.
    """
    rms = np.sqrt(np.mean(np.square(audio_data)))
    decibel = 20 * np.log10(rms + 1e-6)  # Avoid log(0)
    return decibel > threshold
