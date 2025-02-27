from pytube import Playlist

def save_playlist_urls(playlist_url, output_file):
    """
    Saves all video URLs from a YouTube playlist to a text file.
    """
    playlist = Playlist(playlist_url)
    with open(output_file, 'w') as file:
        for url in playlist.video_urls:
            print(url)
            file.write(f"{url}\n")

if __name__ == "__main__":
    playlist_url = input("Enter the YouTube playlist URL: ")
    output_file = input("Enter the output file path (e.g., 'playlist_urls.txt'): ")
    save_playlist_urls(playlist_url, output_file)
