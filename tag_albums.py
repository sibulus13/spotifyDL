"""
Stamps the ID3 album tag of each MP3 with its parent folder name.
This makes Samsung Music's Albums view group songs by vibe folder
instead of scattering them across random YouTube video titles.

Usage:
    python tag_albums.py
    python tag_albums.py --downloads <folder>
"""

import sys
import argparse
from pathlib import Path
from mutagen.id3 import ID3, TALB, error as ID3Error
from mutagen.mp3 import MP3

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_DOWNLOADS = Path(__file__).parent / "downloads"


def stamp(downloads_dir: Path):
    mp3s = list(downloads_dir.rglob("*.mp3"))
    if not mp3s:
        print(f"No MP3s found in {downloads_dir}")
        return

    updated = 0
    for mp3_path in mp3s:
        folder_name = mp3_path.parent.name
        if folder_name == downloads_dir.name:
            continue  # skip files sitting in root (unclassified)

        try:
            audio = MP3(mp3_path, ID3=ID3)
            try:
                audio.add_tags()
            except ID3Error:
                pass  # tags already exist
            audio.tags["TALB"] = TALB(encoding=3, text=folder_name)
            audio.save()
            updated += 1
        except Exception as e:
            print(f"  SKIP {mp3_path.name}: {e}")

    print(f"Stamped album tag on {updated}/{len(mp3s)} files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads", default=str(DEFAULT_DOWNLOADS))
    args = parser.parse_args()
    stamp(Path(args.downloads))
