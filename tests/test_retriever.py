"""Retrieval tests for data/campus.json.

Run:  python tests/test_retriever.py      (prints a report; exit code 1 if anything fails)
  or: pytest tests/                        (if pytest is installed)

Each case is (question, expected entry name). expected=None means "nothing should be found"
(off-topic / small talk), so the AI won't be fed unrelated campus facts.
A case passes if the expected entry is in the top 3 results (that's what the AI receives).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from robotvision.knowledge.retriever import CampusDB  # noqa: E402

CASES = {
    "direct": [
        ("where is the library", "Central Library"),
        ("where is the cafeteria", "Student Welfare Building and Cafeteria"),
        ("where is the main building", "Main Building"),
        ("where is the student union", "Student Union Building"),
        ("where is the graduate school", "Graduate School"),
        ("where is the dormitory", "Dormitory Building 1"),
        ("where is the sports complex", "Sports Complex"),
        ("where is the main gate", "Main Gate 1"),
        ("where is the animal hospital", "University Animal Hospital"),
        ("where is the shuttle bus stop", "Campus Shuttle and Circulation Bus Stop"),
        ("where is the BIC office", "Busan International College Office"),
        ("where is the companion animal building", "Companion Animal Building"),
    ],
    "paraphrase": [
        ("I'm hungry", "Student Welfare Building and Cafeteria"),
        ("where can I get lunch", "Student Welfare Building and Cafeteria"),
        ("is there halal food on campus", "Student Welfare Building and Cafeteria"),
        ("I want to borrow some books", "Central Library"),
        ("where can I study quietly", "Central Library"),
        ("I need a coffee", "Student Cafe"),
        ("where do the professors sit", "Faculty Research Building"),
        ("where can I play tennis", "Sports Complex"),
        ("where can I leave my car", "Parking Lots"),
        ("where do international students go for admission", "International College Building"),
        ("I want to register for my classes", "Busan International College Office"),
        ("where is the computer science department", "ICT Building 1"),
        ("where do I find the career center", "Student Union Building"),
        ("how do I get to Seomyeon", "How do I get here by bus or subway?"),
        ("which subway station is closest", "How do I get here by bus or subway?"),
        ("what time does the school bus come", "Campus Shuttle and Circulation Bus Stop"),
        ("what's the university's address", "What is the address of the university?"),
        ("what is your phone number", "What is the phone number of the university?"),
        ("what can I study here", "What colleges does the university have?"),
        ("how do I apply", "How do I apply as an international student?"),
        ("who runs this university", "Who is the president of the university?"),
        ("I use a wheelchair, is the campus accessible", "Is there help for students with disabilities?"),
        ("how much is the dorm fee", "What are the dormitory rules and hours?"),
        ("what are you", "Who are you / what can you do?"),
    ],
    "typos_and_mishearing": [
        ("where is the libary", "Central Library"),
        ("where is the cafetaria", "Student Welfare Building and Cafeteria"),
        ("where's the dormitry", "Dormitory Building 1"),
        ("where is the admissions ofice", "International College Building"),
        ("where is the startup town", "Green Startup Town and Startup Hub"),
        ("where is the do-ing hall", "Do-ing Hall"),
        ("where is gaon nuri", "Gaonnuri"),
    ],
    "building_numbers": [
        ("where is building 10", "Central Library"),
        ("where is building 17", "International College Building"),
        ("building 8 please", "Student Welfare Building and Cafeteria"),
        ("how do I get to building 19", "Busan International College Office"),
        ("ICT building 1", "ICT Building 1"),
        ("where is ICT 3", "ICT Building 3"),
        ("where is gate 3", "Gate 3"),
    ],
    "off_topic": [
        ("how are you", None),
        ("tell me a joke", None),
        ("what's the weather like today", None),
        ("I'm doing great thanks", None),
        ("what's your favourite colour", None),
        ("thanks, bye", None),
    ],
}


def name_of(entry_text):
    """'PLACE Central Library - ...' -> 'Central Library'"""
    return entry_text.split(" - ", 1)[0].split(" ", 1)[1]


def run(db):
    results = {}
    for group, cases in CASES.items():
        rows = []
        for question, expected in cases:
            found = [name_of(t) for t in db.search(question)]
            if expected is None:
                ok, top1 = not found, not found
            else:
                ok, top1 = expected in found, bool(found) and found[0] == expected
            rows.append((question, expected, found, ok, top1))
        results[group] = rows
    return results


def test_retrieval():
    results = run(CampusDB(ROOT / "data" / "campus.json"))
    failures = [r for rows in results.values() for r in rows if not r[3]]
    assert not failures, "\n".join(f"{q!r}: expected {e!r}, got {f}" for q, e, f, _, _ in failures)


if __name__ == "__main__":
    results = run(CampusDB(ROOT / "data" / "campus.json"))
    total = passed = first = 0
    for group, rows in results.items():
        g_pass = sum(r[3] for r in rows)
        g_first = sum(r[4] for r in rows)
        total += len(rows)
        passed += g_pass
        first += g_first
        print(f"\n{group}: {g_pass}/{len(rows)} found in top 3, {g_first}/{len(rows)} ranked first")
        for question, expected, found, ok, top1 in rows:
            mark = "PASS" if ok else "FAIL"
            note = "" if top1 or not ok else "  (not ranked first)"
            print(f"  {mark}  {question!r:52} -> {found}{note}")
    print(f"\nTOTAL: {passed}/{total} passed (top 3), {first}/{total} ranked first")
    sys.exit(0 if passed == total else 1)
