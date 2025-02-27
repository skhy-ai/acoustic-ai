import os
import numpy as np
import librosa
import pickle
import gc

def extract_features(file_path):
    try:
        audio, sample_rate = librosa.load(file_path, res_type='kaiser_fast')
        n_fft = min(1024, len(audio))
        mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40, n_fft=n_fft)
        chroma = librosa.feature.chroma_stft(y=audio, sr=sample_rate, n_fft=n_fft)
        mel = librosa.feature.melspectrogram(y=audio, sr=sample_rate, n_fft=n_fft)
        contrast = librosa.feature.spectral_contrast(y=audio, sr=sample_rate, n_fft=n_fft)
        tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(audio), sr=sample_rate)
        features = np.hstack([
            np.mean(mfccs, axis=1),
            np.mean(chroma, axis=1),
            np.mean(mel, axis=1),
            np.mean(contrast, axis=1),
            np.mean(tonnetz, axis=1)
        ])
        return features
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def extract_and_save_features(data_path, feature_folder='../../features'):
    os.makedirs(feature_folder, exist_ok=True)
    for label in os.listdir(data_path):
        label_path = os.path.join(data_path, label)
        feature_file = os.path.join(feature_folder, f'{label}.pkl')
        if os.path.exists(feature_file):
            print(f"Features for class '{label}' already exist. Skipping extraction.")
        else:
            if os.path.isdir(label_path):
                features = []
                for file in os.listdir(label_path):
                    file_path = os.path.join(label_path, file)
                    feature = extract_features(file_path)
                    if feature is not None:
                        features.append(feature)
                with open(feature_file, 'wb') as f:
                    pickle.dump(features, f)
                print(f"Features for class '{label}' saved to {feature_file}")
                del features
                gc.collect()

if __name__ == "__main__":
    data_path = '../../sampled_data/'
    extract_and_save_features(data_path)
