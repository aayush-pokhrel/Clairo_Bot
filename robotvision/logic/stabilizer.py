"""Turns noisy per-frame gesture labels into clean "gesture started" events."""


class GestureStabilizer:
    def __init__(self, hold_frames=8, min_confidence=0.6):
        self.hold_frames = hold_frames
        self.min_confidence = min_confidence
        self._candidate = None
        self._count = 0
        self.current = None  # the confirmed, currently held gesture (or None)

    def update(self, gesture, score):
        """Feed one frame. Returns the gesture name once when it becomes confirmed."""
        if gesture == "None" or score < self.min_confidence:
            gesture = None

        if gesture == self._candidate:
            self._count += 1
        else:
            self._candidate = gesture
            self._count = 1

        if self._count >= self.hold_frames and self._candidate != self.current:
            self.current = self._candidate
            return self.current  # may be None when the hand goes away
        return None
