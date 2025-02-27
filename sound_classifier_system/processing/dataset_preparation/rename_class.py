import os
import shutil

def list_directories_with_extension(base_path, extension):
    directories = []
    for root, _, files in os.walk(base_path):
        if any(file.endswith(extension) for file in files):
            directories.append(root)
    return directories

def copy_files_to_directory(source_dirs, dest_dir, extension):
    os.makedirs(dest_dir, exist_ok=True)
    for source_dir in source_dirs:
        for file_name in os.listdir(source_dir):
            if file_name.endswith(extension):
                full_file_name = os.path.join(source_dir, file_name)
                if os.path.isfile(full_file_name):
                    shutil.copy(full_file_name, dest_dir)

def main():
    base_path = "../../external_sound_data"
    output_base_path = "../../sampled_data"
    file_type = input("Enter the file type (.wav or .mp3): ").strip().lower()
    if file_type not in ['.wav', '.mp3']:
        print("Invalid file type.")
        return
    directories = list_directories_with_extension(base_path, file_type)
    if not directories:
        print(f"No directories found containing {file_type} files.")
        return
    print("Select directories to include in the sampled data:")
    for idx, directory in enumerate(directories):
        print(f"{idx + 1}. {directory}")
    selected_indices = input("Enter numbers separated by commas: ").strip()
    selected_indices = [int(idx) - 1 for idx in selected_indices.split(',') if idx.isdigit()]
    selected_dirs = [directories[idx] for idx in selected_indices if 0 <= idx < len(directories)]
    for directory in selected_dirs:
        dir_name = os.path.basename(directory)
        class_name = input(f"Enter the class name for '{dir_name}': ").strip() or dir_name
        output_dir = os.path.join(output_base_path, class_name)
        copy_files_to_directory([directory], output_dir, file_type)
        print(f"Copied files from {directory} to {output_dir}")
    
if __name__ == "__main__":
    main()
