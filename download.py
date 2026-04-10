"""
Spotify playlist downloader via CSV + yt-dlp YouTube search.

Usage:
    python download.py --csv <path/to/playlist.csv>
    python download.py --csv <path/to/playlist.csv> --output <folder>

The CSV must have "Track Name" and "Artist Name(s)" columns (Exportify format).
"""

import csv
import sys
import argparse
from pathlib import Path
import yt_dlp

# Force UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_CSV = Path(__file__).parent.parent / "Spring_26.csv"
DEFAULT_OUTPUT = Path(__file__).parent / "downloads"
FFMPEG_PATH = Path.home() / ".spotdl" / "ffmpeg.exe"


def load_tracks(csv_path: Path) -> list[dict]:
    tracks = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Track Name", "").strip()
            artists_raw = row.get("Artist Name(s)", "").strip()
            # Artists are semicolon-separated; use the first one for search clarity
            artist = artists_raw.split(";")[0].strip()
            if name and artist:
                tracks.append({"name": name, "artist": artist})
    return tracks


def download_track(track: dict, output_dir: Path, ydl_opts: dict) -> bool:
    query = f"{track['artist']} - {track['name']}"
    search_url = f"ytsearch1:{query}"
    opts = {
        **ydl_opts,
        "outtmpl": str(output_dir / f"{track['artist']} - {track['name']}.%(ext)s"),
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([search_url])
        return True
    except yt_dlp.utils.DownloadError as e:
        print(f"  FAILED: {query} — {e}")
        return False


def download_all(tracks: list[dict], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg = str(FFMPEG_PATH) if FFMPEG_PATH.exists() else "ffmpeg"

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": ffmpeg,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
    }

    failed = []
    for i, track in enumerate(tracks, 1):
        label = f"{track['artist']} - {track['name']}"
        dest = output_dir / f"{track['artist']} - {track['name']}.mp3"
        if dest.exists():
            print(f"[{i}/{len(tracks)}] Skipping (exists): {label}")
            continue
        print(f"[{i}/{len(tracks)}] Downloading: {label}")
        ok = download_track(track, output_dir, ydl_opts)
        if not ok:
            failed.append(label)

    print(f"\nDone. {len(tracks) - len(failed)}/{len(tracks)} tracks saved to: {output_dir}")
    if failed:
        print(f"\nFailed ({len(failed)}):")
        for f in failed:
            print(f"  - {f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to Exportify CSV")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output folder")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}")
        sys.exit(1)

    tracks = load_tracks(csv_path)
    print(f"Loaded {len(tracks)} tracks from {csv_path.name}\n")
    download_all(tracks, Path(args.output))
