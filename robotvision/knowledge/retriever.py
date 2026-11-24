"""Finds the campus entries relevant to a question.

The data is a small JSON file (data/campus.json), so plain keyword matching with a
bit of fuzziness (to survive speech-recognition typos) is enough; no vector DB needed.
Swap this class out later if the database moves to SQLite / an online DB: the rest of
the code only calls search() and the two attributes below.
"""

import difflib
import json
import re

STOPWORDS = {
    "a", "an", "the", "is", "are", "where", "what", "how", "can", "i", "do", "to", "of",
    "in", "on", "me", "my", "you", "your", "please", "tell", "find", "get", "go", "there",
    "it", "for", "and", "at", "be", "this", "that", "with", "when", "does", "which", "hi", "hello",
    "building", "number", "no", "room", "doing", "want", "need", "know", "any", "some", "here", "near", "nearest",
}  # fmt: skip

SKIP_FIELDS = {"name", "aliases", "source"}  # not useful to the LLM (source stays in the JSON for humans)


def _words(text):
    """Lowercase content words. Drops filler words and 1-letter fragments ("what's" -> "what", "s"),
    but keeps single digits so "building 8" still works."""
    return [w for w in re.findall(r"[a-z0-9\-]+", text.lower())
            if w not in STOPWORDS and (len(w) > 1 or w.isdigit())]


class CampusDB:
    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.campus_name = data.get("campus_name", "the university")
        self.help_desk = data.get("help_desk", "the reception desk")
        self.robot_location = data.get("robot_location", "")
        self.entries = []  # (search_terms, vocabulary, text_for_llm)
        for p in data.get("places", []):
            terms = [p["name"], *p.get("aliases", [])]
            fields = [f"{k.replace('_', ' ')}: {v}" for k, v in p.items()
                      if k not in SKIP_FIELDS and v and isinstance(v, str)]
            self._add(terms, f"PLACE {p['name']} - " + "; ".join(fields))
        for q in data.get("faq", []):
            terms = [q["question"], *q.get("keywords", [])]
            self._add(terms, f"FAQ {q['question']} - {q['answer']}")

    def _add(self, terms, text):
        terms = [t.lower() for t in terms if t]
        vocab = {w for t in terms for w in _words(t)}  # each word counted once per entry
        self.entries.append((terms, vocab, text))

    def search(self, query, k=3):
        """Return up to k entry texts relevant to the query (may be empty).

        Score per entry:
          +3  a whole multi-word alias appears in the question ("computer lab", "what are you")
          +2  per question word that exactly matches a word of the entry
          +1  per question word that is a close misspelling of one ("libary" ~ "library", 85% similar)
          +1  bonus if a question word IS a one-word alias on its own ("dormitory", "car")
        Each question word scores once per entry, so repeating a word in many aliases
        doesn't inflate the score.
        """
        q = " " + re.sub(r"[^a-z0-9\- ]", " ", query.lower()) + " "
        q_words = _words(query)
        scored = []
        for terms, vocab, text in self.entries:
            score = 0.0
            for t in terms:
                if " " in t and f" {t} " in q:
                    score += 3
            for qw in q_words:
                if qw in vocab:
                    score += 2
                    if qw in terms:
                        score += 1
                elif len(qw) > 3 and any(len(w) > 3 and difflib.SequenceMatcher(None, qw, w).ratio() >= 0.85
                                         for w in vocab):
                    score += 1
            if score > 0:
                scored.append((score, text))
        scored.sort(key=lambda s: -s[0])  # stable: ties keep file order
        return [text for _, text in scored[:k]]
