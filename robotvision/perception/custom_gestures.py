"""Extra gestures built on top of MediaPipe's 7 built-in ones.

- OK_Sign: thumb tip touching index tip, other three fingers extended (from landmarks)
- Two_Thumbs_Up: both hands showing Thumb_Up
- Wave: an open palm swinging left-right (from motion over time)
"""

import math
import time
from collections import deque

# MediaPipe hand landmark indices
WRIST, THUMB_TIP, INDEX_TIP = 0, 4, 8
MIDDLE_MCP = 9
FINGERS = [(10, 12), (14, 16), (18, 20)]  # (pip, tip) for middle, ring, pinky


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def hand_size(pts):
    """Wrist to middle-finger knuckle: a scale that doesn't depend on distance to camera."""
    return max(_dist(pts[WRIST], pts[MIDDLE_MCP]), 1.0)


def is_ok_sign(pts):
    size = hand_size(pts)
    pinch = _dist(pts[THUMB_TIP], pts[INDEX_TIP]) < 0.35 * size
    others_extended = all(_dist(pts[WRIST], pts[tip]) > _dist(pts[WRIST], pts[pip]) * 1.1 for pip, tip in FINGERS)
    return pinch and others_extended


def frame_gesture(hands, min_confidence):
    """Pick one gesture label for this frame, including the custom static gestures.

    Returns (label, score). label is "None" when nothing is shown.
    """
    thumbs = [h for h in hands if h.gesture == "Thumb_Up" and h.score >= min_confidence]
    if len(thumbs) >= 2:
        return "Two_Thumbs_Up", min(h.score for h in thumbs)

    for h in hands:
        if is_ok_sign(h.landmarks):
            return "OK_Sign", 1.0

    best = max((h for h in hands if h.gesture != "None"), key=lambda h: h.score, default=None)
    return (best.gesture, best.score) if best else ("None", 0.0)


class WaveDetector:
    """Detects a wave: an open palm whose wrist swings left-right a few times."""

    def __init__(self, window_seconds=1.5, min_swings=2, swing_size=0.4):
        self.window = window_seconds
        self.min_swings = min_swings
        self.swing_size = swing_size
        self._track = deque()  # (time, x in hand-size units)

    def update(self, hands):
        """Feed one frame of hands. Returns True once when a wave is detected."""
        now = time.monotonic()
        palm = next((h for h in hands if h.gesture == "Open_Palm"), None)
        if palm is None:
            self._track.clear()
            return False

        self._track.append((now, palm.landmarks[WRIST][0] / hand_size(palm.landmarks)))
        while self._track and now - self._track[0][0] > self.window:
            self._track.popleft()

        if self._count_swings() >= self.min_swings:
            self._track.clear()
            return True
        return False

    def _count_swings(self):
        """Count direction changes, ignoring jitter smaller than swing_size."""
        xs = [x for _, x in self._track]
        if len(xs) < 3:
            return 0
        s = self.swing_size
        swings, direction, extreme = 0, 0, xs[0]  # direction: 1 right, -1 left, 0 not moving yet
        for x in xs[1:]:
            if direction == 0:
                if abs(x - extreme) > s:
                    direction, extreme = (1 if x > extreme else -1), x
            elif direction == 1:
                if x > extreme:
                    extreme = x
                elif extreme - x > s:  # turned around, now going left
                    swings, direction, extreme = swings + 1, -1, x
            else:
                if x < extreme:
                    extreme = x
                elif x - extreme > s:  # turned around, now going right
                    swings, direction, extreme = swings + 1, 1, x
        return swings
