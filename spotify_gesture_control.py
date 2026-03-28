import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import urllib.request
import os

CLIENT_ID     = "YOUR CLIENT ID"
CLIENT_SECRET = "YOUR SECRET KEY"
REDIRECT_URI  = "http://127.0.0.1:8888/callback"

SCOPE = (
    "user-modify-playback-state "
    "user-read-playback-state "
    "user-read-currently-playing"
)

GESTURE_COOLDOWN = 1.5


def connect_spotify():
    auth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
    )
    return spotipy.Spotify(auth_manager=auth)


def count_raised_fingers(hand_landmarks):
    lm = hand_landmarks.landmark

    TIPS   = [4, 8, 12, 16, 20]
    KNUCK  = [3, 6, 10, 14, 18]

    fingers_up = 0

    if lm[TIPS[0]].x < lm[KNUCK[0]].x:
        fingers_up += 1

    for tip, knuck in zip(TIPS[1:], KNUCK[1:]):
        if lm[tip].y < lm[knuck].y:
            fingers_up += 1

    return fingers_up


def perform_action(sp, finger_count):
    try:
        if finger_count == 1:
            pb = sp.current_playback()
            if pb and pb.get("is_playing"):
                sp.pause_playback()
                return "⏸  Paused"
            else:
                sp.start_playback()
                return "▶️  Playing"

        elif finger_count == 2:
            sp.next_track()
            return "⏭  Next Track"

        elif finger_count == 3:
            sp.previous_track()
            return "⏮  Previous Track"

        elif finger_count == 4:
            pb = sp.current_playback()
            if pb:
                new_vol = min(100, pb["device"]["volume_percent"] + 10)
                sp.volume(new_vol)
                return f"🔊  Volume → {new_vol}%"

        elif finger_count == 5:
            pb = sp.current_playback()
            if pb:
                new_vol = max(0, pb["device"]["volume_percent"] - 10)
                sp.volume(new_vol)
                return f"🔉  Volume → {new_vol}%"

    except spotipy.exceptions.SpotifyException as e:
        return f"Spotify error: {e}"

    return ""


# ── MediaPipe landmark indices ───────────────────────────────────────────────
TIPS  = [4, 8, 12, 16, 20]
KNUCK = [3, 6, 10, 14, 18]

HAND_CONNECTIONS = frozenset([
    (0,1),(1,2),(2,3),(3,4),
    (5,6),(6,7),(7,8),
    (9,10),(10,11),(11,12),
    (13,14),(14,15),(15,16),
    (17,18),(18,19),(19,20),
    (0,5),(5,9),(9,13),(13,17),(0,17),
])


def count_raised_fingers_new(hand_landmarks):
    """Count raised fingers from a list of NormalizedLandmark (new Tasks API)."""
    fingers_up = 0
    # Thumb: compare x coords (mirrored frame)
    if hand_landmarks[TIPS[0]].x < hand_landmarks[KNUCK[0]].x:
        fingers_up += 1
    # Other four fingers: tip y < knuckle y means finger is up
    for tip, knuck in zip(TIPS[1:], KNUCK[1:]):
        if hand_landmarks[tip].y < hand_landmarks[knuck].y:
            fingers_up += 1
    return fingers_up


def get_model_path():
    """Download hand_landmarker.task once and return its local path."""
    model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
    if not os.path.exists(model_path):
        print("⬇️  Downloading hand_landmarker.task model (~8 MB) …")
        url = (
            "https://storage.googleapis.com/mediapipe-models/"
            "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        )
        urllib.request.urlretrieve(url, model_path)
        print("✅  Model downloaded.")
    return model_path


def draw_hand_landmarks(frame, landmarks_list):
    """Draw hand skeleton on frame using raw landmark coordinates."""
    h, w = frame.shape[:2]
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks_list]
    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, pts[start], pts[end], (0, 255, 0), 2)
    for x, y in pts:
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)


def main():
    sp = connect_spotify()
    print("✅  Connected to Spotify")

    # ── Build the HandLandmarker (new Tasks API) ──────────────────────────────
    model_path = get_model_path()
    base_opts  = mp_python.BaseOptions(model_asset_path=model_path)
    options    = mp_vision.HandLandmarkerOptions(
        base_options=base_opts,
        running_mode=mp_vision.RunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=0.75,
        min_hand_presence_confidence=0.75,
        min_tracking_confidence=0.75,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    last_action_time  = 0.0
    last_finger_count = -1
    status_text       = "Show a gesture!"

    with mp_vision.HandLandmarker.create_from_options(options) as detector:

        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            frame  = cv2.flip(frame, 1)
            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = detector.detect(mp_img)

            finger_count = 0

            if result.hand_landmarks:
                for hand_lm in result.hand_landmarks:
                    draw_hand_landmarks(frame, hand_lm)
                    finger_count = count_raised_fingers_new(hand_lm)

                now = time.time()
                gesture_changed = finger_count != last_finger_count
                cooldown_over   = (now - last_action_time) > GESTURE_COOLDOWN
                if finger_count > 0 and gesture_changed and cooldown_over:
                    action = perform_action(sp, finger_count)
                    if action:
                        status_text       = action
                        last_action_time  = now
                        last_finger_count = finger_count
                        print(f"[gesture={finger_count}] {action}")

            else:
                last_finger_count = -1

            h, w = frame.shape[:2]

            overlay = frame.copy()
            cv2.rectangle(overlay, (0, h - 70), (w, h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

            badge_color = (0, 200, 100) if finger_count > 0 else (60, 60, 60)
            cv2.circle(frame, (40, h - 35), 28, badge_color, -1)
            cv2.putText(
                frame, str(finger_count),
                (28 if finger_count < 10 else 20, h - 24),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2,
            )

            cv2.putText(
                frame, status_text,
                (80, h - 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2,
            )

            legend = [
                "1 finger  = Play/Pause",
                "2 fingers = Next Track",
                "3 fingers = Prev Track",
                "4 fingers = Vol Up",
                "5 fingers = Vol Down",
            ]
            for i, line in enumerate(legend):
                cv2.putText(
                    frame, line,
                    (w - 260, 25 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1,
                )

            cv2.imshow("Spotify Gesture Control  |  Press Q to quit", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("👋  Closed.")


if __name__ == "__main__":
    main()
