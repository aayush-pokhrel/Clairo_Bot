import time

import cv2


class Camera:
    """Webcam capture with mirror flip and an FPS counter."""

    def __init__(self, index=0, width=1280, height=720, mirror=True):
        # CAP_DSHOW avoids the slow MSMF startup on Windows
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            raise RuntimeError(f"Camera {index} didn't open - try index 1 or 2")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.mirror = mirror
        self.fps = 0.0
        self._last = time.perf_counter()

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            return None
        if self.mirror:
            frame = cv2.flip(frame, 1)
        now = time.perf_counter()
        dt = now - self._last
        self._last = now
        if dt > 0:
            # exponential moving average keeps the number readable
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt) if self.fps else 1.0 / dt
        return frame

    def release(self):
        self.cap.release()
