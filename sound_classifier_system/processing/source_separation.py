import librosa
import numpy as np
from librosa import decomposition

def separate_sources(audio_data, n_components=2):
    """
    Separates mixed audio into distinct sources using Non-negative Matrix Factorization (NMF).
    Returns a list of separated sources.
    """
    stft = librosa.stft(audio_data)
    magnitude, phase = librosa.magphase(stft)
    components, activations = decomposition.decompose(magnitude, n_components=n_components, sort=True)
    sources = []
    for i in range(n_components):
        source_stft = components[:, i:i+1] * activations[i:i+1, :]
        source = librosa.istft(source_stft * phase)
        sources.append(source)
    return sources
