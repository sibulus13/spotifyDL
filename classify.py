"""
Classify downloaded MP3s into vibe-based folders.
Reads genre/metadata from the Exportify CSV, then moves files from
downloads/ into categorized subfolders.

Pass --reclassify to move files already in subfolders back to root first,
then re-classify everything from scratch.

Usage:
    python classify.py
    python classify.py --reclassify
    python classify.py --dry-run
"""

import csv
import sys
import shutil
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_CSV = Path(__file__).parent.parent / "Spring_26.csv"
DEFAULT_DOWNLOADS = Path(__file__).parent / "downloads"

# ── Category definitions ──────────────────────────────────────────────────────
# Priority is evaluated in ORDER — first match wins.
# Each entry: (folder_name, genre_keywords, exclude_genres, artist_keywords, title_keywords, weight)

ORDERED_CATEGORIES = [
    {
        "name": "Subtitled Feelings (anime, j-pop, asian pop)",
        "genres": ["anime", "j-pop", "j-rock", "mandopop", "c-pop", "taiwanese pop",
                   "cantopop", "k-pop", "k-ballad", "gufeng", "chinese r&b", "neoclassical",
                   "japanese classical"],
        "artists": ["jj lin", "jay chou", "gem", "radwimps", "ikimonogakari", "akano",
                    "co shu nie", "cö shu nie", "yiruma", "joe hisaishi", "10cm",
                    "andrew seoul", "samuel kim", "wanting"],
        "titles": ["demon slayer", "kimetsu", "suzume", "one summer day", "rick and morty",
                   "ブルーバード", "kamado"],
        "exclude": [],
    },
    {
        "name": "You Probably Own A Katana (heavy bass, metal, dubstep)",
        "genres": ["dubstep", "riddim", "deathstep", "metalcore", "metal",
                   "screamo", "post-hardcore", "bass music", "dub", "drum and bass",
                   "drumstep", "liquid funk", "nu metal", "rap metal",
                   "alternative rock", "rock", "emo", "christian rock", "alternative metal",
                   "pop punk"],
        "artists": ["subtronics", "kai wachi", "sullivan king", "skrillex", "griz",
                    "zomboy", "i prevail", "avenged sevenfold", "bring me the horizon",
                    "linkin park", "ray volpe", "deadlyft", "tape b", "over saturated",
                    "smash into pieces", "micah ariss"],
        "titles": [],
        "exclude": [],
    },
    {
        "name": "3AM NPC Speedrun (techno, hyperpop, phonk)",
        "genres": ["hypertechno", "techno", "slap house", "hard techno",
                   "phonk", "g-house", "tech house", "brazilian phonk", "vinahouse"],
        "artists": ["hyper kenzo", "alema", "davuiside", "atlast", "d-push", "valexus",
                    "neptunica", "kickcheeze"],
        "titles": ["techno", "sped up", "speed up"],
        "exclude": [],
    },
    {
        "name": "Crying In The Parking Lot Of A Whole Foods (melodic bass, future bass)",
        "genres": ["melodic bass", "future bass", "chillstep"],
        "artists": ["illenium", "william black", "sabai", "dabin", "ghostdragon", "nurko",
                    "fairlane", "elephante", "armnhmr", "notaker", "bonnie x clyde",
                    "btwrks", "janho", "3thos", "deeps", "crux one", "lights on",
                    "rise", "ryn", "bound to break", "sadbois", "clouds",
                    "not enough", "secrets", "patfromlastyear", "better than me",
                    "albert neve", "cinema kid", "in my arms", "maypops",
                    "neon tide", "tristam", "paper skies"],
        "titles": [],
        "exclude": ["dubstep", "riddim", "deathstep", "metalcore", "metal"],
    },
    {
        "name": "You've Never Left Your State But You Call Yourself A Festival Guy (EDM, big room, hardstyle)",
        "genres": ["big room", "hardstyle", "happy hardcore", "progressive house",
                   "tropical house", "future house", "electro house", "europop",
                   "eurodance", "stutter house", "italo dance", "moombahton",
                   "bass house", "edm trap"],
        "artists": ["tungevaag", "tatsunoshin", "mako", "cascada", "major lazer",
                    "alan walker", "the chainsmokers", "bingo players", "gabry ponte",
                    "felix jaehn", "severman", "waiting for you", "albert neve",
                    "bvrnout", "young & reckless", "bijou"],
        "titles": [],
        "exclude": [],
    },
    {
        "name": "2013 Called, It Wants Its Feelings Back (throwback indie, pop, alt rock)",
        "genres": [],
        "artists": ["one direction", "coldplay", "the goo goo dolls", "bastille",
                    "vance joy", "the killers", "gym class heroes", "mike posner",
                    "lorde", "ed sheeran", "mike arell"],
        "titles": ["mr. brightside", "riptide", "iris", "pompeii", "viva la vida",
                   "night changes", "perfect", "payphone", "faded", "i took a pill",
                   "ass back home", "team"],
        "exclude": [],
    },
    {
        "name": "Your Situationship Left You On Read (sad indie, soft pop, emotional)",
        "genres": ["soft pop", "folk pop", "pop singer-songwriter", "art pop",
                   "norwegian pop", "acoustic pop"],
        "artists": ["anson seabra", "alex warren", "tate mcrae", "d4vd", "kina",
                    "lany", "lauv", "sasha alex sloan", "dean lewis", "james tw",
                    "kyle hume", "camylio", "brdgs", "rosie darling", "munn",
                    "isabel larosa", "yung kai", "bbno$", "elley duhé",
                    "elley duhe", "david kushner", "neoni", "aurora", "rumi",
                    "satellite music collective", "small things", "neon tide",
                    "elijah woods", "jared benjamin", "imor", "arlow", "pixiepunk",
                    "desren", "karma fields", "mia vaile", "feel so lucky",
                    "rozei", "kiremi", "martha speros", "tattooed mulligan",
                    "crash adams", "joel adams", "biscuit beats", "notaker",
                    "gustixa", "cara", "cyril", "lunatic souls", "twinbed",
                    "valorant", "last time", "weight of the world",
                    "djss", "aou", "slowli", "sapientdream"],
        "titles": ["love", "heart", "goodbye", "gone", "you", "miss",
                   "slowed", "reverb"],
        "exclude": [],
    },
]

