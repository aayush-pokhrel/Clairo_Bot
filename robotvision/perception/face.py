"""Person detection via MediaPipe FaceLandmarker (VIDEO mode). Returns face boxes."""

import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class FaceTracker:
    def __init__(self, model_path, num_faces=1):
        options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=num_faces,
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        self._t0 = time.perf_counter()
        self._last_ts = -1

    def process(self, frame_bgr):
        """Return a list of (x1, y1, x2, y2) pixel boxes, one per detected face."""
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        ts = int((time.perf_counter() - self._t0) * 1000)
        if ts <= self._last_ts:
            ts = self._last_ts + 1
        self._last_ts = ts

        result = self.landmarker.detect_for_video(image, ts)
        boxes = []
        for lms in result.face_landmarks:
            xs = [lm.x for lm in lms]
            ys = [lm.y for lm in lms]
            boxes.append((int(min(xs) * w), int(min(ys) * h), int(max(xs) * w), int(max(ys) * h)))
        return boxes

    def close(self):
        self.landmarker.close()
