# RobotVision

Real-time webcam gesture tracker with spoken feedback.

## Run

```
uv run python -m robotvision.main
```

Press `q` to quit.

## Voice chat setup

1. Get a free API key at https://console.groq.com/keys
2. Copy `.env.example` to `.env` and paste the key: `GROQ_API_KEY=gsk_...`
   (`.env` is gitignored, so the key never ends up on GitHub.)
3. Run the app. When it sees a person it starts listening (HUD shows `Mic: listening`).
   Ask things like "where is the library?" or "how do I pay my fees?".

Speech-to-text is Groq Whisper (`whisper-large-v3-turbo`), and replies come from
`openai/gpt-oss-20b` on Groq. Without a key, the bot still runs with gestures only.

### Campus database

Everything the bot knows about Tongmyong University is in `data/campus.json`: all 48 numbered
places from the official campus map (with Korean names), plus offices, hours, phone numbers,
buses, the shuttle and dorm info from tu.ac.kr. Each entry has a `source`. The bot answers campus
questions **only** from this file; if something isn't there it says so and points to the main office.

Set `robot_location` in the file to where the robot stands (e.g. "inside Main Gate 1, next to the
fountain") and it will give directions from there. `aliases` are the words people might say for a place.

## How it behaves

When someone steps in front of the camera, Nova greets them ("Ohh, hello! How are you?").
After about 5 seconds with nobody in view, it says goodbye. Its replies depend on the
conversation so far, and each reply is picked at random from a few variations.

| Gesture | Response |
|---|---|
| Open palm | "Hii! What can I help you with today?" |
| Wave (palm moving left-right) | "Hey! Waving right back at you!" |
| Victory (V) after it offered help | "Yay, I'm so happy that helped!" |
| Victory (otherwise) | "Peace! Hope you're having a good day." |
| Thumb up / down right after "how are you?" | "Glad you're doing well!" / "Sorry to hear that..." |
| Thumb up / down | "Awesome!" / "Oh no, sorry about that..." |
| Two thumbs up | "You're making me blush!" |
| OK sign | "Perfect, sounds good!" |
| Pointing up | "Ooh, you have a question? I'm all ears." |
| I love you (🤟) | "Aww, love you too!" |
| Closed fist | Goes quiet until it sees an open palm or a wave |

Edit `robotvision/phrases.py` to change what it says. Edit `robotvision/config.py` for its name,
voice (Zira/David), speed, timings and thresholds.

## Architecture

![System architecture](docs/architecture.png)

Regenerate after changes: `python docs/make_architecture.py`

## Layout

```
robotvision/
  main.py            capture -> perceive -> decide -> respond -> draw
  config.py          all settings
  phrases.py         everything the robot says (random variations)
  camera.py          webcam, mirror flip, FPS
  perception/hands.py   MediaPipe GestureRecognizer (VIDEO mode)
  perception/face.py    MediaPipe FaceLandmarker, used to detect a person
  perception/custom_gestures.py   OK sign, two thumbs up, wave
  logic/stabilizer.py   gesture must hold N frames before it counts
  logic/presence.py     person arrived / left events
  logic/behavior.py     personality + conversation state -> phrase
  logic/assistant.py    AI replies (Groq LLM + campus info), background thread
  speech/listener.py    mic -> speech detection -> Groq Whisper, background thread
  knowledge/retriever.py  finds campus entries relevant to a question
data/campus.json        the campus database (edit me)
  feedback/voice.py     pyttsx3 TTS in a background thread
  feedback/overlay.py   hand skeleton + HUD drawing
```
