import os
from pydub import AudioSegment
import numpy as np

def split_audio_on_clicks(audio_path, output_prefix, min_duration=3000):
    audio = AudioSegment.from_file(audio_path)
    samples = np.array(audio.get_array_of_samples())
    sample_rate = audio.frame_rate
    changes = np.diff(samples)
    threshold = np.mean(np.abs(changes)) + 2 * np.std(np.abs(changes))
    clicks = np.where(np.abs(changes) > threshold)[0]
    start = 0
    chunk_count = 1
    for click in clicks:
        end = click / sample_rate * 1000  # in milliseconds
        chunk = audio[start:end]
        if len(chunk) >= min_duration and chunk.dBFS > -50:
            if audio_path.lower().endswith('.mp3'):
                print(f"Generating chunk: {output_prefix}_{chunk_count}.mp3")
                chunk.export(f"{output_prefix}_{chunk_count}.mp3", format="mp3")
            elif audio_path.lower().endswith('.wav'):
                print(f"Generating chunk: {output_prefix}_{chunk_count}.wav")
                chunk.export(f"{output_prefix}_{chunk_count}.wav", format="wav")
            chunk_count += 1
        start = end
    chunk = audio[start:]
    if len(chunk) >= min_duration and chunk.dBFS > -50:
        chunk.export(f"{output_prefix}_{chunk_count}.mp3", format="mp3")

def process_all_files(input_folder, output_folder):
    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith(('.mp3', '.wav')):
            file_path = os.path.join(input_folder, file_name)
            base_name = os.path.splitext(file_name)[0]
            output_prefix = os.path.join(output_folder, f"{base_name}_chunk")
            split_audio_on_clicks(file_path, output_prefix)

if __name__ == "__main__":
    input_folder = "../../sound_data/raw"
    output_folder = "../../sound_data/chunked"
    os.makedirs(output_folder, exist_ok=True)
    process_all_files(input_folder, output_folder)
