"""The AI part: answers what the person said, using the campus database, in a background
thread so the camera loop never freezes while waiting for the API."""

import queue
import re
import threading
import unicodedata

SYSTEM_PROMPT = """You are {name}, a friendly help robot standing at the entrance of {campus}.
People walk up to you for a quick chat or to ask for directions.

How you talk:
- Your replies are spoken out loud, so use 1 or 2 short, natural sentences. No lists, markdown, emojis or URLs.
- Be warm and casual, like a helpful student volunteer. A little humour is fine.
- Keep conversations short. If the person says thanks or bye, say a short friendly goodbye.

Facts:
- For anything about the campus (places, directions, hours, rules) use ONLY the CAMPUS INFO below.
- If the answer is not in CAMPUS INFO, say you're not sure and suggest asking at {help_desk}. Never make up rooms, directions, times or names.
- Small talk (how are you, jokes, your name) is fine without CAMPUS INFO.
- When giving directions, mention the building number and one or two landmarks; keep it short.
{where}"""

FALLBACK = "Sorry, I'm having a little trouble thinking right now. Could you ask at the reception desk?"


_REPLACEMENTS = {
    "\u00a0": " ", "\u202f": " ", "\u2009": " ",  # odd spaces
    "\u2013": " to ", "\u2014": ", ", "\u2011": "-",  # dashes ("8 AM-8 PM" reads "8 AM to 8 PM")
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2026": "...",
}


def clean_for_speech(text):
    """Make LLM output safe to print on Windows and nice to speak: plain ASCII, no markdown."""
    for a, b in _REPLACEMENTS.items():
        text = text.replace(a, b)
    text = re.sub(r"[*_#`>|]", "", text)  # markdown symbols
    text = unicodedata.normalize("NFKD", text)  # accented letters -> plain ("café" -> "cafe")
    text = text.encode("ascii", "ignore").decode()  # drops emojis and anything exotic
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"\s+([,.!?])", r"\1", text).strip()


class Assistant:
    def __init__(self, client, model, db, robot_name="Nova", history_turns=6, reasoning_effort="low"):
        self.client = client
        self.model = model
        self.db = db
        self.history_turns = history_turns
        self.reasoning_effort = reasoning_effort
        where = getattr(db, "robot_location", "")
        where = (f"- You are standing at: {where}. Give directions starting from there.\n" if where
                 else "- Your exact position on campus is not set, so describe where places are using landmarks "
                      "(Main Gate 1, the fountain, the main road, the big field) rather than turn-by-turn steps.\n")
        self.system = SYSTEM_PROMPT.format(name=robot_name, campus=db.campus_name, help_desk=db.help_desk,
                                           where=where)
        self.history = []  # [{"role": ..., "content": ...}]
        self._last_facts = []  # previous topic, for follow-ups like "when does it close?"
        self.thinking = False
        self.replies = queue.Queue()
        self._questions = queue.Queue()
        self._lock = threading.Lock()
        threading.Thread(target=self._worker, daemon=True).start()

    def ask(self, text):
        self._questions.put(text)

    def note_bot_said(self, text):
        """Record lines the robot said on its own (greetings, gesture replies) for context."""
        with self._lock:
            self.history.append({"role": "assistant", "content": text})
            self._trim()

    def note_user_gesture(self, gesture):
        with self._lock:
            self.history.append({"role": "user", "content": f"(shows a {gesture.replace('_', ' ').lower()} gesture)"})
            self._trim()

    def reset(self):
        """Forget the conversation (call when the person leaves)."""
        with self._lock:
            self.history.clear()
            self._last_facts = []

    def _trim(self):
        del self.history[: max(0, len(self.history) - self.history_turns * 2)]

    def _worker(self):
        while True:
            text = self._questions.get()
            self.thinking = True
            try:
                reply = self._answer(text)
            finally:
                self.thinking = False
            self.replies.put(reply)

    def _answer(self, text):
        facts = self.db.search(text) or self._last_facts  # follow-up: keep the previous topic
        self._last_facts = facts
        if facts:
            info = "CAMPUS INFO:\n" + "\n".join(facts)
        else:
            info = ("CAMPUS INFO: nothing in the database matches this. Do NOT mention any campus place, "
                    "direction, time or facility. If it is a campus question, say you're not sure and "
                    "suggest the help desk; otherwise just chat.")
        with self._lock:
            self.history.append({"role": "user", "content": text})
            self._trim()
            messages = [{"role": "system", "content": self.system},
                        {"role": "system", "content": info}, *self.history]
        try:
            kwargs = {"model": self.model, "messages": messages, "temperature": 0.6, "max_completion_tokens": 600}
            if self.reasoning_effort:
                kwargs["reasoning_effort"] = self.reasoning_effort
            resp = self.client.chat.completions.create(**kwargs)
            reply = clean_for_speech(resp.choices[0].message.content or "") or FALLBACK
        except Exception as e:  # network / rate limit: answer politely instead of crashing  # noqa: BLE001
            print(f"[assistant] API error: {e}")
            reply = FALLBACK
        with self._lock:
            self.history.append({"role": "assistant", "content": reply})
            self._trim()
        return reply
