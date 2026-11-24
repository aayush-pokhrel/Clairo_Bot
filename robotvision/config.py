"""All tunable settings in one place. Phrases live in phrases.py."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.example")  # GROQ_API_KEY lives here (gitignored, never committed)

# --- Camera ---
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
MIRROR = True  # flip horizontally so it behaves like a mirror

# --- Models ---
GESTURE_MODEL = ROOT / "gesture_recognizer.task"
FACE_MODEL = ROOT / "face_landmarker.task"
NUM_HANDS = 2
FACE_EVERY_N_FRAMES = 2  # run face detection every Nth frame to save CPU

# --- Stabilizer ---
MIN_CONFIDENCE = 0.6  # ignore gesture scores below this
HOLD_FRAMES = 8  # gesture must be seen this many frames in a row to count

# --- Presence (person detection) ---
ARRIVE_SECONDS = 0.8  # person must be visible this long before we greet them
LEAVE_SECONDS = 5.0  # person must be gone this long before we say goodbye

# --- Behavior ---
ROBOT_NAME = "Nova"  # used when introducing itself
COOLDOWN_SECONDS = 4.0  # don't react to the same gesture again within this window
GREETING_CONTEXT_SECONDS = 12.0  # thumbs up/down this soon after "how are you?" = an answer

# --- Wave detection ---
WAVE_WINDOW_SECONDS = 1.5  # look at this much recent hand motion
WAVE_MIN_SWINGS = 2  # direction changes needed (right-left-right = 2)
WAVE_SWING_SIZE = 0.4  # each swing must travel this many "hand sizes"

# --- Voice ---
VOICE_ENABLED = True
VOICE_NAME = "Zira"  # part of an installed voice name ("Zira", "David"), or None for default
VOICE_RATE = 165  # words per minute; a bit slower sounds friendlier
VOICE_VOLUME = 1.0

# --- Voice conversation (Groq: free API key at https://console.groq.com/keys) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHAT_ENABLED = True  # turns off automatically if GROQ_API_KEY is missing
STT_MODEL = "whisper-large-v3-turbo"  # speech -> text
LLM_MODEL = "openai/gpt-oss-20b"  # fast; "openai/gpt-oss-120b" is smarter but slower
LLM_REASONING_EFFORT = "low"  # "low" keeps replies fast; set None for models without reasoning
HISTORY_TURNS = 6  # how many back-and-forths the bot remembers within one conversation
CAMPUS_DB = ROOT / "data" / "campus.json"

# --- Microphone ---
MIC_DEVICE = None  # None = system default; or a device index/name from `python -m sounddevice`
MIC_MIN_RMS = 300  # loudness needed to count as speech; raise in noisy halls
MIC_SILENCE_SECONDS = 0.8  # this much quiet = the person finished their sentence
