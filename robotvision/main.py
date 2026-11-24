"""Main loop: capture -> perceive -> decide -> respond -> draw.

Run from the project root:  uv run python -m robotvision.main
"""

import sys
from pathlib import Path

# Allow running this file directly (e.g. VS Code "Run Python File"), not only via -m.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from robotvision import config
from robotvision.camera import Camera
from robotvision.feedback.overlay import draw_faces, draw_hands, draw_hud
from robotvision.feedback.voice import Voice
from robotvision.logic.behavior import Behavior
from robotvision.logic.presence import PresenceTracker
from robotvision.logic.stabilizer import GestureStabilizer
from robotvision.perception.custom_gestures import WaveDetector, frame_gesture
from robotvision.perception.face import FaceTracker
from robotvision.perception.hands import HandTracker
from robotvision.phrases import PHRASES


def build_chat(voice):
    """Create the listener + AI assistant, or (None, None) if voice chat isn't available."""
    if not config.CHAT_ENABLED:
        return None, None
    if not config.GROQ_API_KEY:
        print("[chat] No GROQ_API_KEY in .env - voice chat off, gestures still work.")
        return None, None
    from groq import Groq

    from robotvision.knowledge.retriever import CampusDB
    from robotvision.logic.assistant import Assistant
    from robotvision.speech.listener import Listener

    client = Groq(api_key=config.GROQ_API_KEY, timeout=15.0)
    db = CampusDB(config.CAMPUS_DB)
    assistant = Assistant(client, config.LLM_MODEL, db, config.ROBOT_NAME, config.HISTORY_TURNS,
                          config.LLM_REASONING_EFFORT)
    try:
        listener = Listener(client, config.STT_MODEL, voice.is_busy, min_rms=config.MIC_MIN_RMS,
                            silence_seconds=config.MIC_SILENCE_SECONDS, device=config.MIC_DEVICE)
    except Exception as e:  # no mic: keep running with gestures only  # noqa: BLE001
        print(f"[chat] Microphone unavailable ({e}) - voice chat off.")
        return None, None
    print(f"[chat] Voice chat on ({config.LLM_MODEL}). Talk when a person is detected.")
    return listener, assistant


def main():
    # Never crash on an unusual character in a print (Windows consoles are not UTF-8).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    camera = Camera(config.CAMERA_INDEX, config.FRAME_WIDTH, config.FRAME_HEIGHT, config.MIRROR)
    hands_tracker = HandTracker(config.GESTURE_MODEL, config.NUM_HANDS)
    face_tracker = FaceTracker(config.FACE_MODEL)
    stabilizer = GestureStabilizer(config.HOLD_FRAMES, config.MIN_CONFIDENCE)
    waves = WaveDetector(config.WAVE_WINDOW_SECONDS, config.WAVE_MIN_SWINGS, config.WAVE_SWING_SIZE)
    presence = PresenceTracker(config.ARRIVE_SECONDS, config.LEAVE_SECONDS)
    behavior = Behavior(PHRASES, config.ROBOT_NAME, config.COOLDOWN_SECONDS, config.GREETING_CONTEXT_SECONDS)
    voice = Voice(config.VOICE_RATE, config.VOICE_ENABLED, config.VOICE_NAME, config.VOICE_VOLUME)
    listener, assistant = build_chat(voice)
    last_phrase = None
    last_heard = None
    faces = []
    frame_no = 0

    def speak(phrase, why, from_ai=False):
        nonlocal last_phrase
        if phrase:
            print(f"[{why}] -> {phrase}")
            last_phrase = phrase
            voice.say(phrase)
            if assistant and not from_ai:
                assistant.note_bot_said(phrase)  # so the AI knows what was already said

    try:
        while True:
            frame = camera.read()
            if frame is None:
                print("Camera returned no frame, stopping.")
                break
            frame_no += 1

            # --- perceive ---
            hands = hands_tracker.process(frame)
            if frame_no % config.FACE_EVERY_N_FRAMES == 0:
                faces = face_tracker.process(frame)

            # --- decide + respond: presence first, so greetings come before gestures ---
            change = presence.update(bool(faces or hands))
            if change == "arrived":
                speak(behavior.on_arrive(), "person arrived")
            elif change == "left":
                speak(behavior.on_leave(), "person left")
                if assistant:
                    assistant.reset()  # next person starts a fresh conversation
                last_heard = None

            if waves.update(hands):
                speak(behavior.on_gesture("Wave"), "gesture Wave")

            label, score = frame_gesture(hands, config.MIN_CONFIDENCE)
            event = stabilizer.update(label, score)
            if event:
                if assistant:
                    assistant.note_user_gesture(event)
                speak(behavior.on_gesture(event), f"gesture {event}")

            # --- voice conversation: listen only while someone is here and not hushed ---
            if listener:
                listener.active = presence.present and behavior.state != "quiet"
                while not listener.transcripts.empty():
                    last_heard = listener.transcripts.get()
                    behavior.on_speech()
                    assistant.ask(last_heard)
                while not assistant.replies.empty():
                    speak(assistant.replies.get(), "ai", from_ai=True)

            # --- draw ---
            draw_faces(frame, faces)
            draw_hands(frame, hands)
            mic = "off"
            if listener and listener.active:
                mic = "thinking..." if assistant.thinking else "hearing you" if listener.hearing else "listening"
            draw_hud(frame, camera.fps, stabilizer.current, last_phrase, presence.present, behavior.state,
                     mic, last_heard)
            cv2.imshow("RobotVision", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        voice.close()
        if listener:
            listener.close()
        hands_tracker.close()
        face_tracker.close()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
