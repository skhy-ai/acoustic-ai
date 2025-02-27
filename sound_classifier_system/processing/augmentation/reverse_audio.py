import os
from pydub import AudioSegment

def reverse_audio(audio_path, output_path):
    audio = AudioSegment.from_file(audio_path)
    reversed_audio = audio.reverse()
    reversed_audio.export(output_path, format="mp3")

def process_all_files(input_folder, output_folder):
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.mp3') or file_name.endswith('.wav'):
            file_path = os.path.join(input_folder, file_name)
            output_file_name = os.path.splitext(file_name)[0] + "_reversed.mp3"
            output_path = os.path.join(output_folder, output_file_name)
            reverse_audio(file_path, output_path)

if __name__ == "__main__":
    input_folder = "../sound_data/filtered"
    output_folder = "../sound_data/filtered_reverse"
    os.makedirs(output_folder, exist_ok=True)
    process_all_files(input_folder, output_folder)