import os
import tkinter as tk
from tkinter import filedialog
import librosa
import soundfile as sf

def select_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    directory = filedialog.askdirectory(title="Select Directory to Clean Up")
    return directory

def clean_up_invalid_files(directory):
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith('.wav'):
                file_path = os.path.join(root, file_name)
                try:
                    # Attempt to load the audio file
                    audio, sample_rate = librosa.load(file_path, res_type='kaiser_fast')
                except Exception as e:
                    # Handle other exceptions
                    print(f"Error processing {file_path}: {e}")
                    print(f"Deleting invalid file: {file_path}")
                    os.remove(file_path)

def main():
    directory = select_directory()
    if directory:
        print(f"Selected directory: {directory}")
        clean_up_invalid_files(directory)
    else:
        print("No directory selected")

if __name__ == "__main__":
    main()
