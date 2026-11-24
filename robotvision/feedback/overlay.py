"""On-screen drawing: hand skeletons, labels, FPS, last response."""

import cv2

# MediaPipe hand skeleton connections (landmark index pairs)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),  # pinky + palm
]  # fmt: skip

GREEN = (0, 220, 0)
WHITE = (255, 255, 255)
YELLOW = (0, 220, 255)


def _text(img, text, org, scale=0.7, color=WHITE, thickness=2):
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 3, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def draw_hands(img, hands):
    for hand in hands:
        pts = hand.landmarks
        for a, b in HAND_CONNECTIONS:
            cv2.line(img, pts[a], pts[b], GREEN, 2, cv2.LINE_AA)
        for p in pts:
            cv2.circle(img, p, 3, WHITE, -1, cv2.LINE_AA)
        x = min(p[0] for p in pts)
        y = min(p[1] for p in pts) - 10
        _text(img, f"{hand.handedness}: {hand.gesture} {hand.score:.2f}", (x, max(y, 20)), 0.6)


def draw_faces(img, boxes):
    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(img, (x1, y1), (x2, y2), YELLOW, 2, cv2.LINE_AA)


def draw_hud(img, fps, confirmed, last_phrase, present=False, state=""):
    _text(img, f"FPS: {fps:.0f}", (10, 30))
    _text(img, f"Gesture: {confirmed or '-'}", (10, 60))
    _text(img, f"Person: {'yes' if present else 'no'}   Mood: {state}", (10, 90))
    if last_phrase:
        h = img.shape[0]
        _text(img, f'Robot: "{last_phrase}"', (10, h - 20), 1.0, YELLOW)
    _text(img, "q = quit", (img.shape[1] - 110, 30), 0.6)
