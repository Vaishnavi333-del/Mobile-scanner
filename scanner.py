import cv2
import numpy as np
import time
import os
from PIL import Image


# -------- SESSION PDF CREATION --------
def create_pdf_session(files, prefix="multi_"):
    if not files:
        print("No images to create PDF!")
        return

    # Sort by number in filename
    files = sorted(files, key=lambda x: int(x.split("_")[1].split(".")[0]))

    images = [Image.open(f).convert("RGB").rotate(-90, expand=True) for f in files]

    # Generate unique PDF name to avoid overwriting
    pdf_count = 1
    while os.path.exists(f"{prefix}session{pdf_count}.pdf"):
        pdf_count += 1
    pdf_name = f"{prefix}session{pdf_count}.pdf"

    images[0].save(pdf_name, save_all=True, append_images=images[1:])
    print("Session PDF created:", pdf_name)


# -------- ORDER POINTS --------
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


# -------- PERSPECTIVE --------
def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    wA = np.linalg.norm(br - bl)
    wB = np.linalg.norm(tr - tl)
    hA = np.linalg.norm(tr - br)
    hB = np.linalg.norm(tl - bl)
    maxW = max(int(wA), int(wB))
    maxH = max(int(hA), int(hB))
    dst = np.array([[0, 0], [maxW - 1, 0], [maxW - 1, maxH - 1], [0, maxH - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxW, maxH))


# -------- FOCUS CHECK --------
def is_in_focus(img, threshold=120):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var() > threshold


# -------- RECTANGLE DETECTION --------
def detect_rectangles(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, 11, 17, 17)
    v = np.median(blur)
    lower = int(max(0, 0.66 * v))
    upper = int(min(255, 1.33 * v))
    edges = cv2.Canny(blur, lower, upper)
    kernel = np.ones((5, 5), np.uint8)
    edges = cv2.dilate(edges, kernel)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rectangles = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 15000:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            rectangles.append((area, approx.reshape(4, 2)))
    rectangles = sorted(rectangles, key=lambda x: x[0], reverse=True)
    return [r[1] for r in rectangles]


# -------- VIDEO MODE WITH DUPLICATE DETECTION --------
def video_mode():
    cap = cv2.VideoCapture("http://192.168.0.225:8080/video")
    HOLD_TIME = 1
    hold_start = None
    count = 1
    last_scan = None
    SIMILARITY_THRESHOLD = 15
    captured_this_hold = False
    captured = False
    capture_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rects = detect_rectangles(frame)
        status = "Searching..."

        if len(rects) > 0:
            rect = rects[0]
            scan = four_point_transform(frame, rect)
            focused = is_in_focus(scan)
            color = (0, 255, 0) if focused else (0, 0, 255)
            cv2.drawContours(frame, [rect.astype(int)], -1, color, 3)

            if not focused:
                status = "Adjust Focus"
                hold_start = None
                captured_this_hold = False
            else:
                if hold_start is None:
                    hold_start = time.time()
                elapsed = time.time() - hold_start
                status = f"Hold Still {round(elapsed, 1)}s"

                if elapsed > HOLD_TIME and not captured_this_hold:
                    gray_scan = cv2.cvtColor(scan, cv2.COLOR_BGR2GRAY)
                    gray_small = cv2.resize(gray_scan, (500, 700))
                    if last_scan is not None:
                        last_small = cv2.resize(last_scan, (500, 700))
                        diff = cv2.absdiff(gray_small, last_small)
                        score = np.mean(diff)
                        if score < SIMILARITY_THRESHOLD:
                            status = "Duplicate - Skipped"
                            captured_this_hold = True
                            hold_start = None
                            continue

                    cv2.imwrite(f"scan_{count}.jpg", scan)
                    print("Saved scan", count)
                    last_scan = gray_scan.copy()
                    count += 1
                    captured_this_hold = True

                    captured = True
                    capture_time = time.time()

        else:
            hold_start = None
            captured_this_hold = False

        if captured and time.time() - capture_time < 2:
            cv2.putText(frame, "CAPTURED!", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
        else:
            captured = False

        cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow("Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    create_pdf_session([f for f in os.listdir() if f.startswith("scan_") and f.endswith(".jpg")], prefix="scan_")


# -------- MULTI PHOTO MODE WITH SESSION PDF & MAX DOC DISPLAY --------
def multi_photo_mode():
    cap = cv2.VideoCapture("http://192.168.0.225:8080/video")

    existing_files = [f for f in os.listdir() if f.startswith("multi_") and f.endswith(".jpg")]
    count = max([int(f.split("_")[1].split(".")[0]) for f in existing_files], default=0) + 1

    captured_files = []  # ✅ keep track of only current session captures

    HOLD_TIME = 1
    OBSERVE_TIME = 10
    STABLE_TIME = 1

    start_time = time.time()
    max_rect_count = 0
    stable_start = None
    last_scan = None
    captured_this_hold = False
    SIMILARITY_THRESHOLD = 15
    captured = False
    capture_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rects = detect_rectangles(frame)
        scans = []

        for rect in rects:
            scan = four_point_transform(frame, rect)
            if is_in_focus(scan):
                scans.append(scan)
                color = (0, 255, 0)
            else:
                color = (0, 0, 255)
            cv2.drawContours(frame, [rect.astype(int)], -1, color, 2)

        current_count = len(scans)
        elapsed = time.time() - start_time

        # -------- PHASE 1: Observing --------
        if elapsed < OBSERVE_TIME:
            max_rect_count = max(max_rect_count, current_count)
            status = f"Observing... {int(OBSERVE_TIME - elapsed)}s | Max: {max_rect_count}"

        # -------- PHASE 2: Capture --------
        else:
            status = f"Waiting for {max_rect_count} docs..."

            if current_count == max_rect_count and max_rect_count > 0:
                if stable_start is None:
                    stable_start = time.time()

                stable_elapsed = time.time() - stable_start
                status = f"Hold steady... {round(stable_elapsed,1)}s"

                if stable_elapsed >= STABLE_TIME and not captured_this_hold:
                    for s in scans:
                        # duplicate detection
                        gray_scan = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)
                        gray_small = cv2.resize(gray_scan, (500, 700))
                        if last_scan is not None:
                            last_small = cv2.resize(last_scan, (500, 700))
                            diff = cv2.absdiff(gray_small, last_small)
                            score = np.mean(diff)
                            if score < SIMILARITY_THRESHOLD:
                                continue  # skip duplicate

                        filename = f"multi_{count}.jpg"
                        cv2.imwrite(filename, s)
                        captured_files.append(filename)  # ✅ add to session list
                        print("Saved", filename)
                        last_scan = gray_scan.copy()
                        count += 1

                    captured_this_hold = True
                    capture_time = time.time()

                    # create PDF for this session only
                    create_pdf_session(captured_files, prefix="multi_")

            else:
                stable_start = None

        # -------- DISPLAY STATUS --------
        cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        if captured_this_hold and time.time() - capture_time < 2:
            cv2.putText(frame, "CAPTURED!", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)

        cv2.imshow("Multi Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# -------- MAIN MENU --------
print("\n1 → Video Scan")
print("2 → Multi Photo Scan")

choice = input("Enter choice: ")

if choice == "1":
    video_mode()
elif choice == "2":
    multi_photo_mode()
else:
    print("Invalid choice")
