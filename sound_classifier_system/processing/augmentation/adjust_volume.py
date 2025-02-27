import os
from pydub import AudioSegment

def adjust_volume(audio_path, output_prefix, decibel_change):
    audio = AudioSegment.from_file(audio_path)
    adjusted_audio = audio + decibel_change
    output_path = f"{output_prefix}_{decibel_change:+d}dB.mp3"
    adjusted_audio.export(output_path, format="mp3")

def process_all_files(input_folder, output_folder):
    decibel_changes = [+10, +20, -10, -20]
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.mp3') or file_name.endswith('.wav'):
            file_path = os.path.join(input_folder, file_name)
            base_name = os.path.splitext(file_name)[0]
            for decibel_change in decibel_changes:
                output_prefix = os.path.join(output_folder, base_name)
                adjust_volume(file_path, output_prefix, decibel_change)

if __name__ == "__main__":
    input_folder = "../sound_data/filtered"
    output_folder = "../sound_data/volume_adjusted"
    os.makedirs(output_folder, exist_ok=True)
    process_all_files(input_folder, output_folder)
