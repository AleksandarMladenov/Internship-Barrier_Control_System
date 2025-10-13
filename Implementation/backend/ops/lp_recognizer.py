import os, re, time, argparse, collections, difflib
from datetime import datetime
import cv2
import numpy as np
import requests
from ultralytics import YOLO
import easyocr

# -------------------- CONFIG (env-tunable) --------------------
DEF_REGEX      = r"^[A-Z]{1,2}\d{4}[A-Z]{2}$"      # default: BG-like
API_BASE       = os.environ.get("API_BASE", "http://api:8000")
MODE           = os.environ.get("MODE", "entry")    # "entry" or "exit"
REGION_CODE    = os.environ.get("REGION_CODE", "BG")
GATE_ID        = os.environ.get("GATE_ID", "GATE-A")
YOLO_WEIGHTS   = os.environ.get("YOLO_WEIGHTS", "/assets/best.pt")
YOLO_CONF      = float(os.environ.get("YOLO_CONF", "0.5"))
FRAME_SKIP     = int(os.environ.get("FRAME_SKIP", "2"))

# STABILIZATION / DEDUP
STABLE_FRAMES  = int(os.environ.get("STABLE_FRAMES", "3"))
COOLDOWN_SEC   = int(os.environ.get("COOLDOWN_SEC", "10"))
DEBOUNCE_SEC   = int(os.environ.get("DEBOUNCE_SEC", "8"))
SIM_RATIO      = float(os.environ.get("SIM_RATIO", "0.88"))
VOTE_WINDOW    = int(os.environ.get("VOTE_WINDOW", "8"))

# BBOX sanity
MIN_AR         = float(os.environ.get("MIN_AR", "2.0"))
MAX_AR         = float(os.environ.get("MAX_AR", "6.0"))
MIN_W          = int(os.environ.get("MIN_W", "120"))
MIN_H          = int(os.environ.get("MIN_H", "30"))

# Demo helpers
EXIT_AFTER_FIRST = os.environ.get("EXIT_AFTER_FIRST", "0") == "1"
LOOP             = os.environ.get("LOOP", "0") == "1"

PLATE_REGEX = os.environ.get("PLATE_REGEX", DEF_REGEX)

# -------------------- HELPERS --------------------
def normalize_ocr(s: str) -> str:
    """Uppercase, strip non-alnum, and fix common OCR confusions."""
    s = (s or "").upper().strip().replace(" ", "")
    s = re.sub(r"[^A-Z0-9]", "", s)
    # visual swaps tuned for plates; adjust if country-specific chars matter
    s = (s.replace("İ", "I").replace("Ø", "O")
           .replace("O", "0").replace("Q", "0")
           .replace("I", "1").replace("L", "1")
           .replace("S", "5").replace("B", "8")
           .replace("Z", "2").replace("T", "7"))
    return s

def similar(a: str, b: str, thr: float = SIM_RATIO) -> bool:
    if not a or not b:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= thr

def majority_vote_sim(values: list[str]) -> str | None:
    """Pick a representative string that has the most similar neighbors in the window."""
    if not values:
        return None
    best_val, best_score = None, -1
    for i, v in enumerate(values):
        score = sum(1 for u in values if similar(v, u))
        if score > best_score:
            best_score, best_val = score, v
    return best_val

def post_scan(plate_text: str):
    url = f"{API_BASE}/scans/{MODE}"
    payload = {
        "plate_text": plate_text,
        "region_code": REGION_CODE,
        "gate_id": GATE_ID,
        "captured_at": datetime.utcnow().isoformat() + "Z",
    }
    try:
        r = requests.post(url, json=payload, timeout=5)
        print(f"[API] {url} {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[API ERROR] {e}")

