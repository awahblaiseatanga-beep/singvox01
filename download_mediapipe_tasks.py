import os
import urllib.request

def download_models():
    os.makedirs(r"d:\Singvox\Singvox\mediapipe_models", exist_ok=True)
    base = "https://storage.googleapis.com/mediapipe-models/"
    
    urls = {
        "pose_landmarker.task": base + "pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
        "hand_landmarker.task": base + "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
        "face_landmarker.task": base + "face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
    }
    
    for name, url in urls.items():
        path = os.path.join(r"d:\Singvox\Singvox\mediapipe_models", name)
        if not os.path.exists(path):
            print(f"Downloading {name}...")
            try:
                urllib.request.urlretrieve(url, path)
                print(f"Success: {name}")
            except Exception as e:
                print(f"Error downloading {name}: {e}")
        else:
            print(f"{name} already exists.")

if __name__ == "__main__":
    download_models()
