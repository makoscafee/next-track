#!/usr/bin/env python
"""
Script to download and prepare datasets for NextTrack
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def download_kaggle_dataset():
    """
    Download Spotify dataset from Kaggle.

    Requires kaggle CLI to be installed and configured:
    pip install kaggle
    """
    print("To download the Spotify dataset from Kaggle:")
    print("1. Install kaggle: pip install kaggle")
    print("2. Set up your Kaggle API credentials")
    print(
        "3. Run: kaggle datasets download -d yamaerenay/spotify-dataset-19212020-600k-tracks"
    )
    print("4. Extract to data/raw/")
    print()
    print("Alternative datasets:")
    print("- Million Song Dataset: http://millionsongdataset.com/")
    print("- Free Music Archive: https://github.com/mdeff/fma")
    print(
        "- Spotify Million Playlist: https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge"
    )


def prepare_data_directories():
    """Create necessary data directories."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dirs = [
        os.path.join(base_dir, "data", "raw"),
        os.path.join(base_dir, "data", "processed"),
        os.path.join(base_dir, "data", "models"),
    ]

    for dir_path in data_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")


def main():
    """Main function."""
    print("NextTrack Data Download Script")
    print("=" * 40)

    prepare_data_directories()
    print()
    download_kaggle_dataset()


if __name__ == "__main__":
    main()
