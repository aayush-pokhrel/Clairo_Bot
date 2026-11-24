"""Draws docs/architecture.png. Re-run after changing the system:  python docs/make_architecture.py"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent / "architecture.png"

# --- palette: fill, border ---
IO = ("#E8EEF6", "#5B7BA6")  # hardware in/out
ML = ("#E3F4E8", "#3E9A5B")  # local ML model (MediaPipe)
RULE = ("#FFF3DF", "#C98A1B")  # rule-based logic written in this project
CLOUD = ("#EFE7FB", "#7B52C7")  # Groq cloud AI
DATA = ("#FDEDEF", "#C2566B")  # data files
INK = "#1F2733"
MUTED = "#55606E"
RED = "#B03A48"

fig = plt.figure(figsize=(34, 24), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 34)
ax.set_ylim(0, 24)
ax.axis("off")
fig.patch.set_facecolor("white")


def box(x, y, w, h, colors, title, sub=None, lines=(), title_size=16.5):
    fill, edge = colors
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.18",
                                fc=fill, ec=edge, lw=2.4, zorder=2))
    ty = y + h - 0.3
    ax.text(x + 0.22, ty, title, fontsize=title_size, weight="bold", color=INK, va="top", zorder=3)
    ty -= 0.55
    if sub:
        ax.text(x + 0.22, ty, sub, fontsize=12.5, style="italic", color=edge, va="top", zorder=3)
        ty -= 0.5
    for line in lines:
        ax.text(x + 0.22, ty, line, fontsize=13, color=INK, va="top", zorder=3)
        ty -= 0.43


def _style(color, dashed):
    return dict(color=color, lw=2.2, linestyle=(0, (5, 4)) if dashed else "-", zorder=4)


def arrow(p, q, color=INK, dashed=False, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=24, connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=1, shrinkB=1, **_style(color, dashed)))


def path(points, color=INK, dashed=False):
    """Right-angled arrow through the given points (arrowhead on the last segment)."""
    xs, ys = zip(*points[:-1])
    ax.plot(xs, ys, solid_capstyle="round", **_style(color, dashed))
    arrow(points[-2], points[-1], color, dashed)


def label(x, y, text, color=INK, size=12, rot=0):
    ax.text(x, y, text, fontsize=size, color=color, ha="center", va="center", rotation=rot, zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.95))


def lane(y0, y1, name):
    ax.add_patch(FancyBboxPatch((0.25, y0), 33.5, y1 - y0, boxstyle="round,pad=0,rounding_size=0.1",
                                fc="#F7F8FA", ec="#D9DDE3", lw=1, zorder=0))
    ax.text(0.62, (y0 + y1) / 2, name, rotation=90, fontsize=16, weight="bold", color="#8A94A3",
            va="center", ha="center", zorder=1)


# ---------------- title ----------------
ax.text(17, 23.45, "Clairo Bot (RobotVision): system architecture", fontsize=32, weight="bold",
        color=INK, ha="center", va="center")
ax.text(17, 22.85, "Tongmyong University help robot: sees people and gestures, listens, answers campus "
        "questions from its own database, and speaks back", fontsize=16, color=MUTED, ha="center", va="center")

# ---------------- lanes ----------------
lane(19.6, 22.35, "INPUT")
lane(13.75, 19.4, "PERCEPTION")
lane(7.4, 13.55, "DECISION")
lane(3.35, 7.2, "OUTPUT")

# Groq cloud region
ax.add_patch(FancyBboxPatch((28.4, 7.6), 5.15, 11.6, boxstyle="round,pad=0,rounding_size=0.25",
                            fc="none", ec=CLOUD[1], lw=2.2, ls=(0, (6, 4)), zorder=1))
ax.text(30.97, 8.25, "Groq cloud (internet)", fontsize=14, weight="bold", color=CLOUD[1], ha="center", va="center")
ax.text(30.97, 7.85, "free API key, .env.example (gitignored)", fontsize=11.5, color=CLOUD[1],
        ha="center", va="center")

# ---------------- INPUT ----------------
box(1.5, 19.85, 6.4, 2.25, IO, "Webcam", "OpenCV VideoCapture (DirectShow)",
    ["1280x720 frames, mirrored, ~30 FPS"])
box(16.6, 19.85, 6.4, 2.25, IO, "Microphone", "sounddevice InputStream",
    ["16 kHz mono, 30 ms frames (480 samples)"])

# ---------------- PERCEPTION ----------------
PY, PH = 14.0, 4.6
box(1.5, PY, 5.7, PH, ML, "MediaPipe GestureRecognizer", "gesture_recognizer.task, up to 2 hands",
    ["1. Palm detector finds each hand",
     "2. Landmark model: 21 3D hand points",
     "3. Classifier: 1 of 7 gestures + score",
     "   (palm, victory, thumb up/down,",
     "    point up, fist, I-love-you)",
     "Out: gesture, score, side, 21 points"])
box(7.9, PY, 4.3, PH, RULE, "Custom gestures", "custom_gestures.py",
    ["OK sign: thumb tip touches",
     "  index tip, 3 fingers out",
     "Two thumbs up: 2 hands",
     "Wave: wrist swings left/right",
     "  >= 2 times within 1.5 s",
     "Out: 1 label/frame + Wave"])
box(12.9, PY, 2.95, PH, ML, "MediaPipe Face", "face_landmarker",
    ["Every 2nd frame",
     "478 face points",
     "  -> face box",
     "Answers only:",
     "'is someone here?'"], title_size=15)
box(16.6, PY, 5.4, PH, RULE, "Speech detector (VAD)", "listener.py, own thread",
    ["Loudness (RMS) of each frame",
     "Noise floor adapts to the room",
     "Start: 3 frames > 2.5 x noise",
     "  (+ 0.3 s kept from before)",
     "End: 0.8 s silence (max 12 s)",
     "Out: WAV clip in memory"])
box(22.6, PY, 5.3, PH, RULE, "Transcript filter", "listener.py",
    ["Drop if Whisper says it is",
     "  probably not speech",
     "  (no_speech_prob > 0.6)",
     "Drop noise hallucinations",
     "  ('Thank you.', 'you', ...)",
     "Out: what the person said"])
box(28.75, PY, 4.45, 3.75, CLOUD, "Whisper", "whisper-large-v3-turbo",
    ["Speech -> English text",
     "+ per-segment",
     "  no_speech_prob",
     "~0.4 s per sentence"])

# ---------------- DECISION ----------------
SY, SH = 10.25, 3.05
box(12.35, SY, 3.5, SH, RULE, "Presence", "presence.py",
    ["face OR hand seen",
     "arrived: 0.8 s",
     "left: 5 s gone"], title_size=15.5)
box(1.5, SY, 3.9, SH, RULE, "Stabilizer", "stabilizer.py",
    ["same label 8 frames",
     "score >= 0.6",
     "fires once per change"], title_size=15.5)
box(6.0, 7.65, 5.75, 5.65, RULE, "Behavior (personality)", "behavior.py + phrases.py",
    ["States: away -> chatting ->",
     "  offered_help, or quiet (fist)",
     "Arrive: 'Ohh, hello! How are you?'",
     "Palm: 'What can I help you with?'",
     "Victory after help: 'Glad it helped!'",
     "Thumb up/down right after greeting",
     "  = answer to 'how are you?'",
     "Fist: quiet until palm or wave",
     "Random phrase, 4 s cooldown"])
box(16.6, 10.25, 5.4, 3.05, RULE, "Retriever", "retriever.py, keyword scoring",
    ["+3 phrase  +2 word  +1 typo",
     "Top 3 entries -> CAMPUS INFO",
     "Nothing found -> AI is told",
     "  to state no campus facts"])
box(16.6, 7.65, 5.4, 2.2, DATA, "data/campus.json", None,
    ["38 places + 10 FAQs (TU map,", "tu.ac.kr), each with a source"], title_size=15)
box(22.6, 7.65, 5.3, 5.65, RULE, "Assistant", "assistant.py, own thread",
    ["Request sent to the LLM:",
     "1. persona + rules (short, spoken,",
     "   campus facts ONLY from info)",
     "2. CAMPUS INFO (top 3)",
     "3. last 6 turns, incl. robot's",
     "   greetings + user's gestures",
     "Follow-up? reuse last topic",
     "Reply -> plain speakable text",
     "No network -> polite fallback"])
box(28.75, 8.95, 4.45, 4.35, CLOUD, "LLM", "openai/gpt-oss-20b",
    ["Chat completion",
     "reasoning effort: low",
     "temperature 0.6",
     "1-2 sentence reply",
     "~0.5 s per answer"])

# ---------------- OUTPUT ----------------
box(1.5, 3.6, 7.6, 3.35, IO, "Screen (OpenCV window)", "overlay.py",
    ["Hand skeletons + face boxes, FPS",
     "Gesture, person here?, mood (state)",
     "Mic: listening / hearing you / thinking",
     "Captions: 'You: ...' and 'Robot: ...'"])
box(10.1, 3.6, 7.3, 3.35, IO, "Voice: text-to-speech", "pyttsx3 + Windows SAPI5 (Zira), offline",
    ["165 words/min, own thread",
     "1 waiting slot: newest phrase wins",
     "is_busy(): speaking, or < 0.6 s after",
     "  -> mic muted (red line)"])
box(18.4, 4.35, 3.4, 1.9, IO, "Speaker", None, ["robot's voice"], title_size=15)

# ---------------- arrows: vision ----------------
arrow((4.35, 19.85), (4.35, 18.6)); label(4.35, 19.25, "frame")
arrow((7.9, 20.9), (14.35, 18.6), rad=-0.18); label(11.6, 20.25, "every 2nd frame")
arrow((7.2, 16.3), (7.9, 16.3)); label(7.55, 16.75, "hands", size=11)
arrow((8.4, 14.0), (4.4, 13.3)); label(6.4, 13.65, "gesture label per frame", size=11)
arrow((11.0, 14.0), (11.0, 13.3)); label(11.0, 13.65, "Wave", size=11)
arrow((14.35, 14.0), (14.35, 13.3)); label(14.35, 13.65, "faces (+ hands)", size=11)
arrow((5.4, 11.8), (6.0, 11.8))
label(3.45, 9.85, "confirmed gesture ->", size=11.5)
arrow((12.35, 11.8), (11.75, 11.8))
label(14.1, 9.85, "<- arrived / left", size=11.5)

# ---------------- arrows: voice ----------------
arrow((19.8, 19.85), (19.8, 18.6)); label(19.8, 19.25, "audio frames")
path([(21.3, 18.6), (21.3, 19.1), (30.97, 19.1), (30.97, 17.75)])
label(26.0, 19.1, "WAV clip over HTTPS", color=CLOUD[1])
arrow((28.75, 16.0), (27.9, 16.0)); label(28.33, 16.4, "text", size=11, color=CLOUD[1])
arrow((25.25, 14.0), (25.25, 13.3)); label(25.25, 13.65, "user's words", size=11)

# ---------------- arrows: knowledge + LLM ----------------
arrow((22.6, 12.3), (22.0, 12.3)); arrow((22.0, 11.0), (22.6, 11.0))
label(22.3, 11.65, "ask / top 3", size=10.5, rot=90)
arrow((19.3, 9.85), (19.3, 10.25)); label(20.4, 10.05, "reads", size=10.5)
arrow((27.9, 12.4), (28.75, 12.4)); label(28.33, 12.8, "msgs", size=11, color=CLOUD[1])
arrow((28.75, 9.6), (27.9, 9.6)); label(28.33, 9.2, "reply", size=11, color=CLOUD[1])

# ---------------- arrows: to output ----------------
arrow((11.0, 7.65), (11.0, 6.95)); label(11.0, 7.3, "phrase", size=11.5)
path([(25.25, 7.65), (25.25, 7.3), (16.9, 7.3), (16.9, 6.95)])
label(21.0, 7.3, "AI reply", size=11.5)
arrow((17.4, 5.3), (18.4, 5.3))
arrow((7.5, 7.65), (7.5, 6.95), color=MUTED, dashed=True); label(7.5, 7.3, "state, text", size=11, color=MUTED)

# ---------------- mic gating (red) ----------------
path([(16.05, 6.95), (16.05, 17.6), (16.6, 17.6)], color=RED, dashed=True)
label(16.22, 10.6, "robot speaking -> mic off", size=11, color=RED, rot=90)
path([(15.85, 12.9), (16.35, 12.9), (16.35, 15.0), (16.6, 15.0)], color=RED, dashed=True)
label(16.33, 13.95, "here + not quiet", size=10, color=RED, rot=90)

# ---------------- bottom: legend, threads, example ----------------
ax.text(0.6, 2.85, "Legend", fontsize=15, weight="bold", color=INK, va="center")
items = [(IO, "Hardware in/out"), (ML, "Local ML model (MediaPipe, CPU)"), (RULE, "Our code (rules / logic)"),
         (CLOUD, "Cloud AI (Groq)"), (DATA, "Data file")]
lx = 2.1
for (fill, edge), name in items:
    ax.add_patch(FancyBboxPatch((lx, 2.65), 0.45, 0.4, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=fill, ec=edge, lw=2))
    ax.text(lx + 0.6, 2.85, name, fontsize=13, color=INK, va="center")
    lx += 0.6 + len(name) * 0.118 + 0.45
ax.plot([0.6, 1.4], [2.05, 2.05], color=INK, lw=2.2)
ax.text(1.55, 2.05, "data flow", fontsize=13, va="center")
ax.plot([3.3, 4.1], [2.05, 2.05], color=RED, lw=2.2, ls=(0, (5, 4)))
ax.text(4.25, 2.05, "mic on/off: on only while someone is here, not in quiet mode, and the robot is silent",
        fontsize=13, va="center")
ax.plot([0.6, 1.4], [1.45, 1.45], color=MUTED, lw=2.2, ls=(0, (5, 4)))
ax.text(1.55, 1.45, "state shown on screen", fontsize=13, va="center")

ax.text(0.6, 0.85, "4 threads, joined by queues: main loop (camera, perception, decision, screen), listener "
        "(VAD + Whisper), assistant (retrieval + LLM), voice (TTS). The camera never waits for the network.",
        fontsize=13, color=MUTED, va="center")
ax.text(0.6, 0.35, "No API key or no internet: gestures, greetings and the screen keep working; only voice chat "
        "turns off.", fontsize=13, color=MUTED, va="center")

ex = ("Example, \"where is the libary?\"\n"
      "1. VAD cuts a 1.2 s clip   2. Whisper (0.4 s): \"Where is the library?\"\n"
      "3. Retriever: Central Library, building 10   4. gpt-oss-20b (0.5 s):\n"
      "   \"The Central Library is building 10, at the top of the main road.\"\n"
      "5. Zira speaks it, mic muted meanwhile.   About 1-2 s end to end.")
ax.text(22.6, 2.0, ex, fontsize=12.5, color=INK, va="center", ha="left", linespacing=1.5,
        bbox=dict(boxstyle="round,pad=0.45", fc="#FFFBEA", ec=RULE[1], lw=1.6))

fig.savefig(OUT, dpi=100, facecolor="white")
print(f"saved {OUT}")