FALLBACK = "Your Situationship Left You On Read (sad indie, soft pop, emotional)"


def classify_track(genres_str: str, artist: str, title: str) -> str:
    genres = [g.strip().lower() for g in genres_str.split(",") if g.strip()]
    artist_lower = artist.lower()
    title_lower = title.lower()

    for cat in ORDERED_CATEGORIES:
        # Check exclusions
        if any(ex in genres for ex in cat["exclude"]):
            continue

        genre_hit = any(g in genres for g in cat["genres"])
        artist_hit = any(a in artist_lower for a in cat["artists"])
        title_hit = any(t in title_lower for t in cat["titles"])

        if genre_hit or artist_hit or title_hit:
            return cat["name"]

    return FALLBACK


def find_mp3(search_root: Path, artist: str, title: str) -> Path | None:
    # Search recursively so we find files already in subfolders too
    prefix = f"{artist} -".lower()
    title_lower = title.lower()[:20]
    for f in search_root.rglob("*.mp3"):
        if f.parent.name == f.parent.parent.name:
            continue  # skip double-nested
        name = f.name.lower()
        if name.startswith(prefix) and title_lower[:15] in name:
            return f
    return None


def flatten(downloads_dir: Path):
    """Move all MP3s from subfolders back to root (for reclassify)."""
    for f in downloads_dir.rglob("*.mp3"):
        if f.parent != downloads_dir:
            dest = downloads_dir / f.name
            if not dest.exists():
                shutil.move(str(f), str(dest))
    # Remove empty subdirs
    for d in downloads_dir.iterdir():
        if d.is_dir():
            try:
                d.rmdir()
            except OSError:
                pass  # not empty, leave it


def classify(csv_path: Path, downloads_dir: Path, dry_run: bool, reclassify: bool):
    if reclassify and not dry_run:
        print("Flattening existing subfolders...")
        flatten(downloads_dir)

    tracks = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("Track Name", "").strip()
            artists_raw = row.get("Artist Name(s)", "").strip()
            artist = artists_raw.split(";")[0].strip()
            genres = row.get("Genres", "").strip()
            if name and artist:
                tracks.append({"name": name, "artist": artist, "genres": genres})

    counts: dict[str, int] = {}
    moved = 0
    missing = 0

    for track in tracks:
        category = classify_track(track["genres"], track["artist"], track["name"])
        counts[category] = counts.get(category, 0) + 1

        mp3 = find_mp3(downloads_dir, track["artist"], track["name"])
        if not mp3:
            missing += 1
            continue

        dest_dir = downloads_dir / category
        dest = dest_dir / mp3.name

        if dest.exists() and mp3.parent == dest_dir:
            continue  # already in the right place

        if dry_run:
            print(f"  {mp3.name}  →  {category}/")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(mp3), str(dest))
            moved += 1

    print("\n── Playlist breakdown ───────────────────────────────────────────────")
    for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
        bar = "█" * (count // 2)
        print(f"  {count:>3}  {bar}  {cat}")

    if dry_run:
        print("\n[Dry run — no files moved]")
    else:
        print(f"\nMoved {moved} files. {missing} not yet downloaded.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    parser.add_argument("--downloads", default=str(DEFAULT_DOWNLOADS))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reclassify", action="store_true",
                        help="Flatten subfolders and re-sort everything from scratch")
    args = parser.parse_args()

    classify(Path(args.csv), Path(args.downloads), args.dry_run, args.reclassify)
