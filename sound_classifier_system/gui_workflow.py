import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import librosa
import librosa.display
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# File dialogs
from tkinter.filedialog import askopenfilename, askdirectory

# Import actual modules (update with your real module paths)
from acquisitions.dataset_download.unified import download_soundata_dataset
from acquisitions.youtube.playlist import save_playlist_urls
from acquisitions.youtube.download import download_audio
from processing.feature_extraction import extract_features
from processing.augmentation.adjust_pitch import process_all_files as process_pitch
from processing.augmentation.adjust_volume import process_all_files as process_volume
from processing.augmentation.reverse_audio import process_all_files as process_reverse
from processing.segmentation.generate_chunks import process_all_files as generate_audio_chunks
from processing.cleanup import validate_audio_samples
from processing.sliding_window import sliding_window
from processing.source_separation import separate_sources
from processing.data_preparation.metadata_based_class_creation import copy_files_to_class_directories, find_audio_files
from processing.data_preparation.organize_sound_samples import organize_samples
from processing.data_preparation.rename_class import copy_files_to_directory
from reports.generate_reports import generate_sampled_data_report, generate_dataset_report

# --- Directory Setup ---
BASE_DIR = os.path.abspath("sound_classifier_system")
SOUND_CHUNKED_DIR = os.path.join(BASE_DIR, "sound_data", "chunked")
SOUND_FILTERED_DIR = os.path.join(BASE_DIR, "sound_data", "filtered")
SOUND_PITCH_DIR = os.path.join(BASE_DIR, "sound_data", "pitch_adjusted")
SOUND_VOLUME_DIR = os.path.join(BASE_DIR, "sound_data", "volume_adjusted")
SOUND_REVERSED_DIR = os.path.join(BASE_DIR, "sound_data", "filtered_reverse")
SOUND_PROCESSED_DIR = os.path.join(BASE_DIR, "sound_data", "processed")
SAMPLED_DATA_DIR = os.path.join(BASE_DIR, "sampled_data")
SOUND_DATASET_DIR = os.path.join(BASE_DIR, "sound_dataset")

# Ensure directories exist
for d in [BASE_DIR, SOUND_CHUNKED_DIR, SOUND_FILTERED_DIR, SOUND_PITCH_DIR, SOUND_VOLUME_DIR,
          SOUND_REVERSED_DIR, SOUND_PROCESSED_DIR, SAMPLED_DATA_DIR, SOUND_DATASET_DIR]:
    os.makedirs(d, exist_ok=True)

# --- Functional Implementations ---
def download_dataset():
    download_soundata_dataset()
    messagebox.showinfo("Acquisitions", "Dataset downloaded and stored in acquisitions/dataset_download")

def download_youtube_playlist():
    save_playlist_urls()
    messagebox.showinfo("Acquisitions", "YouTube playlist URLs saved in acquisitions/youtube")

def download_youtube_video():
    download_audio()
    messagebox.showinfo("Acquisitions", "YouTube video downloaded and saved in acquisitions/youtube")

def process_feature_extraction_file():
    file_path = askopenfilename(title="Select Audio File for Feature Extraction", 
                                filetypes=[("Audio Files", "*.wav *.mp3")])
    if file_path:
        feature = extract_features(file_path)
        if feature is not None:
            messagebox.showinfo("Processing", f"Feature extraction complete.\nFeature vector length: {len(feature)}")
        else:
            messagebox.showerror("Processing", "Feature extraction failed.")
    else:
        messagebox.showwarning("Processing", "No file selected.")

def process_augmentation():
    process_pitch(SOUND_FILTERED_DIR, SOUND_PITCH_DIR)
    process_volume(SOUND_FILTERED_DIR, SOUND_VOLUME_DIR)
    process_reverse(SOUND_FILTERED_DIR, SOUND_REVERSED_DIR)
    messagebox.showinfo("Processing", "Audio augmentation completed: pitch, volume, and reversal adjustments applied.")

def process_segmentation():
    generate_audio_chunks(SOUND_FILTERED_DIR, SOUND_CHUNKED_DIR)
    messagebox.showinfo("Processing", "Audio segmentation completed and stored in sound_data/chunked")

