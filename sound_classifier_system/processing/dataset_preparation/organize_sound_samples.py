import os
import shutil
from sklearn.model_selection import train_test_split

def organize_samples(input_dir, output_dir, test_size=0.15, val_size=0.15):
    for split in ['train', 'validation', 'test']:
        os.makedirs(os.path.join(output_dir, split), exist_ok=True)
    for class_name in os.listdir(input_dir):
        class_dir = os.path.join(input_dir, class_name)
        if not os.path.isdir(class_dir):
            continue
        audio_files = [f for f in os.listdir(class_dir) if f.lower().endswith(('.wav', '.mp3'))]
        train_files, test_files = train_test_split(audio_files, test_size=test_size + val_size, random_state=42)
        val_files, test_files = train_test_split(test_files, test_size=test_size/(test_size + val_size), random_state=42)
        for split, files in [('train', train_files), ('validation', val_files), ('test', test_files)]:
            split_class_dir = os.path.join(output_dir, split, class_name)
            os.makedirs(split_class_dir, exist_ok=True)
            for file in files:
                shutil.copy(os.path.join(class_dir, file), os.path.join(split_class_dir, file))
    print("Dataset organization complete!")

if __name__ == "__main__":
    input_directory = "../../sampled_data"
    output_directory = "../../sound_dataset"
    organize_samples(input_directory, output_directory)
