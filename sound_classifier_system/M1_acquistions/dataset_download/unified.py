import os
import soundata
import librosa
import requests
import zipfile

def download_soundata_dataset(dataset_name, data_home):
    """
    Downloads and validates datasets available in Soundata (e.g., UrbanSound8K, ESC-50, GTZAN).
    
    Parameters:
      dataset_name (str): Name of the dataset to download.
      data_home (str): Directory where the dataset should be stored.
    """
    try:
        dataset = soundata.initialize(dataset_name, data_home=data_home)
        if dataset.validate():
            print(f"✅ {dataset_name} is already downloaded and validated.")
            return dataset

        print(f"⬇️ Downloading {dataset_name}...")
        dataset.download()
        if dataset.validate():
            print(f"✅ {dataset_name} downloaded and validated successfully.")
        else:
            print(f"⚠️ Warning: {dataset_name} may be incomplete or corrupted.")
        return dataset

    except Exception as e:
        print(f"❌ Error: Failed to download {dataset_name}. Details: {e}")
        return None

def download_custom_dataset(dataset_name, data_home, source_url=None):
    """
    Downloads, extracts, and validates non-Soundata datasets.
    
    Parameters:
      dataset_name (str): Name of the dataset.
      data_home (str): Directory where the dataset should be stored.
      source_url (str, optional): URL from which to download the dataset.
    """
    dataset_path = os.path.join(data_home, dataset_name)
    if os.path.exists(dataset_path) and os.listdir(dataset_path):
        print(f"✅ {dataset_name} already exists in {dataset_path}. Skipping download.")
        return

    if source_url:
        print(f"⬇️ Downloading {dataset_name} from {source_url}...")
        dataset_zip = os.path.join(data_home, f"{dataset_name}.zip")
        try:
            response = requests.get(source_url, stream=True)
            with open(dataset_zip, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"✅ {dataset_name} downloaded successfully.")
            with zipfile.ZipFile(dataset_zip, 'r') as zip_ref:
                zip_ref.extractall(dataset_path)
            print(f"✅ {dataset_name} extracted to {dataset_path}.")
            os.remove(dataset_zip)
        except Exception as e:
            print(f"❌ Error downloading {dataset_name}: {e}")
            return
    else:
        print(f"⚠️ No download URL provided for {dataset_name}. Please manually place files in {dataset_path}.")

    # Validate dataset by checking audio files
    for file in os.listdir(dataset_path):
        if file.endswith((".wav", ".flac")):
            try:
                y, sr = librosa.load(os.path.join(dataset_path, file), sr=None)
                print(f"✅ {file} loaded successfully (Sample Rate: {sr})")
            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
    print(f"✅ {dataset_name} is ready for use.")

if __name__ == "__main__":
    data_home = "../../external_sound_data"
    soundata_datasets = ["urbansound8k", "esc50", "gtzan"]
    custom_datasets = {
        "NDT_Ultrasonic": "https://lib.dr.iastate.edu/cgi/viewcontent.cgi?article=1000&context=cnde_data",
        "AE_Corrosion": "https://data.mendeley.com/datasets/xyz12345/1",
        "NASA_Prognostics": "https://www.nasa.gov/content/prognostics-center-of-excellence-data-set-repository"
    }
    
    # Download Soundata datasets
    for dataset in soundata_datasets:
        download_soundata_dataset(dataset, data_home)
    
    # Download custom datasets
    for dataset, url in custom_datasets.items():
        download_custom_dataset(dataset, data_home, url)
