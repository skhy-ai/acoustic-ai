from pytube import Playlist
from tkinter import filedialog, messagebox, simpledialog

def save_playlist_urls(playlist_url=None, output_file=None):
    """
    Saves all video URLs from a YouTube playlist to a text file.
    
    If playlist_url and output_file are not provided, the function prompts the user.
    
    Parameters:
      playlist_url (str, optional): The YouTube playlist URL.
      output_file (str, optional): Path to the file where URLs will be saved.
    """
    if not playlist_url:
        playlist_url = simpledialog.askstring("Playlist URL", "Enter the YouTube Playlist URL:")
        if not playlist_url:
            messagebox.showwarning("Input Error", "Playlist URL is required.")
            return

    if not output_file:
        output_file = filedialog.asksaveasfilename(defaultextension=".txt",
                                                   title="Save Playlist URLs File",
                                                   filetypes=[("Text Files", "*.txt")])
        if not output_file:
            messagebox.showwarning("Input Error", "Output file is required.")
            return

    try:
        playlist = Playlist(playlist_url)
        with open(output_file, 'w') as file:
            for url in playlist.video_urls:
                file.write(f"{url}\n")
        messagebox.showinfo("Success", "Playlist URLs saved successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save playlist URLs. Details: {e}")

if __name__ == "__main__":
    # If run as a standalone script, prompt the user.
    from tkinter import Tk
    root = Tk()
    root.withdraw()
    save_playlist_urls()
