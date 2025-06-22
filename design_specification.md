## Hand-Tracking VST Controller Specification

### 1. Sensing Hardware

* **Input Device:** Standard consumer webcam

  * Captures RGB video at \~30 fps
  * Placement: centered above or in front of the playing area

### 2. MIDI Protocol

* **MPE Emulation:**

  * One MIDI channel per note
  * Per-note pitch-bend, velocity, and CC messages for polyphonic expression

### 3. Note Layout & Mapping

* **Rectangular Grid:**

  * 3 rows × 4 columns (12 zones) mapped to C4–B4
  * Evenly divide the webcam’s horizontal and vertical field into zones

### 4. Hand-Tracking Framework

* **MediaPipe Hands (Python):**

  * Real-time detection of 21 landmarks per hand
  * Python API for easy integration

### 5. Data Filtering & Smoothing

* **Exponential Moving Average (EMA):**

  * Per-landmark smoothing with α tuned for \~5–8 frame responsiveness
  * Balances stability with low latency

### 6. Expression Parameter Extraction

* **Pressure Proxy:** Fingertip Z-depth (MediaPipe’s normalized Z)
* **Velocity:** Frame-to-frame 2D fingertip speed → MIDI velocity/attack
* **Slide/Glide:** Swipe detection across adjacent zones → pitch-bend events
* **Vertical Motion:** Use upward/downward movement speed as additional CC (e.g. CC74)

### 7. Software Framework

* **Standalone Python Application:**

  * **Hand-Tracking & Filtering:** MediaPipe Hands + EMA in Python
  * **MIDI Output:** `python-rtmidi` library for virtual MIDI ports
  * **Configuration UI:** Simple Tkinter/Qt window for grid calibration and smoothing α