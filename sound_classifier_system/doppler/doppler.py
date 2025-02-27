import numpy as np
from scipy.signal import correlate

def calculate_velocity(chunk1, chunk2, sample_rate, source_frequency):
    """
    Calculates object velocity based on the Doppler shift.
    """
    correlation = correlate(chunk1, chunk2)
    delay = np.argmax(correlation) - len(chunk1)
    frequency_shift = delay * sample_rate / len(chunk1)
    speed_of_sound = 343  # Speed of sound in air (m/s)
    velocity = (speed_of_sound * frequency_shift) / source_frequency
    return velocity
