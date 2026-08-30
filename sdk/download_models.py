import os
from sentence_transformers import SentenceTransformer
from faster_whisper import WhisperModel

def download_all_models(target_dir="./models"):
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"Downloading all-MiniLM-L6-v2 to {target_dir}/all-MiniLM-L6-v2...")
    # This downloads and saves the model directly to the target folder
    model = SentenceTransformer("all-MiniLM-L6-v2")
    model.save(os.path.join(target_dir, "all-MiniLM-L6-v2"))
    
    print(f"\nDownloading faster-whisper (tiny) to {target_dir}/whisper-tiny...")
    # WhisperModel automatically downloads to a specific directory if download_root is provided
    # but we can just let it cache and use the cache path, or download via huggingface_hub
    from huggingface_hub import snapshot_download
    snapshot_download(
        repo_id="Systran/faster-whisper-tiny",
        local_dir=os.path.join(target_dir, "whisper-tiny"),
        local_dir_use_symlinks=False
    )
    
    print("\n✅ All models successfully downloaded for complete offline use!")
    print("You can now point the SDK to this folder and disable internet access.")

if __name__ == "__main__":
    download_all_models()
