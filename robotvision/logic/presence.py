"""Turns per-frame "is someone there?" into clean arrived / left events."""

import time


class PresenceTracker:
    def __init__(self, arrive_seconds=0.8, leave_seconds=5.0):
        self.arrive_seconds = arrive_seconds
        self.leave_seconds = leave_seconds
        self.present = False
        self._seen_since = None
        self._missing_since = None

    def update(self, visible):
        """Feed one frame. Returns "arrived", "left", or None."""
        now = time.monotonic()
        if visible:
            self._missing_since = None
            if self._seen_since is None:
                self._seen_since = now
            if not self.present and now - self._seen_since >= self.arrive_seconds:
                self.present = True
                return "arrived"
        else:
            self._seen_since = None
            if self._missing_since is None:
                self._missing_since = now
            if self.present and now - self._missing_since >= self.leave_seconds:
                self.present = False
                return "left"
        return None
