import os
from pydub import AudioSegment
import numpy as np
import pyrubberband as pyrb
import noisereduce as nr

def change_pitch(audio, sample_rate, semitones):
    samples = np.array(audio.get_array_of_samples())
    shifted_samples = pyrb.pitch_shift(samples, sample_rate, semitones)
    return AudioSegment(
        shifted_samples.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio.sample_width,
        channels=audio.channels
    )

def reduce_noise(audio):
    samples = np.array(audio.get_array_of_samples())
    try:
        reduced_noise_samples = nr.reduce_noise(y=samples, sr=audio.frame_rate)
        return AudioSegment(
            reduced_noise_samples.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=audio.channels
        )
    except Exception as e:
        print(f"Noise reduction failed: {e}")
        return audio  # Return the original audio if noise reduction fails

def adjust_pitch_and_volume(audio_path, output_prefix, pitch_changes):
    audio = AudioSegment.from_file(audio_path)
    sample_rate = audio.frame_rate
    for pitch_change in pitch_changes:
        semitones = pitch_change / 100.0  # Convert Hz change to semitones
        adjusted_audio = change_pitch(audio, sample_rate, semitones)
        noise_reduced_audio = reduce_noise(adjusted_audio)
        output_path = f"{output_prefix}_{pitch_change:+d}Hz.mp3"
        noise_reduced_audio.export(output_path, format="mp3")

def process_all_files(input_folder, output_folder):
    pitch_changes = [-50, -100, -150, -200, -250]
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.mp3') or file_name.endswith('.wav'):
            file_path = os.path.join(input_folder, file_name)
            base_name = os.path.splitext(file_name)[0]
            output_prefix = os.path.join(output_folder, base_name)
            adjust_pitch_and_volume(file_path, output_prefix, pitch_changes)

if __name__ == "__main__":
    input_folder = "../sound_data/filtered"
    output_folder = "../sound_data/pitch_adjusted"
    os.makedirs(output_folder, exist_ok=True)
    process_all_files(input_folder, output_folder)
import os
from pydub import AudioSegment
import numpy as np
import pyrubberband as pyrb
import noisereduce as nr

def change_pitch(audio, sample_rate, semitones):
    samples = np.array(audio.get_array_of_samples())
    shifted_samples = pyrb.pitch_shift(samples, sample_rate, semitones)
    return AudioSegment(
        shifted_samples.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio.sample_width,
        channels=audio.channels
    )

def reduce_noise(audio):
    samples = np.array(audio.get_array_of_samples())
    try:
        reduced_noise_samples = nr.reduce_noise(y=samples, sr=audio.frame_rate)
        return AudioSegment(
            reduced_noise_samples.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=audio.channels
        )
    except Exception as e:
        print(f"Noise reduction failed: {e}")
        return audio  # Return the original audio if noise reduction fails

def adjust_pitch_and_volume(audio_path, output_prefix, pitch_changes):
    audio = AudioSegment.from_file(audio_path)
    sample_rate = audio.frame_rate
    for pitch_change in pitch_changes:
        semitones = pitch_change / 100.0  # Convert Hz change to semitones
        adjusted_audio = change_pitch(audio, sample_rate, semitones)
        noise_reduced_audio = reduce_noise(adjusted_audio)
        output_path = f"{output_prefix}_{pitch_change:+d}Hz.mp3"
        noise_reduced_audio.export(output_path, format="mp3")

def process_all_files(input_folder, output_folder):
    pitch_changes = [-50, -100, -150, -200, -250]
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.mp3') or file_name.endswith('.wav'):
            file_path = os.path.join(input_folder, file_name)
            base_name = os.path.splitext(file_name)[0]
            output_prefix = os.path.join(output_folder, base_name)
            adjust_pitch_and_volume(file_path, output_prefix, pitch_changes)

if __name__ == "__main__":
    input_folder = "../sound_data/filtered"
    output_folder = "../sound_data/pitch_adjusted"
    os.makedirs(output_folder, exist_ok=True)
    process_all_files(input_folder, output_folder)
