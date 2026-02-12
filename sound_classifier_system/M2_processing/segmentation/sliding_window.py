SAMPLE_RATE = 44100

def sliding_window(audio, window_size=1.0, step=0.5):
    """
    Generator that yields overlapping audio windows.
    """
    samples_per_window = int(window_size * SAMPLE_RATE)
    step_samples = int(step * SAMPLE_RATE)
    for i in range(0, len(audio) - samples_per_window, step_samples):
        yield audio[i:i + samples_per_window]