def process_sliding_window_file():
    file_path = askopenfilename(title="Select Audio File for Sliding Window", 
                                filetypes=[("Audio Files", "*.wav *.mp3")])
    if file_path:
        y, sr = librosa.load(file_path, sr=44100)
        windows = list(sliding_window(y))
        messagebox.showinfo("Processing", f"Sliding window applied. {len(windows)} windows generated for {os.path.basename(file_path)}")
    else:
        messagebox.showwarning("Processing", "No file selected.")

def process_source_separation_file():
    file_path = askopenfilename(title="Select Audio File for Source Separation", 
                                filetypes=[("Audio Files", "*.wav *.mp3")])
    if file_path:
        y, _ = librosa.load(file_path, sr=44100)
        sources = separate_sources(y)
        messagebox.showinfo("Processing", f"Source separation applied. {len(sources)} sources extracted for {os.path.basename(file_path)}")
    else:
        messagebox.showwarning("Processing", "No file selected.")

def validate_samples():
    validate_audio_samples()
    messagebox.showinfo("Validation", "Audio samples validated and cleaned in processing/cleanup")

def generate_sampled_report():
    generate_sampled_data_report()
    messagebox.showinfo("Reports", "Sampled data report generated in reports/")

def generate_dataset_report():
    generate_dataset_report()
    messagebox.showinfo("Reports", "Sound dataset report generated in reports/")

def create_classes_from_metadata():
    metadata_file = askopenfilename(title="Select Metadata CSV File", filetypes=[("CSV Files", "*.csv")])
    if not metadata_file:
        messagebox.showwarning("Data Preparation", "No metadata file selected.")
        return
    audio_base_dir = askdirectory(title="Select Base Directory for Audio Files")
    if not audio_base_dir:
        messagebox.showwarning("Data Preparation", "No audio base directory selected.")
        return
    # Ask user for file extension
    file_ext = simpledialog.askstring("Data Preparation", "Enter file extension (.wav or .mp3):", initialvalue=".wav")
    if file_ext not in ['.wav', '.mp3']:
        messagebox.showerror("Data Preparation", "Invalid file extension.")
        return
    audio_files = find_audio_files(audio_base_dir, file_ext)
    if not audio_files:
        messagebox.showerror("Data Preparation", f"No audio files with extension {file_ext} found in {audio_base_dir}.")
        return
    copy_files_to_class_directories(metadata_file, audio_files, SAMPLED_DATA_DIR)
    messagebox.showinfo("Data Preparation", "Classes created based on metadata.")

def organize_dataset():
    organize_samples(SAMPLED_DATA_DIR, SOUND_DATASET_DIR)
    messagebox.showinfo("Data Preparation", "Sound samples organized into training, validation, and test sets.")

def rename_classes():
    source_dir = askdirectory(title="Select Directory to Rename Classes")
    if not source_dir:
        messagebox.showwarning("Data Preparation", "No directory selected.")
        return
    # Ask for file extension to process
    file_ext = simpledialog.askstring("Data Preparation", "Enter file extension (.wav or .mp3):", initialvalue=".wav")
    if file_ext not in ['.wav', '.mp3']:
        messagebox.showerror("Data Preparation", "Invalid file extension.")
        return
    copy_files_to_directory([source_dir], SAMPLED_DATA_DIR, file_ext)
    messagebox.showinfo("Data Preparation", "Classes renamed and structured.")

