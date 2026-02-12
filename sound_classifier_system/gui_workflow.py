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
from pytube import Playlist
import pickle
import joblib
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
import webbrowser

# File dialogs
from tkinter.filedialog import askopenfilename, askdirectory

# Import your actual modules (update with your real module paths)
from acquisitions.dataset_download.unified import download_soundata_dataset
from acquisitions.youtube.playlist import save_playlist_urls
from acquisitions.youtube.download import download_audio
from processing.dataset_preparation.feature_extraction import extract_features
from processing.augmentation.adjust_pitch import process_all_files as process_pitch
from processing.augmentation.adjust_volume import process_all_files as process_volume
from processing.augmentation.reverse_audio import process_all_files as process_reverse
from processing.segmentation.generate_chunks import process_all_files as generate_audio_chunks
from cleanup.cleanup_invalid_files import clean_up_invalid_files as validate_audio_samples
from processing.segmentation.sliding_window import sliding_window
from processing.segmentation.source_separation import separate_sources
from processing.dataset_preparation.metadata_based_class_creation import copy_files_to_class_directories, find_audio_files
from processing.dataset_preparation.organize_sound_samples import organize_samples
from processing.dataset_preparation.rename_class import copy_files_to_directory
#from reports.generate_reports import generate_sampled_data_report, generate_dataset_report

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

for d in [BASE_DIR, SOUND_CHUNKED_DIR, SOUND_FILTERED_DIR, SOUND_PITCH_DIR, SOUND_VOLUME_DIR,
          SOUND_REVERSED_DIR, SOUND_PROCESSED_DIR, SAMPLED_DATA_DIR, SOUND_DATASET_DIR]:
    os.makedirs(d, exist_ok=True)

# --- Tooltip Class for Button Explanations ---
class CreateToolTip:
    """
    Create a tooltip for a given widget.
    """
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.showtip()

    def leave(self, event=None):
        self.hidetip()

    def showtip(self):
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 20
        y = y + cy + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# --- Helper for Logging and Error Handling ---
def log_message(message, error=False):
    """Insert a log message in the log panel."""
    tag = "ERROR" if error else "INFO"
    log_entry = f"[{tag}] {message}\n"
    log_text.config(state="normal")
    log_text.insert("end", log_entry)
    log_text.see("end")
    log_text.config(state="disabled")

def safe_run(func):
    """Wrap a callback so that errors are caught, logged, and shown to the user."""
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Error in {func.__name__}: {str(e)}"
            log_message(error_msg, error=True)
            messagebox.showerror("Error", error_msg)
    return wrapper

# --- Functional Implementations (existing functions remain unchanged) ---
def download_dataset():
    dataset_name = simpledialog.askstring("Download Dataset",
                                            "Enter the dataset name (e.g., urbansound8k, esc50, gtzan):")
    if not dataset_name:
        messagebox.showwarning("Input Error", "Dataset name is required.")
        return

    data_home = filedialog.askdirectory(title="Select Directory to Store Dataset")
    if not data_home:
        messagebox.showwarning("Input Error", "You must select a directory to store the dataset.")
        return

    download_soundata_dataset(dataset_name, data_home)
    messagebox.showinfo("Acquisitions", f"{dataset_name} dataset downloaded to {data_home}")

def download_youtube_playlist():
    playlist_url = simpledialog.askstring("Download YouTube Playlist", "Enter the YouTube Playlist URL:")
    if not playlist_url:
        messagebox.showwarning("Input Error", "Playlist URL is required.")
        return

    output_file = filedialog.asksaveasfilename(defaultextension=".txt",
                                               title="Save Playlist URLs",
                                               filetypes=[("Text Files", "*.txt")])
    if not output_file:
        messagebox.showwarning("Input Error", "You must select an output file to save the URLs.")
        return

    save_playlist_urls(playlist_url, output_file)

def download_youtube_video():
    video_url = simpledialog.askstring("Download YouTube Video", "Enter the YouTube Video URL:")
    if not video_url:
        messagebox.showwarning("Input Error", "Video URL is required.")
        return

    output_file = filedialog.asksaveasfilename(defaultextension=".mp3",
                                               title="Save Video Audio",
                                               filetypes=[("MP3 Files", "*.mp3"), ("WAV Files", "*.wav")])
    if not output_file:
        messagebox.showwarning("Input Error", "You must select an output file to save the audio.")
        return

    download_audio(video_url, output_file)
    messagebox.showinfo("Acquisitions", "Video audio downloaded successfully.")

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
    file_ext = simpledialog.askstring("Data Preparation", "Enter file extension (.wav or .mp3):", initialvalue=".wav")
    if file_ext not in ['.wav', '.mp3']:
        messagebox.showerror("Data Preparation", "Invalid file extension.")
        return
    copy_files_to_directory([source_dir], SAMPLED_DATA_DIR, file_ext)
    messagebox.showinfo("Data Preparation", "Classes renamed and structured.")

