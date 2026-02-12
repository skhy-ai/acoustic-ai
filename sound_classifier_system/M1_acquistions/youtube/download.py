import yt_dlp
from tkinter import filedialog, simpledialog, Tk, messagebox

def download_audio(url, output_path):
    """
    Downloads audio from a YouTube video and converts it to MP3.
    
    Parameters:
      url (str): YouTube video URL.
      output_path (str): File path to save the downloaded audio.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    video_url = simpledialog.askstring("Download YouTube Video", "Enter the YouTube video URL:")
    if not video_url:
        messagebox.showwarning("Input Error", "No video URL provided.")
        exit()
    output_path = filedialog.asksaveasfilename(defaultextension=".mp3", title="Save Audio",
                                               filetypes=[("MP3 Files", "*.mp3"), ("WAV Files", "*.wav")])
    if not output_path:
        messagebox.showwarning("Input Error", "No output file selected.")
        exit()
    download_audio(video_url, output_path)
