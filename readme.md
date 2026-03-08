# Document Scanner using OpenCV

This project implements a **real-time document scanner** using Python and OpenCV.  
It detects rectangular documents from a camera feed and performs **perspective correction** to generate a flat scanned image similar to a scanned document.

The project supports two modes:
- Video Auto Scan
- Multi Photo Scan

---

# Requirements

Python 3.8+

Install required libraries:

pip install opencv-python numpy

---

# Running the Program

Run the script:

python test.py

You will see the menu:

Select Mode  
1 → Video Auto Scan  
2 → Multi Photo Scan

Enter the desired option.

---

# Mode 1 — Video Auto Scan

- Detects a single document in real time
- When the document is held steady for about **1 second**, the program automatically captures it
- The scanned image is saved automatically

Example output files:

scan_1.jpg  
scan_2.jpg  
scan_3.jpg  

Press **Q** to exit the program.

---

# Mode 2 — Multi Photo Scan

- Detects multiple rectangular documents or photos
- Press **C** to capture all detected rectangles

Example output files:

multipage_1.jpg  
multipage_2.jpg  
multipage_3.jpg  

Press **Q** to exit.

---

# Camera Setup

The program can run using either:

1. Laptop Webcam  
2. Phone Camera using IP Webcam

---

# Option 1 — Laptop Webcam

No changes are required.

The program uses the default camera:

cap = cv2.VideoCapture(0)

Run the program:

python test.py

---

# Option 2 — Phone Camera (IP Webcam)

Steps:

1. Install **IP Webcam** on an Android phone.
2. Connect the **phone and laptop to the same WiFi network**.
3. Open the app and press **Start Server**.
4. The app will display an address such as:

http://192.168.1.7:8080

Modify the camera line in the code.

Replace:

cap = cv2.VideoCapture(0)

with:

cap = cv2.VideoCapture("http://192.168.1.7:8080/video")

Use the IP address shown in the app.

Then run:

python test.py