# --- Manual Filtering GUI ---
class AudioFilterGUI(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Manual Audio Chunk Filtering")
        self.geometry("900x600")
        self.audio_files = [os.path.join(SOUND_CHUNKED_DIR, f) for f in os.listdir(SOUND_CHUNKED_DIR) if f.endswith(('.wav', '.mp3'))]
        self.current_index = 0
        self.setup_widgets()
        if self.audio_files:
            self.display_current_file()
        else:
            messagebox.showinfo("Info", "No audio files found in the chunked folder.")
            self.destroy()

    def setup_widgets(self):
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        control_frame = ttk.Frame(self)
        control_frame.pack(side=tk.BOTTOM, pady=10)
        self.keep_button = ttk.Button(control_frame, text="Keep", command=self.keep_current)
        self.keep_button.pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(control_frame, text="Delete", command=self.delete_current)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        self.next_button = ttk.Button(control_frame, text="Next", command=self.next_file)
        self.next_button.pack(side=tk.LEFT, padx=5)

    def display_current_file(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        current_file = self.audio_files[self.current_index]
        y, sr = librosa.load(current_file, sr=None)
        D = librosa.stft(y)
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        fig, ax = plt.subplots(figsize=(8, 4))
        img = librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='log', ax=ax)
        ax.set_title(f"Spectrogram: {os.path.basename(current_file)}")
        fig.colorbar(img, ax=ax, format="%+2.f dB")
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        plt.close(fig)

    def keep_current(self):
        shutil.move(self.audio_files[self.current_index], SOUND_FILTERED_DIR)
        self.remove_current_file()

    def delete_current(self):
        os.remove(self.audio_files[self.current_index])
        self.remove_current_file()

    def remove_current_file(self):
        del self.audio_files[self.current_index]
        if self.audio_files:
            self.display_current_file()
        else:
            messagebox.showinfo("Done", "No more files to process.")
            self.destroy()

    def next_file(self):
        if self.current_index < len(self.audio_files) - 1:
            self.current_index += 1
            self.display_current_file()

# --- Main GUI Code ---
def main():
    root = tk.Tk()
    root.title("Sound Classifier System - End-to-End Workflow")
    root.geometry("1000x700")
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both")
    
    # Acquisitions Tab
    tab_acq = ttk.Frame(notebook)
    notebook.add(tab_acq, text="Acquisitions")
    ttk.Label(tab_acq, text="Acquisition Methods:", font=("Helvetica", 14)).pack(pady=10)
    ttk.Button(tab_acq, text="Download Dataset", command=download_dataset).pack(pady=5)
    ttk.Button(tab_acq, text="Download YouTube Playlist", command=download_youtube_playlist).pack(pady=5)
    ttk.Button(tab_acq, text="Download YouTube Video", command=download_youtube_video).pack(pady=5)
    
    # Processing Tab
    tab_proc = ttk.Frame(notebook)
    notebook.add(tab_proc, text="Processing")
    ttk.Label(tab_proc, text="Processing Options:", font=("Helvetica", 14)).pack(pady=10)
    ttk.Button(tab_proc, text="Feature Extraction", command=process_feature_extraction_file).pack(pady=5)
    ttk.Button(tab_proc, text="Augmentation", command=process_augmentation).pack(pady=5)
    ttk.Button(tab_proc, text="Segmentation", command=process_segmentation).pack(pady=5)
    ttk.Button(tab_proc, text="Sliding Window", command=process_sliding_window_file).pack(pady=5)
    ttk.Button(tab_proc, text="Source Separation", command=process_source_separation_file).pack(pady=5)
    
    # Validation Tab
    tab_valid = ttk.Frame(notebook)
    notebook.add(tab_valid, text="Validation")
    ttk.Label(tab_valid, text="Validation Options:", font=("Helvetica", 14)).pack(pady=10)
    ttk.Button(tab_valid, text="Validate Audio Samples", command=validate_samples).pack(pady=5)
    
    # Reports Tab
    tab_reports = ttk.Frame(notebook)
    notebook.add(tab_reports, text="Reports")
    ttk.Label(tab_reports, text="Report Generation:", font=("Helvetica", 14)).pack(pady=10)
    ttk.Button(tab_reports, text="Generate Sampled Report", command=generate_sampled_report).pack(pady=5)
    ttk.Button(tab_reports, text="Generate Dataset Report", command=generate_dataset_report).pack(pady=5)
    
    # Data Preparation Tab
    tab_data = ttk.Frame(notebook)
    notebook.add(tab_data, text="Data Preparation")
    ttk.Label(tab_data, text="Organize & Rename Data:", font=("Helvetica", 14)).pack(pady=10)
    ttk.Button(tab_data, text="Create Classes from Metadata", command=create_classes_from_metadata).pack(pady=5)
    ttk.Button(tab_data, text="Organize Dataset", command=organize_dataset).pack(pady=5)
    ttk.Button(tab_data, text="Rename Classes", command=rename_classes).pack(pady=5)
    
    # Manual Filtering Tab
    tab_filter = ttk.Frame(notebook)
    notebook.add(tab_filter, text="Manual Filtering")
    ttk.Button(tab_filter, text="Launch Filtering GUI", command=lambda: AudioFilterGUI(root)).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()

