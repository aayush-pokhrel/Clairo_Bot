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


def main():
    camera = Camera(config.CAMERA_INDEX, config.FRAME_WIDTH, config.FRAME_HEIGHT, config.MIRROR)
    hands_tracker = HandTracker(config.GESTURE_MODEL, config.NUM_HANDS)
    face_tracker = FaceTracker(config.FACE_MODEL)
    stabilizer = GestureStabilizer(config.HOLD_FRAMES, config.MIN_CONFIDENCE)
    waves = WaveDetector(config.WAVE_WINDOW_SECONDS, config.WAVE_MIN_SWINGS, config.WAVE_SWING_SIZE)
    presence = PresenceTracker(config.ARRIVE_SECONDS, config.LEAVE_SECONDS)
    behavior = Behavior(PHRASES, config.ROBOT_NAME, config.COOLDOWN_SECONDS, config.GREETING_CONTEXT_SECONDS)
    voice = Voice(config.VOICE_RATE, config.VOICE_ENABLED, config.VOICE_NAME, config.VOICE_VOLUME)
    last_phrase = None
    faces = []
    frame_no = 0

    def speak(phrase, why):
        nonlocal last_phrase
        if phrase:
            print(f"[{why}] -> {phrase}")
            last_phrase = phrase
            voice.say(phrase)

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

            if waves.update(hands):
                speak(behavior.on_gesture("Wave"), "gesture Wave")

            label, score = frame_gesture(hands, config.MIN_CONFIDENCE)
            event = stabilizer.update(label, score)
            if event:
                speak(behavior.on_gesture(event), f"gesture {event}")

            # --- draw ---
            draw_faces(frame, faces)
            draw_hands(frame, hands)
            draw_hud(frame, camera.fps, stabilizer.current, last_phrase, presence.present, behavior.state)
            cv2.imshow("RobotVision", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        voice.close()
        hands_tracker.close()
        face_tracker.close()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
