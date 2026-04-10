# spotifyDL

Downloads a Spotify playlist as MP3s and sorts them into vibe-based folders.
No Spotify Premium required. No API keys required.

---

## How it works

Spotify doesn't allow direct audio downloads. This tool works around that by:

1. You export your playlist metadata to a CSV file from Exportify (free, browser-based)
2. The downloader reads each track name + artist from the CSV
3. It searches YouTube for each song and downloads the best audio match via `yt-dlp`
4. The classifier reads the same CSV and sorts the MP3s into themed folders based on genre tags

---

## Prerequisites

- Python 3.12+ installed and on PATH
- Internet connection

That's it. All other dependencies install automatically on first run.

---

## Step-by-step: Download a new playlist

### Step 1 — Export the playlist to CSV

1. Open your browser and go to **https://exportify.net**
2. Click **Log in with Spotify** and authorize
3. Find the playlist you want and click **Export**
4. Save the `.csv` file somewhere you can find it (e.g. `D:\repo\_Misc\Music\MyPlaylist.csv`)

### Step 2 — Run the downloader

Open a terminal in this folder (`D:\repo\_Misc\Music\spotifyDL\`) and run:

```
python download.py --csv "D:\repo\_Misc\Music\MyPlaylist.csv"
```

Or to change where the MP3s are saved:

```
python download.py --csv "D:\repo\_Misc\Music\MyPlaylist.csv" --output "D:\MyMusic"
```

- Downloads go to `downloads\` inside this folder by default
- Already-downloaded songs are skipped automatically — safe to re-run if interrupted
- Failed downloads are listed at the end; re-running will retry them

### Step 3 — Sort into vibe folders

Once downloading is done (or even while it's running):

```
python classify.py --csv "D:\repo\_Misc\Music\MyPlaylist.csv"
```

To re-sort from scratch if you've already classified:

```
python classify.py --csv "D:\repo\_Misc\Music\MyPlaylist.csv" --reclassify
```

To preview what would happen without moving any files:

```
python classify.py --csv "D:\repo\_Misc\Music\MyPlaylist.csv" --dry-run
```

---

## The 7 vibe folders

These are generated automatically based on genre tags in the Exportify CSV.
The folder names are intentionally unhinged. The parentheses tell you what's actually inside.

| Folder | What's in it |
|--------|-------------|
| **Your Situationship Left You On Read** *(sad indie, soft pop, emotional)* | The soft stuff. Anson Seabra, LANY, Tate McRae, Alex Warren, d4vd. You put this on and stare out a car window. |
| **Crying In The Parking Lot Of A Whole Foods** *(melodic bass, future bass)* | ILLENIUM, William Black, SABAI, Dabin, Fairlane. Emotional but with drops. The genre for people who feel things loudly. |
| **You Probably Own A Katana** *(heavy bass, metal, dubstep)* | Subtronics, Kai Wachi, Sullivan King, Bring Me The Horizon, Linkin Park. Aggressive. For working out or being genuinely pissed off. |
| **Subtitled Feelings** *(anime, j-pop, asian pop)* | Jay Chou, JJ Lin, RADWIMPS, Ikimonogakari, Yiruma. Songs you have feelings about in a language you may or may not speak. |
| **You've Never Left Your State But You Call Yourself A Festival Guy** *(EDM, big room, hardstyle)* | Cascada, Mako, The Chainsmokers, Tungevaag. Festival-core. You listen to this and imagine yourself on a main stage. |
| **2013 Called, It Wants Its Feelings Back** *(throwback indie, pop, alt rock)* | Coldplay, One Direction, Bastille, Vance Joy, The Killers. You know every word and you are not ashamed. |
| **3AM NPC Speedrun** *(techno, hyperpop, phonk)* | Hyper Kenzo, D-Push, Davuiside. You are not sleeping. You are also not okay. But the beat goes hard. |

Songs with no genre data in Spotify's catalog default into **Your Situationship Left You On Read**.

---

## Transferring to Samsung S23

**Total size: ~1.6 GB** for a 200-track playlist at 320kbps MP3.

### Option A — USB (easiest)

1. Connect your phone via USB cable
2. On the phone, tap the notification and select **File Transfer (MTP)**
3. Open File Explorer on your PC → navigate to your phone → `Internal storage\Music\`
4. Copy the entire `downloads\` folder there (rename it to your playlist name first if you want)
5. Open **Samsung Music** → it will auto-scan and index everything

### Option B — ADB (faster for large transfers)

Requires USB Debugging enabled in Developer Options on the phone.

```
adb push "D:\repo\_Misc\Music\spotifyDL\downloads" /sdcard/Music/Spring26
```

### Viewing on Samsung Music

| View | Behavior |
|------|----------|
| **All Songs** | Shows every MP3 in a flat list — works perfectly |
| **Folders** | Shows your 7 vibe folders exactly as named — works perfectly |
| **Albums** | Groups by ID3 album tag embedded in the file — will be scattered unless you run the tag-stamping script (see below) |

### Optional: Fix the Albums view

Run this to stamp each MP3 with its folder name as the album tag so Samsung Music groups them correctly:

```
python tag_albums.py
```

*(See `tag_albums.py` in this folder)*

---

## Files in this folder

```
spotifyDL/
├── download.py       # Downloads tracks from YouTube based on CSV
├── classify.py       # Sorts MP3s into vibe folders
├── tag_albums.py     # Stamps ID3 album tags so Samsung Music shows folders as albums
├── downloads/        # Where MP3s go (created on first run)
│   ├── Your Situationship Left You On Read (sad indie, soft pop, emotional)/
│   ├── Crying In The Parking Lot Of A Whole Foods (melodic bass, future bass)/
│   ├── You Probably Own A Katana (heavy bass, metal, dubstep)/
│   ├── Subtitled Feelings (anime, j-pop, asian pop)/
│   ├── You've Never Left Your State But You Call Yourself A Festival Guy (EDM, big room, hardstyle)/
│   ├── 2013 Called, It Wants Its Feelings Back (throwback indie, pop, alt rock)/
│   └── 3AM NPC Speedrun (techno, hyperpop, phonk)/
└── README.md         # This file
```

---

## Troubleshooting

**"FFmpeg not found"**
Run `python -m spotdl --download-ffmpeg` once. It saves to `~/.spotdl/ffmpeg.exe`.

**A song downloaded but sounds wrong / is the wrong track**
yt-dlp matched the wrong YouTube video. Delete the MP3 and find the correct YouTube URL manually, then download it with:
```
yt-dlp -x --audio-format mp3 --audio-quality 320k "https://youtube.com/watch?v=..." -o "downloads/Artist - Title.%(ext)s"
```

**Download interrupted mid-way**
Just re-run `python download.py`. It skips files that already exist.

**Song is missing after classify**
Re-run `python classify.py --reclassify` — it searches all subfolders recursively so nothing gets lost.
