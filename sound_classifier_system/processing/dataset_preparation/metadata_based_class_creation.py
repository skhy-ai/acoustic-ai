import os
import shutil
import pandas as pd

def find_audio_files(base_path, extension):
    audio_files = []
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(extension):
                audio_files.append(os.path.join(root, file))
    return audio_files

def copy_files_to_class_directories(metadata_file, audio_files, output_base_path):
    metadata = pd.read_csv(metadata_file)
    file_path_dict = {os.path.basename(file): file for file in audio_files}
    for _, row in metadata.iterrows():
        class_name = row['class']
        file_name = row['slice_file_name']
        source_file = file_path_dict.get(file_name)
        if source_file and os.path.isfile(source_file):
            class_dir = os.path.join(output_base_path, class_name)
            os.makedirs(class_dir, exist_ok=True)
            shutil.copy(source_file, class_dir)
            print(f"Copied {file_name} to {class_dir}")

def main():
    base_path = "../../external_sound_data"
    output_base_path = "../../sampled_data"
    metadata_file = input("Enter the path to the metadata file: ").strip()
    if not os.path.isfile(metadata_file):
        print("Invalid metadata file path.")
        return
    file_type = input("Enter the file type (.wav or .mp3): ").strip().lower()
    if file_type not in ['.wav', '.mp3']:
        print("Invalid file type.")
        return
    audio_files = find_audio_files(base_path, file_type)
    if not audio_files:
        print(f"No audio files found with extension {file_type} in {base_path}.")
        return
    copy_files_to_class_directories(metadata_file, audio_files, output_base_path)
    print(f"Files have been organized into {output_base_path}.")

if __name__ == "__main__":
    main()