# --- New Functions for Model Building and API Connection ---
def build_model():
    feature_folder = filedialog.askdirectory(title="Select Feature Folder")
    if not feature_folder:
        messagebox.showwarning("Model Building", "No feature folder selected.")
        return

    class_files = [f for f in os.listdir(feature_folder) if f.endswith('.pkl')]
    if not class_files:
        messagebox.showerror("Model Building", "No feature files (.pkl) found in the selected folder.")
        return

    classes_message = "Available classes:\n"
    for idx, file in enumerate(class_files):
        classes_message += f"{idx + 1}. {os.path.splitext(file)[0]}\n"
    messagebox.showinfo("Available Classes", classes_message)

    indices_str = simpledialog.askstring("Select Classes", "Enter the numbers of the classes to use (comma separated):")
    if not indices_str:
        messagebox.showwarning("Model Building", "No classes selected.")
        return
    try:
        selected_indices = [int(idx.strip()) - 1 for idx in indices_str.split(",")]
    except Exception as e:
        messagebox.showerror("Model Building", "Invalid input for class indices.")
        return

    def load_features(feature_folder, selected_indices):
        features = []
        labels = []
        class_files_local = [f for f in os.listdir(feature_folder) if f.endswith('.pkl')]
        try:
            filtered_files = [class_files_local[i] for i in selected_indices]
        except IndexError:
            messagebox.showerror("Model Building", "One or more class indices are out of range.")
            return None, None
        for file in filtered_files:
            class_name = os.path.splitext(file)[0]
            with open(os.path.join(feature_folder, file), 'rb') as f:
                class_features = pickle.load(f)
                features.extend(class_features)
                labels.extend([class_name] * len(class_features))
        return np.array(features), np.array(labels)

    X, y = load_features(feature_folder, selected_indices)
    if X is None or y is None:
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    num_neighbors_str = simpledialog.askstring("KNN Parameter", "Enter the number of neighbors for KNN (default 5):")
    try:
        num_neighbors = int(num_neighbors_str) if num_neighbors_str and num_neighbors_str.strip() != "" else 5
    except:
        num_neighbors = 5

    svm_clf = SVC(kernel='linear', probability=True)
    rf_clf = RandomForestClassifier(n_estimators=100, random_state=42)
    knn_clf = KNeighborsClassifier(n_neighbors=num_neighbors)

    ensemble_clf = VotingClassifier(estimators=[
        ('svm', svm_clf),
        ('rf', rf_clf),
        ('knn', knn_clf)
    ], voting='soft')

    ensemble_clf.fit(X_train, y_train)
    y_pred = ensemble_clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    msg = f"Ensemble classifier built with accuracy: {acc:.2f}\nModel will be saved as 'ensemble_model.joblib'."
    joblib.dump(ensemble_clf, "ensemble_model.joblib")
    messagebox.showinfo("Model Building", msg)

def connect_to_api():
    api_url = "http://localhost:8000/docs"
    try:
        webbrowser.open(api_url)
        messagebox.showinfo("API Connection", f"Opening API documentation at {api_url}")
    except Exception as e:
        messagebox.showerror("API Connection", f"Failed to open API documentation: {e}")

# --- Manual Filtering GUI (unchanged) ---
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
        btn_keep = ttk.Button(control_frame, text="Keep", command=safe_run(self.keep_current))
        btn_keep.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        CreateToolTip(btn_keep, "Keep the current audio chunk.")
        btn_delete = ttk.Button(control_frame, text="Delete", command=safe_run(self.delete_current))
        btn_delete.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        CreateToolTip(btn_delete, "Delete the current audio chunk.")
        btn_next = ttk.Button(control_frame, text="Next", command=safe_run(self.next_file))
        btn_next.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        CreateToolTip(btn_next, "Move to the next audio chunk.")

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

