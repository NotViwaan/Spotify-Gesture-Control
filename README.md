# Spotify-Gesture-Control
🖐️ Control Spotify playback using hand gestures detected via webcam — built with Python, MediaPipe &amp; Spotipy.

# 🎵 Spotify Gesture Control

Control Spotify playback using hand gestures detected via your webcam — no keyboard or mouse needed!

## How It Works

Uses **MediaPipe** to track hand landmarks in real time via **OpenCV**, counts raised fingers, and maps each gesture to a **Spotify** action through the **Spotipy** API.

## Gesture Map

| Fingers Raised | Action            |
|:--------------:|-------------------|
| ☝️ 1           | Play / Pause       |
| ✌️ 2           | Next Track         |
| 🤟 3           | Previous Track     |
| 🖖 4           | Volume Up (+10%)   |
| 🖐️ 5           | Volume Down (−10%) |

## Prerequisites

- Python 3.8+
- A **Spotify Premium** account (required for playback control via API)
- A webcam

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Spotify API credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Create an app and copy your **Client ID** and **Client Secret**.
3. Add `http://127.0.0.1:8888/callback` as a **Redirect URI** in your app settings.
4. Open `spotify_gesture_control.py` and replace the placeholder values:

```python
CLIENT_ID     = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
```

### 3. Run the script

```bash
python spotify_gesture_control.py
```

On first run, a browser window will open asking you to authorise the app. After that, a token is cached locally.

## Usage

- Hold your hand clearly in front of the webcam.
- Raise the corresponding number of fingers for the action you want.
- A **1.5-second cooldown** prevents accidental repeated triggers.
- Press **`Q`** to quit.

## Project Structure

```
spotify-gesture-control/
├── spotify_gesture_control.py   # Main application
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot open webcam` | Check that no other app is using the camera |
| `Spotify error: 403` | Ensure you have a **Spotify Premium** account |
| No active device error | Open Spotify on any device and start playing something first |
| Auth token issues | Delete the `.cache` file and re-authenticate |
