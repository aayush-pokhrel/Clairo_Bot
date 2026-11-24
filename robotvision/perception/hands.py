"""Hand gesture perception using MediaPipe's GestureRecognizer (VIDEO mode)."""

import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class Hand:
    gesture: str  # e.g. "Open_Palm", "None"
    score: float
    handedness: str  # "Left" / "Right"
    landmarks: list  # 21 (x, y) pixel coordinates


class HandTracker:
    def __init__(self, model_path, num_hands=2):
        options = vision.GestureRecognizerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(options)
        self._t0 = time.perf_counter()
        self._last_ts = -1

    def process(self, frame_bgr):
        """Return a list of Hand for the given BGR frame (may be empty)."""
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # VIDEO mode needs strictly increasing timestamps in ms
        ts = int((time.perf_counter() - self._t0) * 1000)
        if ts <= self._last_ts:
            ts = self._last_ts + 1
        self._last_ts = ts

        result = self.recognizer.recognize_for_video(image, ts)

        hands = []
        for i, lms in enumerate(result.hand_landmarks):
            gesture, score = "None", 0.0
            if i < len(result.gestures) and result.gestures[i]:
                top = result.gestures[i][0]
                gesture, score = top.category_name, top.score
            side = "?"
            if i < len(result.handedness) and result.handedness[i]:
                side = result.handedness[i][0].category_name
            points = [(int(lm.x * w), int(lm.y * h)) for lm in lms]
            hands.append(Hand(gesture, score, side, points))
        return hands

    def close(self):
        self.recognizer.close()