# -------------------- MAIN --------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to video file inside container, e.g. /assets/entry_demo.mp4")
    parser.add_argument("--display", action="store_true", help="Show annotated preview (needs GUI/X11)")
    parser.add_argument("--regex", default=PLATE_REGEX, help="Plate regex or ANY")
    args = parser.parse_args()

    plate_re = None
    if args.regex.upper() != "ANY":
        plate_re = re.compile(args.regex)

    model = YOLO(YOLO_WEIGHTS)
    print(f"[INIT] Loaded YOLO weights: {YOLO_WEIGHTS}")

    reader = easyocr.Reader(["en"], gpu=False)
    print("[INIT] EasyOCR ready")

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {args.video}")

    # state
    frame_idx         = 0
    stable_count      = 0
    last_candidate    = None
    last_sent         = {}
    last_success_ts   = 0.0
    recent_texts      = collections.deque(maxlen=VOTE_WINDOW)

    while True:
        ok, frame = cap.read()
        if not ok:
            if LOOP:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break
        frame_idx += 1
        if FRAME_SKIP > 1 and (frame_idx % FRAME_SKIP != 0):
            continue

        res = model.predict(frame, conf=YOLO_CONF, verbose=False)[0]
        if len(res.boxes) == 0:
            stable_count, last_candidate = 0, None
            if args.display:
                cv2.imshow("LP", frame)
                if cv2.waitKey(1) == 27: break
            continue

        # pick largest plate-like bbox
        boxes = res.boxes.xyxy.cpu().numpy().astype(int)
        areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in boxes]
        b     = boxes[int(np.argmax(areas))]
        x1, y1, x2, y2 = map(int, b)
        w = max(0, x2 - x1); h = max(0, y2 - y1)
        ar = (w / max(1, h))

        if w < MIN_W or h < MIN_H or not (MIN_AR <= ar <= MAX_AR):
            # not plate-like; skip
            if args.display:
                cv2.rectangle(frame, (x1,y1),(x2,y2),(0,0,255),2)
                cv2.putText(frame, f"reject w{w} h{h} ar{ar:.1f}", (x1, max(y1-8,0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
                cv2.imshow("LP", frame)
                if cv2.waitKey(1) == 27: break
            stable_count, last_candidate = 0, None
            continue

        crop = frame[max(y1,0):max(y2,0), max(x1,0):max(x2,0)]
        if crop.size == 0:
            stable_count, last_candidate = 0, None
            continue

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 5, 75, 75)

        result = reader.readtext(gray, detail=0, paragraph=True)
        raw = "".join(result)
        norm = normalize_ocr(raw)

        # generic "ANY" acceptance or pattern-based
        candidate = None
        if args.regex.upper() == "ANY":
            if 4 <= len(norm) <= 10 and sum(c.isdigit() for c in norm) >= 2:
                candidate = norm
        else:
            if norm and plate_re and plate_re.match(norm):
                candidate = norm
            else:
                # try the raw (unmapped) string against regex too
                raw2 = re.sub(r"[^A-Z0-9]", "", raw.upper())
                if raw2 and plate_re and plate_re.match(raw2):
                    candidate = raw2

        # maintain a sliding window of similar candidates for voting
        if candidate:
            recent_texts.append(candidate)
            vote = majority_vote_sim(list(recent_texts)) or candidate
            # stability by similarity: if similar to last_candidate, count up
            if last_candidate and similar(vote, last_candidate):
                stable_count += 1
            else:
                stable_count = 1
            last_candidate = vote
        else:
            stable_count, last_candidate = 0, None

        if args.display:
            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
            cv2.putText(frame, norm or "", (x1, max(y1-8,0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.imshow("LP", frame)
            if cv2.waitKey(1) == 27: break

        # fire once when enough stability AND dedup guards pass
        if stable_count >= STABLE_FRAMES and last_candidate:
            now = time.time()

            # global debounce: prevent bursts
            if now - last_success_ts < DEBOUNCE_SEC:
                continue

            # per-text cooldown (uses fuzzy key merging)
            # find any previously sent plate that's "similar" to this one
            sent_key = None
            for k in list(last_sent.keys()):
                if similar(k, last_candidate):
                    sent_key = k
                    break
            if sent_key is None:
                sent_key = last_candidate

            if now - last_sent.get(sent_key, 0) >= COOLDOWN_SEC:
                print(f"[SCAN] plate={last_candidate} stable={stable_count}")
                post_scan(last_candidate)
                last_sent[sent_key] = now
                last_success_ts = now
                # reset window after success to avoid double-firing on trailing frames
                recent_texts.clear()
                stable_count = 0
                last_candidate = None
                if EXIT_AFTER_FIRST:
                    print("[INFO] EXIT_AFTER_FIRST=1 -> stopping after first POST")
                    break

    cap.release()
    if args.display: cv2.destroyAllWindows()
    print("[DONE]")

if __name__ == "__main__":
    main()
