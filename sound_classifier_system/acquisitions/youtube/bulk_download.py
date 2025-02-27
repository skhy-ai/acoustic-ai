import yt_dlp
import os

def download_audio(url, output_path):
    """
    Downloads audio from a YouTube video and converts it to WAV.
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
    file_path = input("Enter the path to the text file with YouTube URLs: ")
    download_from_file(file_path)
