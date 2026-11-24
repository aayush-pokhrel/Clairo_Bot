"""Microphone -> speech detection -> Groq Whisper transcription, in a background thread.

Audio frames come from a queue, so the source can be swapped later (e.g. audio streamed
from the ESP32 over Wi-Fi) without touching the speech logic: just call feed(frame).
"""

import io
import queue
import threading
import time
import wave

import numpy as np

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000

# Whisper tends to "hear" these in silence or noise; ignore them.
HALLUCINATIONS = {"", "you", "thank you", "thank you.", "thanks for watching", "thanks for watching!", ".", "bye", "okay"}


class Listener:
    def __init__(self, client, model, is_bot_speaking, min_rms=300, silence_seconds=0.8,
                 max_seconds=12.0, min_speech_seconds=0.4, start_mic=True, device=None):
        self.client = client
        self.model = model
        self.is_bot_speaking = is_bot_speaking  # callable -> bool, used to avoid hearing itself
        self.min_rms = min_rms
        self.silence_frames = int(silence_seconds * 1000 / FRAME_MS)
        self.max_frames = int(max_seconds * 1000 / FRAME_MS)
        self.min_speech_frames = int(min_speech_seconds * 1000 / FRAME_MS)
        self.active = False  # main loop turns this on only while a person is present
        self.hearing = False  # True while the user is mid-sentence (for the HUD)
        self.transcripts = queue.Queue()
        self._frames = queue.Queue(maxsize=500)
        self._stream = None
        self._stop = False
        threading.Thread(target=self._worker, daemon=True).start()
        if start_mic:
            self._start_mic(device)

    def _start_mic(self, device):
        import sounddevice as sd

        def callback(indata, _frames, _time, _status):
            self.feed(indata[:, 0].copy())

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=FRAME_SAMPLES,
            device=device, callback=callback,
        )
        self._stream.start()

    def feed(self, frame):
        """Push one frame of 16 kHz mono int16 samples."""
        try:
            self._frames.put_nowait(frame)
        except queue.Full:
            pass

    def _worker(self):
        noise = float(self.min_rms)
        speech, voiced, silent = [], 0, 0
        preroll = []
        while not self._stop:
            try:
                frame = self._frames.get(timeout=0.5)
            except queue.Empty:
                continue

            if not self.active or self.is_bot_speaking():
                speech, voiced, silent, preroll = [], 0, 0, []
                self.hearing = False
                continue

            rms = float(np.sqrt(np.mean(frame.astype(np.float32) ** 2)))
            threshold = max(self.min_rms, noise * 2.5)
            loud = rms > threshold

            if not speech:
                preroll = (preroll + [frame])[-10:]  # keep ~0.3 s before speech starts
                if loud:
                    voiced += 1
                    if voiced >= 3:
                        speech, silent = list(preroll), 0
                        self.hearing = True
                else:
                    voiced = 0
                    noise = 0.95 * noise + 0.05 * rms  # adapt to the room's background noise
                continue

            speech.append(frame)
            silent = 0 if loud else silent + 1
            if silent >= self.silence_frames or len(speech) >= self.max_frames:
                self.hearing = False
                if len(speech) - silent >= self.min_speech_frames:
                    self._transcribe(np.concatenate(speech))
                speech, voiced, silent, preroll = [], 0, 0, []

    def _transcribe(self, samples):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(samples.tobytes())
        try:
            t0 = time.perf_counter()
            result = self.client.audio.transcriptions.create(
                file=("speech.wav", buf.getvalue()),
                model=self.model,
                language="en",
                response_format="verbose_json",
                temperature=0.0,
            )
        except Exception as e:  # network trouble must not kill the robot  # noqa: BLE001
            print(f"[listen] transcription failed: {e}")
            return
        text = (result.text or "").strip()
        segments = getattr(result, "segments", None) or []
        probs = [s.get("no_speech_prob", 0) if isinstance(s, dict) else getattr(s, "no_speech_prob", 0) for s in segments]
        if probs and sum(probs) / len(probs) > 0.6:
            return  # Whisper itself thinks this was not speech
        if text.lower().strip(" .!?") in {h.strip(" .!?") for h in HALLUCINATIONS}:
            return
        print(f"[heard in {time.perf_counter() - t0:.1f}s] {text}")
        self.transcripts.put(text)

    def close(self):
        self._stop = True
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
