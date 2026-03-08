import cv2
import numpy as np
import time


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


# -------- PERSPECTIVE TRANSFORM --------
def four_point_transform(image, pts):

    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    return warped


# -------- DETECT SINGLE RECTANGLE --------
def detect_rectangle(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    edges = cv2.Canny(blur, 50, 150)

    kernel = np.ones((5, 5), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    largest_rect = None
    max_area = 0

    for c in contours:

        area = cv2.contourArea(c)

        if area < 20000:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4 and area > max_area:
            largest_rect = approx
            max_area = area

    return largest_rect


# -------- DETECT MULTIPLE RECTANGLES --------
def detect_rectangles(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    edges = cv2.Canny(blur, 50, 150)

    kernel = np.ones((5, 5), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []

    for c in contours:

        area = cv2.contourArea(c)

        if area < 20000:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:
            rectangles.append(approx.reshape(4, 2))

    return rectangles


# -------- VIDEO MODE (AUTO CAPTURE) --------
def video_mode():

    cap = cv2.VideoCapture(0)

    HOLD_TIME = 1
    hold_start = None
    count = 1

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        rect = detect_rectangle(frame)
        status = "Searching..."

        if rect is not None:

            cv2.drawContours(frame, [rect], -1, (0, 255, 0), 3)

            if hold_start is None:
                hold_start = time.time()

            elapsed = time.time() - hold_start
            status = f"Hold Still {round(elapsed,1)}s"

            if elapsed > HOLD_TIME:

                scan = four_point_transform(frame, rect.reshape(4, 2))

                filename = f"scan_{count}.jpg"
                cv2.imwrite(filename, scan)

                print("Saved:", filename)

                cv2.imshow("Scanned", scan)

                count += 1
                hold_start = None

        else:
            hold_start = None

        cv2.putText(frame, status, (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("Video Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# -------- MULTI PHOTO MODE --------
def multi_photo_mode():

    cap = cv2.VideoCapture(0)

    count = 1

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        rectangles = detect_rectangles(frame)

        scans = []

        for rect in rectangles:

            rect_int = rect.astype(int)
            cv2.drawContours(frame, [rect_int], -1, (0, 255, 0), 2)

            scan = four_point_transform(frame, rect)
            scans.append(scan)

        cv2.putText(frame,
                    f"{len(rectangles)} photos detected",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2)

        cv2.putText(frame,
                    "Press C to capture",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2)

        cv2.imshow("Multi Photo Scanner", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):

            for scan in scans:

                filename = f"multipage_{count}.jpg"
                cv2.imwrite(filename, scan)

                print("Saved:", filename)

                count += 1

        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# -------- MAIN MENU --------
print("\nSelect Mode")
print("1 → Video Auto Scan")
print("2 → Multi Photo Scan")

choice = input("Enter choice: ")

if choice == "1":
    video_mode()

elif choice == "2":
    multi_photo_mode()

else:
    print("Invalid option")
