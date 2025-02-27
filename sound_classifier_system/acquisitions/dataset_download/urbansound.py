import soundata

def download_urbansound8k(data_home="../../external_sound_data"):
    """
    Downloads the UrbanSound8K dataset using Soundata.
    """
    dataset = soundata.initialize('urbansound8k', data_home=data_home)
    dataset.download()

if __name__ == "__main__":
    download_urbansound8k()
