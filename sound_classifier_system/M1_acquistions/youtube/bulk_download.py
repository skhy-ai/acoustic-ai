import yt_dlp
import os
from tkinter import filedialog, Tk

def download_audio(url, output_path):
    """
    Downloads audio from a YouTube video and converts it to WAV.
    
    Parameters:
      url (str): YouTube video URL.
      output_path (str): File path to save the downloaded audio.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': output_path
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_from_file(file_path):
    """
    Reads YouTube URLs from a file and downloads each as WAV.
    The output filenames are generated based on the input file's basename.
    
    Parameters:
      file_path (str): Path to the text file containing YouTube URLs.
    """
    with open(file_path, 'r') as file:
        urls = file.readlines()
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    for i, url in enumerate(urls, start=1):
        url = url.strip()
        if url:
            output_path = f"{base_name}_{i}.wav"
            download_audio(url, output_path)

if __name__ == "__main__":
    # Use a file dialog to select the file with YouTube URLs.
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select text file with YouTube URLs", filetypes=[("Text Files", "*.txt")])
    if file_path:
        download_from_file(file_path)
    else:
        print("No file selected.")
