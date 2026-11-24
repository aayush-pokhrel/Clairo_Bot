"""The robot's personality: decides what to say based on the gesture AND the conversation so far.

States:
    away          nobody here
    chatting      greeted the person, nothing pending
    offered_help  asked "what can I help you with?" -> a victory sign now means "got it, thanks"
    quiet         user showed a fist; only an open palm / wave wakes it up
"""

import random
import time

HELLO_GESTURES = ("Open_Palm", "Wave")
# Gestures in the same group share one cooldown, so a wave right after an open palm
# doesn't trigger two hellos in a row.
COOLDOWN_GROUP = {"Open_Palm": "hello", "Wave": "hello"}


class Behavior:
    def __init__(self, phrases, robot_name="Nova", cooldown=4.0, greeting_context=12.0):
        self.phrases = phrases
        self.robot_name = robot_name
        self.cooldown = cooldown
        self.greeting_context = greeting_context
        self.state = "away"
        self._met_before = False
        self._greeted_at = -1e9
        self._last_said = {}  # cooldown key -> time
        self._last_pick = {}  # phrase key -> last phrase used

    # --- presence ---

    def on_arrive(self):
        if self.state != "away":
            return None  # already greeted (e.g. a gesture came first)
        return self._greet()

    def on_leave(self):
        was_quiet = self.state == "quiet"
        self.state = "away"
        return None if was_quiet else self._pick("goodbye")

    # --- gestures ---

    def on_gesture(self, gesture):
        """Return a phrase to say, or None if nothing should be said."""
        if self.state == "away":
            # Someone is gesturing before presence kicked in: greet them first.
            return self._greet()

        if self.state == "quiet":
            if gesture in HELLO_GESTURES and self._off_cooldown(gesture):
                self.state = "offered_help"
                return self._pick("wake_up")
            return None

        if gesture not in self.phrases or not self._off_cooldown(gesture):
            return None

        just_greeted = time.monotonic() - self._greeted_at < self.greeting_context

        if gesture == "Thumb_Up" and just_greeted:
            self._greeted_at = -1e9  # question answered
            return self._pick("doing_well")
        if gesture == "Thumb_Down" and just_greeted:
            self._greeted_at = -1e9
            return self._pick("doing_badly")

        if gesture == "Victory":
            if self.state == "offered_help":
                self.state = "chatting"
                return self._pick("Victory")
            return self._pick("Victory_no_context")

        if gesture == "Open_Palm":
            self.state = "offered_help"
        elif gesture == "Closed_Fist":
            self.state = "quiet"
        return self._pick(gesture)

    # --- helpers ---

    def _greet(self):
        self.state = "chatting"
        self._greeted_at = time.monotonic()
        key = "greeting" if self._met_before else "first_greeting"
        self._met_before = True
        # Count the greeting as a hello so a palm right after doesn't say hi twice.
        self._last_said["hello"] = time.monotonic()
        return self._pick(key)

    def _off_cooldown(self, gesture):
        key = COOLDOWN_GROUP.get(gesture, gesture)
        now = time.monotonic()
        if now - self._last_said.get(key, -1e9) < self.cooldown:
            return False
        self._last_said[key] = now
        return True

    def _pick(self, key):
        options = self.phrases[key]
        choices = [p for p in options if p != self._last_pick.get(key)] or options
        phrase = random.choice(choices)
        self._last_pick[key] = phrase
        return phrase.format(name=self.robot_name)
