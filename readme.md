# Document Scanner using OpenCV

[![GitHub stars](https://img.shields.io/github/stars/Vaishnavi333-del/Mobile-scanner?style=social)](https://github.com/Vaishnavi333-del/Mobile-scanner)
[![GitHub forks](https://img.shields.io/github/forks/Vaishnavi333-del/Mobile-scanner?style=social)](https://github.com/Vaishnavi333-del/Mobile-scanner)

<button class="copy-button" onclick="copyToClipboard('#document-scanner-using-opencv')">📋 Copy</button>

This project implements a **real-time document scanner** using Python and OpenCV. It detects rectangular documents from a camera feed and performs perspective correction to generate a flat scanned image similar to a scanned document.

The project supports two modes:
- **Video Auto Scan**
- **Multi Photo Scan**

## Table of Contents
- [Requirements](#requirements)
- [Running the Program](#running-the-program)
- [Mode 1 — Video Auto Scan](#mode-1--video-auto-scan)
- [Mode 2 — Multi Photo Scan](#mode-2--multi-photo-scan)
- [Camera Setup](#camera-setup)
- [Option 1 — Laptop Webcam](#option-1--laptop-webcam)
- [Option 2 — Phone Camera (IP Webcam)](#option-2--phone-camera-ip-webcam)

## Requirements
<button class="copy-button" onclick="copyToClipboard('#requirements')">📋 Copy</button>

```bash
Python 3.8+
pip install opencv-python numpy

