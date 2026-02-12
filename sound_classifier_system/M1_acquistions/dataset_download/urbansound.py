import soundata
import sys

def download_urbansound8k(data_home):
    """
    Downloads the UrbanSound8K dataset using Soundata.
    
    Parameters:
      data_home (str): Directory where the dataset should be stored.
    """
    dataset = soundata.initialize('urbansound8k', data_home=data_home)
    dataset.download()

if __name__ == "__main__":
    # Allow data_home to be passed as a command-line argument, or default to "sound_dataset".
    data_home = sys.argv[1] if len(sys.argv) > 1 else "sound_dataset"
    download_urbansound8k(data_home)