# --- Main GUI Code with Enhanced UI, Reordered Tabs, and Log Panel ---
def main():
    global log_text  # To be used in the log_message function
    root = tk.Tk()
    root.title("Sound Classifier System - End-to-End Workflow")
    root.geometry("1000x750")
    
    # Set window icon (favicon placeholder) and add logo in header
    try:
        logo_image = tk.PhotoImage(file="skhysignal.png")
        root.iconphoto(False, logo_image)
    except Exception as e:
        print("Logo file not found, using default icon.")
    
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TButton", font=("Helvetica", 12), padding=5)
    style.configure("TLabel", font=("Helvetica", 12))
    
    header_frame = ttk.Frame(root)
    header_frame.pack(side=tk.TOP, fill="x", padx=10, pady=10)
    try:
        logo = tk.PhotoImage(file="skhysignal.png")
        logo_label = ttk.Label(header_frame, image=logo)
        logo_label.image = logo
        logo_label.pack(side=tk.LEFT, padx=10)
    except Exception as e:
        pass
    title_label = ttk.Label(header_frame, text="Sound Classifier System", font=("Helvetica", 18, "bold"))
    title_label.pack(side=tk.LEFT, padx=10)
    
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)
    
    def add_tab(tab, title, label_text, buttons):
        """Helper to add a tab with a header label and a grid of buttons.
           'buttons' is a list of tuples: (button_text, callback, tooltip)."""
        header = ttk.Label(tab, text=label_text, font=("Helvetica", 14))
        header.grid(row=0, column=0, columnspan=2, pady=(10, 20))
        for i, (btn_text, callback, tooltip) in enumerate(buttons, start=1):
            btn = ttk.Button(tab, text=btn_text, command=safe_run(callback))
            btn.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
            CreateToolTip(btn, tooltip)
        tab.grid_columnconfigure(0, weight=1)
    
    # Tab 1: Acquisitions
    tab_acq = ttk.Frame(notebook)
    notebook.add(tab_acq, text="1. Acquisitions")
    add_tab(tab_acq, "Acquisition Methods:", "Acquisition Methods:",
            [("Download Dataset", download_dataset, "Download a specified audio dataset to a chosen directory."),
             ("Download YouTube Playlist", download_youtube_playlist, "Enter a YouTube playlist URL and save its video URLs."),
             ("Download YouTube Video", download_youtube_video, "Download the audio from a YouTube video.")])
    
    # Tab 2: Processing
    tab_proc = ttk.Frame(notebook)
    notebook.add(tab_proc, text="2. Processing")
    add_tab(tab_proc, "Processing Options:", "Processing Options:",
            [("Feature Extraction", process_feature_extraction_file, "Extract audio features from a selected file."),
             ("Augmentation", process_augmentation, "Apply pitch, volume, and reversal adjustments."),
             ("Segmentation", process_segmentation, "Segment audio into smaller chunks."),
             ("Sliding Window", process_sliding_window_file, "Apply sliding window processing on audio."),
             ("Source Separation", process_source_separation_file, "Separate mixed audio sources.")])
    
    # Tab 3: Manual Filtering
    tab_filter = ttk.Frame(notebook)
    notebook.add(tab_filter, text="3. Manual Filtering")
    add_tab(tab_filter, "Manual Filtering:", "Manual Filtering:",
            [("Launch Filtering GUI", lambda: AudioFilterGUI(root), "Open the manual filtering interface.")])
    
    # Tab 4: Validation
    tab_valid = ttk.Frame(notebook)
    notebook.add(tab_valid, text="4. Validation")
    add_tab(tab_valid, "Validation Options:", "Validation Options:",
            [("Validate Audio Samples", validate_samples, "Validate and clean audio samples.")])
    
    # Tab 5: Reports
    tab_reports = ttk.Frame(notebook)
    notebook.add(tab_reports, text="5. Reports")
    add_tab(tab_reports, "Report Generation:", "Report Generation:",
            [("Generate Sampled Report", generate_sampled_report, "Generate a report from a subset of audio data."),
             ("Generate Dataset Report", generate_dataset_report, "Generate a comprehensive report for the dataset.")])
    
    # Tab 6: Data Preparation
    tab_data = ttk.Frame(notebook)
    notebook.add(tab_data, text="6. Data Preparation")
    add_tab(tab_data, "Organize & Rename Data:", "Organize & Rename Data:",
            [("Create Classes from Metadata", create_classes_from_metadata, "Organize files into classes using metadata."),
             ("Organize Dataset", organize_dataset, "Arrange audio samples into training, validation, and test sets."),
             ("Rename Classes", rename_classes, "Rename class directories or files based on a file extension.")])
    
    # Tab 7: Model & API
    tab_model_api = ttk.Frame(notebook)
    notebook.add(tab_model_api, text="7. Model & API")
    add_tab(tab_model_api, "Model Building & API Connection:", "Model Building & API Connection:",
            [("Build Model", build_model, "Train an ensemble classifier from feature files and save the model."),
             ("Connect to API", connect_to_api, "Open API documentation to test FastAPI endpoints.")])
    
    # Log Panel at the bottom
    log_frame = ttk.Frame(root)
    log_frame.pack(side=tk.BOTTOM, fill="x", padx=10, pady=(0,10))
    ttk.Label(log_frame, text="Log:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=5)
    log_text = tk.Text(log_frame, height=6, state="disabled", bg="#f0f0f0")
    log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    main()

