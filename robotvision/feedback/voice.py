"""Non-blocking text-to-speech using pyttsx3 in a background thread."""

import threading


class Voice:
    def __init__(self, rate=165, enabled=True, voice_name=None, volume=1.0):
        self.enabled = enabled
        self.rate = rate
        self.voice_name = voice_name
        self.volume = volume
        # One "next up" slot: if a phrase arrives while speaking, it waits; if another
        # arrives too, the newest replaces the older one so the robot never lags behind.
        self._pending = None
        self._closed = False
        self._cond = threading.Condition()
        if enabled:
            threading.Thread(target=self._worker, daemon=True).start()

    def say(self, text):
        if not self.enabled:
            return
        with self._cond:
            self._pending = text
            self._cond.notify()

    def _worker(self):
        import pyttsx3

        while True:
            with self._cond:
                while self._pending is None and not self._closed:
                    self._cond.wait()
                if self._closed:
                    return
                text, self._pending = self._pending, None
            try:
                # A fresh engine per phrase avoids pyttsx3's known hang on
                # repeated runAndWait() calls. It must live in this thread (COM).
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                if self.voice_name:
                    for v in engine.getProperty("voices"):
                        if self.voice_name.lower() in v.name.lower():
                            engine.setProperty("voice", v.id)
                            break
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                del engine
            except Exception as e:  # never let TTS kill the vision loop
                print(f"[voice] error: {e}")

    def close(self):
        with self._cond:
            self._closed = True
            self._cond.notify()
