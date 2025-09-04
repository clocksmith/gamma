"""A script to download GGUF models from the Hugging Face Hub."""

import argparse
import os
from huggingface_hub import hf_hub_download

def download_model(repo_id: str, filename: str, token: str = None) -> None:
    """Downloads a model file from a Hugging Face repository.

    Args:
        repo_id: The repository ID on Hugging Face (e.g., "google/gemma-3-27b-it-qat-q4_0-gguf").
        filename: The exact name of the file to download from the repo.
        token: An optional Hugging Face access token for gated models.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_dir_path = os.path.join(project_root, "models")
    local_file_path = os.path.join(local_dir_path, filename)

    print(f"--- Model Download Utility ---")
    print(f"Repository: {repo_id}")
    print(f"File:       {filename}")
    print(f"Target Dir: {local_dir_path}")
    print("------------------------------")

    if os.path.exists(local_file_path):
        print("Model file already exists locally. Skipping download.")
        return

    os.makedirs(local_dir_path, exist_ok=True)

    try:
        print("Starting download...")
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir_path,
            local_dir_use_symlinks=False,
            token=token,
        )
        print(f"File downloaded successfully to: {downloaded_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("\nPlease check the following:")
        print("1. You are logged in to Hugging Face (`huggingface-cli login`).")
        print("2. You have been granted access to this model if it's gated.")
        print("3. The repository ID and filename are correct.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download a GGUF model from Hugging Face."
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        required=True,
        help="The repository ID on Hugging Face.",
    )
    parser.add_argument(
        "--filename",
        type=str,
        required=True,
        help="The exact filename to download.",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Optional Hugging Face access token.",
    )

    args = parser.parse_args()
    download_model(args.repo_id, args.filename, args.token)