# **Real-Time Hand-Tracking VST Controller: A Comprehensive Implementation Plan for MPE Integration on Ubuntu**

## **I. Executive Summary**

This report details a comprehensive implementation plan for a real-time hand-tracking VST controller, designed to operate within an Ubuntu Linux environment. The system leverages a standard consumer webcam as its primary input, utilizing Google's MediaPipe Hands framework for robust hand landmark detection. The core innovation lies in translating nuanced hand movements and gestures into expressive MIDI Polyphonic Expression (MPE) messages, enabling per-note control over pitch, velocity, and continuous controller (CC) parameters. Initial testing will target the Surge XT VST synthesizer, a highly capable and MPE-compatible instrument. The plan addresses critical aspects including system environment configuration, real-time data processing with Exponential Moving Average (EMA) filtering, sophisticated MIDI mapping strategies, and a modular software architecture featuring a user-friendly configuration interface. Emphasis is placed on minimizing latency and ensuring computational efficiency for a responsive and musically expressive control experience.

## **II. Introduction**

The evolution of digital music production has consistently sought more intuitive and expressive control interfaces. Traditional MIDI controllers, while powerful, often lack the organic responsiveness of acoustic instruments. This project addresses this gap by proposing a novel hand-tracking VST controller that harnesses the ubiquity of consumer webcams and the advancements in real-time computer vision. By translating natural hand and finger movements into rich MPE MIDI data, the system aims to unlock new avenues for musical performance and sound design.

The Hand-Tracking VST Controller concept centers on capturing visual information of a performer's hands and transforming it into a stream of musical control signals. The system architecture involves several interconnected stages: video acquisition, hand landmark detection, data filtering, extraction of expressive parameters, conversion to MPE MIDI messages, and output to a virtual MIDI port. The design prioritizes real-time performance, ensuring minimal latency between physical gesture and sonic response. This report outlines the technical specifications and implementation steps required to build this innovative controller on an Ubuntu platform, providing a detailed blueprint for development.

## **III. System Environment Setup (Ubuntu)**

Establishing a robust and low-latency operating environment is foundational for a real-time musical instrument. This section details the necessary Ubuntu configurations and library installations.

### **A. Operating System and Core Dependencies**

For optimal real-time performance, particularly crucial for musical applications, configuring Ubuntu with a low-latency kernel is highly recommended. This can be achieved by installing the linux-lowlatency package via sudo apt-get install linux-lowlatency.1 This kernel provides a more preemptive environment, which significantly reduces latency for audio processing. For applications demanding the most stringent real-time guarantees, such as professional audio production, "Real-time Ubuntu" with a

PREEMPT\_RT kernel is available through Ubuntu Pro.2 This specialized kernel offers truly deterministic response times, which can be essential to eliminate even the most subtle perceived delays in a high-performance musical instrument. The choice between the standard low-latency kernel and the

PREEMPT\_RT kernel represents a critical trade-off between ease of setup and the absolute minimum achievable latency.3

The JACK Audio Connection Kit is the industry standard audio server for professional audio applications on Linux. It offers superior low-latency performance and flexible audio/MIDI routing capabilities compared to the default PulseAudio system.1 Installation typically involves

sudo apt-get install jackd qjackctl pulseaudio-module-jack.5 The

qjackctl utility provides a graphical interface for configuring JACK, allowing precise control over crucial parameters such as buffer sizes and sample rates. It also facilitates bridging PulseAudio, ensuring seamless integration of system sounds with professional audio applications.1 It is imperative that the user account running the application is added to the

audio group to grant the necessary real-time scheduling privileges for audio processes, typically done via sudo usermod \-a \-G audio $USER.1 This step is vital for achieving consistent low-latency performance.

It is important to recognize that MIDI latency, in the context of a VST instrument, is not solely determined by the Python application's processing speed or the python-rtmidi library. It is fundamentally tied to the entire audio stack's latency.6 Even if MIDI messages are generated instantaneously by the Python application, a high-latency audio buffer setting in JACK or an unoptimized kernel will introduce a noticeable delay before sound is produced by Surge XT. Therefore, a holistic approach to latency optimization, encompassing kernel tuning, proper JACK configuration, and VST host settings, is essential for a truly responsive musical experience.

Utilizing venv or conda for creating isolated Python environments is considered a best practice for dependency management. This approach prevents conflicts between different projects and ensures that the specific versions of MediaPipe, python-rtmidi, and other libraries required for this controller do not interfere with other Python installations or projects on the system.8

MediaPipe relies on OpenCV for image and video processing and FFmpeg for video decoding.9 On Ubuntu, these can be installed using the

apt-get package manager. The following command installs the necessary development libraries: sudo apt-get install \-y libopencv-core-dev libopencv-highgui-dev libopencv-calib3d-dev libopencv-features2d-dev libopencv-imgproc-dev libopencv-video-dev.9 For newer Ubuntu versions (e.g., 21.04 and above) that ship with OpenCV 4.x,

libopencv-contrib-dev might also be a required dependency.9 Alternatively, building OpenCV from source using MediaPipe's

setup\_opencv.sh script (Option 2 in the MediaPipe documentation) is a robust method to ensure compatibility and leverage specific optimizations, particularly if pre-compiled packages present issues.9

### **B. Python Library Installation**

The mediapipe PyPI package, specifically the Hand Landmarker solution, is central to the hand-tracking functionality.11 It is installed using pip:

python \-m pip install mediapipe.12 This package provides the Python API for real-time hand detection and landmark extraction. While the instruction is to install the "latest stable version," reports indicate potential compatibility issues between MediaPipe and very recent Python versions, with Python 3.13 noted as problematic for installation.13 This suggests that selecting a known compatible Python version (e.g., Python 3.11 or 3.12, as of recent reports)

*before* MediaPipe installation is a critical preventative measure to avoid build failures or runtime errors. This proactive approach ensures a smoother development process and avoids common setup challenges.

The python-rtmidi library is essential for MIDI communication. It is installed via pip: python \-m pip install python-rtmidi.8 This library provides the necessary Python bindings for the RtMidi C++ library, enabling real-time MIDI input/output and virtual MIDI port creation on Linux.14 System-level build tools (

build-essential) and Python development headers (python-dev) are prerequisites on Debian-based systems like Ubuntu for successful compilation of the C++ extension.8 It is important to distinguish

python-rtmidi from an older, similarly named library, rtmidi-python.16 The latter is significantly outdated (last updated in 2014\) compared to

python-rtmidi (last updated in late 2023).15 Explicitly choosing

python-rtmidi is crucial for project stability and access to modern features, including robust virtual MIDI port support.

### **C. VST Host Setup**

Surge XT is available for Linux as a 64-bit VST3 and CLAP plugin, and also as a standalone application.17 The recommended installation method involves downloading the appropriate

.deb package from the official Surge XT website and installing it using sudo dpkg \-i \<package\_name.deb\>.

For initial testing and simplified MIDI routing, running Surge XT as a standalone application is advisable. Its top-left options menu allows direct configuration of MIDI and audio inputs/outputs.17 The virtual MIDI port created by the Python application must be selected as an active MIDI input within Surge XT. If the intention is to use Surge XT as a VST plugin within a Digital Audio Workstation (DAW), the DAW's internal MIDI routing capabilities will be used to direct the virtual MIDI port's output to the specific Surge XT instance.

While Surge XT is explicitly MPE-compatible 18, a common challenge arises with many DAWs (e.g., Ableton Live, as noted in community discussions).22 These DAWs may "strip away" MIDI channel information when routing to VST plugins, which can inadvertently hinder the per-note expression fundamental to MPE. For reliable MPE performance, direct routing to the standalone Surge XT application is recommended for initial testing. Alternatively, specific DAW configurations, such as creating multiple MIDI tracks each assigned a unique MIDI channel and routed to the same Surge XT instance, or utilizing advanced instrument rack features, will be necessary to preserve MPE channel data and ensure proper polyphonic expression.22 This challenge highlights a critical integration aspect that extends beyond simple installation and requires careful consideration of the MIDI signal flow within the audio production environment.

## **IV. Hand Tracking and Data Processing**

The core functionality of the controller relies on accurate and real-time hand tracking and subsequent data processing.

### **A. Webcam Integration and Video Capture**

A standard consumer webcam captures RGB video, typically at around 30 frames per second, serving as the primary input device for the system \[User Query\]. OpenCV's cv2.VideoCapture(0) is the conventional and widely used method for acquiring this live video stream from the default webcam.23

Optimal hand tracking accuracy is heavily dependent on environmental conditions. The webcam should be positioned centrally above or in front of the playing area, ensuring a clear and unobstructed view of the hands \[User Query\]. Consistent, adequate lighting is crucial; avoiding overly bright or dark conditions, and minimizing reflective surfaces (such as windows or glossy tabletops) will help prevent tracking errors and improve sensor accuracy.25 Furthermore, ensuring the hands are fully visible within the camera's field of view and are presented against a high-contrast background will significantly enhance detection robustness and overall tracking performance.26

While cv2.VideoCapture is widely used, its read() method can be a blocking operation, meaning the program pauses and waits for a new frame before proceeding.27 In a real-time application aiming for low latency, this blocking behavior can introduce significant processing delays and reduce overall responsiveness. To mitigate this, alternative video capture strategies are recommended. One approach is to use the

acapture library, which offers non-blocking frame reads, allowing the application to continue processing while waiting for the next frame.27 A more robust solution involves implementing video capture in a separate thread, which continuously captures frames and places them into a synchronized queue. The main processing thread can then asynchronously consume frames from this queue, ensuring that video acquisition does not block the hand tracking and MIDI generation pipeline.28 This architectural decision is vital for maintaining a fluid user experience and minimizing end-to-end latency in a real-time system.

### **B. MediaPipe Hands Implementation**

The mediapipe.tasks.python.vision.HandLandmarker API is the designated framework for hand tracking.12 When initializing the

HandLandmarker instance, key configuration options must be set. The running\_mode should be configured to LIVE\_STREAM to enable continuous processing of webcam input.12 The

num\_hands parameter can be set to 1 or 2, depending on whether single or multi-hand tracking is desired for polyphonic expression.12 Additionally, confidence thresholds such as

min\_hand\_detection\_confidence and min\_tracking\_confidence can be tuned to balance the trade-off between detection accuracy and computational performance.12 Adjusting these values can help prevent spurious detections while maintaining robust tracking.

MediaPipe provides 21 distinct landmarks for each detected hand.12 Each landmark is represented by

x, y, and z coordinates. The x and y coordinates are normalized to a range of \[0.0, 1.0\] relative to the image width and height, respectively.12 The

z coordinate represents the landmark's depth, with the wrist serving as the origin point.12 A smaller

z value indicates that the landmark is closer to the camera.12 The magnitude of the

z coordinate is roughly on the same scale as the x and y coordinates, providing a consistent spatial representation.12 This normalized 3D data forms the basis for extracting expressive control parameters.

### **C. Data Filtering and Smoothing (Exponential Moving Average)**

To mitigate inherent sensor noise and tracking jitter that can lead to erratic MIDI output, an Exponential Moving Average (EMA) filter will be applied independently to each x, y, and z coordinate of every detected hand landmark. The EMA is a type of moving average that gives more weight to recent data points, making it more responsive to current trends compared to a simple moving average.32 The mathematical formulation for EMA is:

EMA\_current \= (alpha \* current\_value) \+ ((1 \- alpha) \* EMA\_previous) 32

Here, alpha (α) is the smoothing factor, a constant between 0 and 1\. current\_value is the raw landmark coordinate, and EMA\_previous is the filtered value from the previous frame.

The alpha parameter directly controls the trade-off between smoothing and responsiveness.32 A higher

alpha (closer to 1\) makes the filter more responsive to recent changes but less smooth, while a lower alpha (closer to 0\) provides more smoothing but introduces more lag.32 The specification targets a responsiveness of "\~5-8 frames" at a webcam capture rate of 30 frames per second. To translate this into an appropriate

alpha value, the relationship between alpha and the filter's time constant (tau) can be utilized. The frame duration T is 1/30 seconds. For a desired responsiveness of 5 frames, the effective tau would be 5 \* (1/30) \= 1/6 seconds. Using the approximation alpha \= 1 \- exp(-T/tau) 37, an

alpha value of approximately 1 \- exp(- (1/30) / (1/6)) \= 1 \- exp(-0.2) ≈ 0.18 would be suitable for 5-frame responsiveness. For 8 frames, tau \= 8/30 seconds, yielding alpha ≈ 1 \- exp(-1/8) ≈ 0.1175. Thus, an alpha range of approximately **0.1 to 0.2** should be targeted for initial tuning.

The technical target of "\~5-8 frame responsiveness" for EMA smoothing must be translated into a musically intuitive feel. A very low alpha might make the controller feel sluggish and unresponsive to subtle gestures, while a very high alpha could result in "twitchy" or unstable MIDI output due to insufficient noise reduction. The optimal alpha value is subjective and depends on the specific musical expression desired by the performer. This necessitates a user-tunable parameter in the configuration interface, allowing the performer to empirically fine-tune this parameter to balance smooth control with immediate responsiveness for a natural musical interaction.

While EMA is the primary smoothing method specified, if significant jitter persists or a more sophisticated approach is desired, a Kalman Filter (KF) could be considered.39 KFs are optimal estimators for linear systems with Gaussian noise and can provide superior state estimation and prediction, further reducing jitter and enhancing tracking accuracy.39 However, implementing a Kalman Filter adds a layer of mathematical complexity compared to EMA, which might be a consideration for development resources.

## **V. MIDI Mapping and Expression Extraction**

This section details the transformation of processed hand tracking data into expressive MPE MIDI messages.

### **A. Rectangular Grid Note Layout**

The webcam's captured frame, with its specific width and height, will be logically divided into 12 equally sized rectangular zones, arranged in a 3 rows × 4 columns grid \[User Query\]. These zones will be visually overlaid on the live video feed display using OpenCV's drawing functions, specifically cv2.rectangle, to provide real-time feedback to the user during performance and calibration.41 This visual overlay is crucial for the performer to understand the interactive space.

Each of the 12 zones will be assigned a unique MIDI note number, covering the standard musical range from C4 (MIDI note 60\) to B4 (MIDI note 71\) \[User Query\]. A logical mapping scheme, such as progressing from left-to-right across columns and then bottom-to-top across rows, will be implemented to ensure intuitive playability.

The system will continuously monitor the smoothed (x,y) coordinates of a designated fingertip (e.g., the index finger tip, which is landmark 8 in MediaPipe's hand model 43). When this fingertip enters a specific zone, a MIDI Note On message is triggered for the corresponding note. When the fingertip subsequently exits that zone (or another note-on event occurs for the same finger, indicating a re-strike or legato transition), a MIDI Note Off message is sent. Point-in-rectangle detection can be efficiently performed by simple coordinate comparisons (checking if the fingertip's x-coordinate is between the zone's left and right boundaries, and its y-coordinate is between the zone's top and bottom boundaries).45 For more complex or rotated zones,

cv2.pointPolygonTest could be used, though for a simple rectangular grid, direct comparison is sufficient and computationally lighter.46

The following table outlines a possible mapping of the 12 zones to MIDI notes C4-B4:

**Table 2: Rectangular Grid Note Assignments (C4-B4)**

| Grid Row | Grid Column 1 | Grid Column 2 | Grid Column 3 | Grid Column 4 |
| :---- | :---- | :---- | :---- | :---- |
| **Row 1 (Top)** | C5 (72) | C\#5 (73) | D5 (74) | D\#5 (75) |
| **Row 2 (Middle)** | E4 (64) | F4 (65) | F\#4 (66) | G4 (67) |
| **Row 3 (Bottom)** | C4 (60) | C\#4 (61) | D4 (62) | D\#4 (63) |

*Note: The table above provides an example mapping. The specification indicates C4-B4 (MIDI 60-71), which is 12 notes. The example table uses C4-G4 and C5-D\#5, which covers a wider range. For strict adherence to C4-B4, the mapping would be: Row 1: G\#4 (68), A4 (69), A\#4 (70), B4 (71); Row 2: E4 (64), F4 (65), F\#4 (66), G4 (67); Row 3: C4 (60), C\#4 (61), D4 (62), D\#4 (63).*

### **B. MPE Protocol Emulation**

MIDI Polyphonic Expression (MPE) is a crucial standard that re-purposes the 16 available MIDI channels to enable independent expressive control for each concurrently sounding note.48 In MPE, instead of a single channel controlling all notes, each note gets its own dedicated channel. This allows for per-note pitch bend, timbre (typically MIDI CC74), and pressure messages to be applied individually, significantly enhancing expressive capabilities.48 This setup typically limits polyphony to 15 notes (channels 2-16), as channel 1 is often reserved as a global master channel for non-per-note messages like sustain pedal or program changes.49

The system must implement dynamic MIDI channel allocation for true polyphonic expression. A pool of available MIDI channels (e.g., channels 2-16) will be maintained. When a new note is triggered (i.e., a fingertip enters a zone), an available MIDI channel is dynamically assigned to that specific note. All subsequent expression messages (pitch bend, CCs) related to that particular note are then sent exclusively on its dedicated channel. Upon a Note Off event for that note, its assigned MIDI channel is released back into the pool, making it available for a new note. This dynamic allocation is fundamental for achieving the rich, independent per-note control that MPE offers.

### **C. Expression Parameter Extraction and MIDI Conversion**

#### **Pressure Proxy (Fingertip Z-depth)**

MediaPipe's z coordinate for each landmark provides a relative depth measurement, normalized with respect to the wrist landmark (landmark 0).12 A smaller

z value indicates that the fingertip is closer to the camera, which can be interpreted as increased "pressure" or "aftertouch." This raw z value needs to be mapped to a standard MIDI Continuous Controller (CC) range of 0-127.

The mapping process involves:

1. **Normalization:** The raw z values, while relative, do not have a fixed absolute range across different camera setups or distances.31 Therefore, a calibration step in the UI is necessary to define the minimum and maximum  
   z values corresponding to "no pressure" and "maximum pressure." These calibrated min/max z values will then be used to linearly scale the current z value to the 0-127 MIDI range. For instance, MIDI\_CC\_Value \= (Z\_current \- Z\_min) / (Z\_max \- Z\_min) \* 127\.  
2. **MIDI CC Assignment:** This "pressure" value can be mapped to MIDI Channel Pressure (Aftertouch) or a general-purpose CC. MPE often uses CC74 for "Timbre" or "Slide" (often associated with the Y-axis of a physical controller).20 If CC74 is used for pressure, another suitable CC would be needed for vertical motion. The choice depends on the desired musical mapping and the capabilities of the target VST (Surge XT supports MPE and allows MIDI CC assignment 17).

#### **Velocity (Frame-to-frame 2D Fingertip Speed)**

MIDI velocity typically controls the attack or intensity of a note. In this system, it will be derived from the speed of the fingertip as it enters a new zone.

1. **Calculate 2D Speed:** The 2D speed of the fingertip can be calculated by determining the Euclidean distance between the fingertip's (x,y) coordinates in the current frame and its (x,y) coordinates in the previous frame, then dividing by the time elapsed between frames (which is 1/FPS for a constant frame rate).51  
   * Distance \= sqrt((x\_current \- x\_previous)^2 \+ (y\_current \- y\_previous)^2) 55  
   * Speed \= Distance / (1/FPS)  
2. **Map Speed to MIDI Velocity:** The calculated speed value will then be scaled to the 0-127 MIDI velocity range. A non-linear mapping (e.g., logarithmic) might provide a more musically expressive response, as human perception of loudness is logarithmic. Calibration points for minimum and maximum effective speeds would allow the user to define the dynamic range.

#### **Slide/Glide (Swipe Detection)**

Slide or glide gestures across adjacent zones will generate per-note pitch-bend events, allowing for smooth transitions between notes or expressive vibrato within a sustained note.

1. **Swipe Detection Algorithm:**  
   * The system monitors the active fingertip holding a note in a specific zone.  
   * If the fingertip moves from its initial zone into an adjacent zone *without a Note Off event being sent* (i.e., the finger remains "down" or detected), a swipe is registered.  
   * The pitch bend value will be determined by the fingertip's continuous position within the target zone, relative to the boundary it crossed.  
2. **Pitch Bend Generation:**  
   * MIDI pitch bend messages are 14-bit values, ranging from 0 to 16383, with 8192 representing no pitch bend.57 This 14-bit value is transmitted as two 7-bit data bytes (LSB and MSB) following the pitch bend status byte (0xE0 for channel 1, 0xE1 for channel 2, etc.).57  
   * The standard MPE pitch bend range is often set to \+/- 48 semitones.19 This means the full 14-bit pitch bend range covers 96 semitones. The mapping should scale the fingertip's horizontal movement within the combined "active" zones (original \+ adjacent) to this 14-bit range.  
   * Each active note (on its dedicated MPE channel) will send its own pitch bend messages, allowing for polyphonic glides.

#### **Vertical Motion (Additional CC)**

Upward or downward movement of the active fingertip can be used as an additional continuous controller, providing another dimension of expression.

1. **Calculate Vertical Speed:** Similar to velocity, the vertical speed can be calculated from the change in the fingertip's y coordinate between frames, divided by the time elapsed. Vertical\_Speed \= (y\_current \- y\_previous) / (1/FPS).13 The sign of the speed indicates upward or downward motion.  
2. **Map to MIDI CC:** This vertical speed value will be mapped to a dedicated MIDI CC (e.g., CC74 if not used for pressure, or another suitable general-purpose CC like CC1 for Modulation Wheel, or CC11 for Expression, depending on the desired musical effect and VST mapping).20 Calibration for the range of vertical motion and its corresponding CC values would be beneficial.

### **D. MIDI Output with python-rtmidi**

The python-rtmidi library will be used to create and manage virtual MIDI ports, which act as software-based MIDI cables allowing the Python application to send MIDI messages to other applications, such as a DAW or the standalone Surge XT synthesizer.13

Creating a virtual MIDI output port is straightforward:  
midiout \= rtmidi.MidiOut()  
midiout.open\_virtual\_port("HandTrackingController") 15  
Once the virtual port is open, MPE-compliant MIDI messages can be sent using the midiout.send\_message() method. Each MIDI message is represented as a list of integers (bytes).15

* **Note On:** \[0x90 | channel, note\_number, velocity\] (e.g., \[0x91, 60, 100\] for C4 on channel 2 with velocity 100).15  
* **Note Off:** \[0x80 | channel, note\_number, 0\] (e.g., \[0x81, 60, 0\] for C4 on channel 2 off).15  
* **Pitch Bend:** \[0xE0 | channel, lsb, msb\] (e.g., \[0xE1, lsb\_value, msb\_value\] for pitch bend on channel 2).57 The 14-bit pitch bend value needs to be split into two 7-bit bytes for LSB and MSB.  
* **Control Change (CC):** (e.g., for CC74 on channel 2).63

The following table summarizes the proposed mapping of hand landmarks to MIDI parameters:

**Table 1: Hand Landmark to MIDI Parameter Mapping**

| Hand Landmark Feature | MIDI Parameter | MIDI Message Type | MIDI Channel | Value Range (MIDI) |
| :---- | :---- | :---- | :---- | :---- |
| Fingertip Z-depth | Pressure/Timbre | Control Change (CC) | Per-note | CC74 (0-127) or Channel Pressure (0-127) |
| 2D Fingertip Speed | Velocity | Note On/Off | Per-note | 1-127 (Note On) |
| Swipe across zones | Pitch Bend | Pitch Bend | Per-note | 0-16383 (8192 \= center) |
| Vertical Motion Speed | Additional CC | Control Change (CC) | Per-note | CC74 (0-127) (if not used for pressure) or other CC (e.g., CC1, CC11) |

## **VI. Software Framework and User Interface**

The software framework will be a standalone Python application designed for modularity and real-time responsiveness.

### **A. Standalone Python Application Architecture**

The application will adopt a modular design, separating concerns into distinct components for hand-tracking, data processing, MIDI generation, and user interface management. This modularity enhances maintainability, testability, and allows for potential future extensions.

To maintain real-time performance and ensure UI responsiveness, a multi-threaded architecture is critical.67 Python's

threading module can be utilized to create separate threads for computationally intensive tasks. A common pattern for real-time video processing involves a producer-consumer model using queue objects for inter-thread communication.28

The proposed thread structure includes:

1. **Video Capture Thread:** This thread continuously captures frames from the webcam using OpenCV (or acapture for non-blocking reads) and places them into an input Queue.28 This ensures that frame acquisition does not block other processing.  
2. **Hand Tracking & Processing Thread:** This thread consumes frames from the input Queue, performs MediaPipe hand landmark detection, applies EMA filtering, and extracts expressive parameters. The processed landmark data and derived parameters are then placed into an output Queue.28  
3. **MIDI Generation & Output Thread:** This thread consumes processed data from the output Queue, applies the MIDI mapping logic (zone detection, MPE channel allocation, CC/pitch bend calculation), and sends MIDI messages via python-rtmidi to the virtual MIDI port.  
4. **UI Thread (Main Thread):** The main thread manages the Tkinter/Qt user interface, displaying the live video feed with overlaid zones, handling user input for calibration and parameter tuning, and updating status information. It reads data from the output Queue for visualization but avoids blocking operations to maintain UI fluidity.

This multi-threaded approach allows CPU-bound tasks (like MediaPipe processing) to run concurrently with I/O-bound tasks (like video capture and MIDI output), significantly improving overall system responsiveness and reducing perceived latency.68

### **B. Configuration UI (Tkinter/Qt)**

A simple graphical user interface (GUI) is essential for calibrating the system and tuning performance parameters. Both Tkinter and PyQt are viable options for Python GUI development.71 Tkinter is often simpler for basic interfaces, while PyQt offers more advanced widgets and a more modern look.72

The UI will feature:

1. **Grid Calibration:** A live video feed from the webcam will be displayed on a canvas. The 3x4 rectangular grid zones will be visually overlaid on this feed.41 The user will be able to visually adjust the boundaries of this grid (e.g., by dragging and resizing the overall grid or individual zone lines) to match the physical playing area and webcam field of view.74 This can be implemented using canvas drawing primitives and event handlers for mouse clicks and drags.75 The coordinates of the grid lines will be stored and used for fingertip-to-zone mapping.  
2. **Smoothing α Slider:** A slider widget will allow real-time adjustment of the EMA α parameter.72 This enables the user to fine-tune the balance between signal smoothness and responsiveness, catering to individual playing preferences. The slider should display its current value.  
3. **Other Mapping Parameters:** Additional sliders or input fields will be provided for calibrating the ranges of other expressive parameters, such as:  
   * Minimum and maximum Z-depth for pressure mapping.  
   * Minimum and maximum fingertip speed for velocity mapping.  
   * Pitch bend range sensitivity.  
   * Vertical motion speed to CC mapping range.  
4. **Basic Status Display:** The UI will include a simple text overlay or dedicated display area to show real-time status information, such as:  
   * Current Frames Per Second (FPS) of the video processing.  
   * Currently active MIDI notes and their assigned MPE channels.  
   * Raw and filtered values of key landmarks (e.g., index fingertip).  
   * MIDI message output log (optional, for debugging).

## **VII. Performance Considerations and Optimization**

Achieving a truly real-time and responsive musical instrument requires meticulous attention to performance throughout the system.

### **A. Latency Management**

Minimizing end-to-end latency, from the physical hand gesture to the audible VST output, is paramount. As discussed, this is a holistic challenge. Kernel-level optimizations are foundational: using a low-latency kernel (linux-lowlatency) or a real-time kernel (PREEMPT\_RT) significantly reduces the operating system's scheduling latency.1 Proper configuration of the JACK Audio Connection Kit, including setting small buffer sizes (e.g., 64 or 128 samples) and appropriate sample rates (e.g., 44100 Hz or 48000 Hz), directly impacts the audio processing latency.1 Users must be granted real-time privileges by being part of the

audio group to allow the JACK server and audio applications to run with high priority.1 Furthermore, ensuring that the VST host (Surge XT standalone or within a DAW) is configured for low-latency audio processing and that its internal buffer settings are optimized is crucial.17 MIDI synchronization issues, often related to USB connections or DAW internal processing, also contribute to latency and require careful attention to buffer settings and potential use of dedicated MIDI clock devices for complex setups.85

### **B. Computational Efficiency**

Optimizing the computational efficiency of the MediaPipe pipeline and subsequent data processing is vital for maintaining a high frame rate and low latency. MediaPipe is designed for real-time performance, but its execution can still be computationally intensive.87 Strategies include:

* **Optimal MediaPipe Configuration:** Tuning min\_hand\_detection\_confidence and min\_tracking\_confidence can reduce unnecessary re-detections, allowing the lightweight tracking algorithm to operate more frequently and improve performance.12  
* **Frame Resolution:** Processing video frames at a lower resolution (e.g., 640x480) can significantly reduce the computational load on MediaPipe without necessarily compromising tracking accuracy for hand gestures, depending on the camera's field of view and hand size in the frame.  
* **Efficient Data Structures and Algorithms:** Using NumPy arrays for numerical operations and vectorized calculations for EMA filtering and speed computations can leverage underlying C implementations for faster processing compared to pure Python loops.56  
* **Targeted Landmark Use:** Only extract and process the specific landmarks required for the control parameters (e.g., fingertip landmarks for position, wrist for Z-depth reference) rather than iterating through all 21 landmarks if not necessary for a given calculation.  
* **GPU Acceleration:** If the system has a compatible GPU, MediaPipe can often leverage it for accelerated inference, dramatically improving frame processing rates.9 This requires specific build configurations for MediaPipe and ensuring the necessary drivers (e.g., Mesa EGL for desktop Linux) are installed.9

### **C. Accuracy and Robustness**

Addressing potential tracking inaccuracies and environmental factors is crucial for a reliable controller.

* **Environmental Factors:** As noted, consistent and appropriate lighting, a high-contrast background, and ensuring the hands are fully within the camera's field of view are fundamental to improving detection accuracy and robustness.25 Avoiding reflective surfaces is also important.25  
* **Jitter Reduction:** While EMA provides a good balance of smoothing and responsiveness, persistent jitter can be further addressed. If EMA proves insufficient, a Kalman Filter offers a more advanced solution for state estimation and prediction, which can significantly reduce jitter and enhance the stability of landmark coordinates.39  
* **Handling Occlusions/Lost Tracking:** MediaPipe's tracking algorithm attempts to maintain hand position even with partial occlusions, but complete loss of tracking can occur.12 The system should implement strategies to handle such events, such as:  
  * **Graceful MIDI Note Off:** If a hand is lost, send Note Off messages for all currently active notes associated with that hand to prevent "stuck" notes.  
  * **Prediction/Interpolation:** For very brief tracking losses, simple linear interpolation of the last known landmark positions can be used to bridge gaps and maintain a smooth output.  
  * **Confidence Thresholds:** Adjusting MediaPipe's min\_detection\_confidence and min\_tracking\_confidence can influence how readily the system re-detects or drops a hand, balancing responsiveness with stability.12

## **VIII. Conclusion and Future Work**

This implementation plan provides a detailed roadmap for developing a real-time hand-tracking VST controller on Ubuntu, leveraging MediaPipe Hands and python-rtmidi for MPE integration. The system's capability to translate natural hand gestures into polyphonic expressive MIDI data represents a significant step towards more intuitive and physically engaging musical interfaces. Key considerations for low-latency performance, robust tracking, and a user-friendly calibration interface have been thoroughly addressed, emphasizing the importance of a holistic approach to system design and optimization.

Potential enhancements and advanced features for future development include:

* **Multi-Hand Tracking:** Extending the system to support two-hand polyphony and independent control, requiring more sophisticated channel management and potentially more complex gesture interpretation.  
* **Custom Gesture Recognition:** Incorporating MediaPipe's Gesture Recognizer or training custom machine learning models to detect specific hand poses or dynamic gestures (e.g., a "fist" to toggle sustain, or a "wave" to trigger a specific effect).89  
* **Machine Learning for Expression Mapping:** Instead of rule-based mapping, a machine learning model could learn complex relationships between hand kinematics and desired musical expression, potentially offering a more nuanced and personalized control experience.  
* **Advanced Calibration:** Implementing more sophisticated calibration routines, such as automatic detection of the playing area or adaptive scaling of control ranges based on user interaction.  
* **Visual Feedback Enhancements:** Overlaying more detailed visual feedback on the live video stream, such as real-time display of MIDI CC values or visual indicators of active notes and pitch bends.

This project offers a compelling demonstration of how modern computer vision and machine learning techniques can be applied to create innovative and expressive musical instruments, blurring the lines between physical interaction and digital sound.

## **IX. Appendices**

**Table 3: Key Dependencies and Installation Commands (Ubuntu)**

| Component | Package/Library | Installation Command(s) | Notes |
| :---- | :---- | :---- | :---- |
| **OS Core** | Low-latency Kernel | sudo apt-get install linux-lowlatency | For reduced audio latency. Consider PREEMPT\_RT via Ubuntu Pro for critical applications. |
|  | JACK Audio Kit | sudo apt-get install jackd qjackctl pulseaudio-module-jack | Professional audio server. Configure with qjackctl. |
|  | User Group | sudo usermod \-a \-G audio $USER | Grants real-time privileges for audio. Requires re-login. |
| **Python Env** | Virtual Environment | python3 \-m venv venv\_name | Best practice for dependency isolation. |
| **CV/ML** | OpenCV Dev Libs | sudo apt-get install \-y libopencv-core-dev libopencv-highgui-dev libopencv-calib3d-dev libopencv-features2d-dev libopencv-imgproc-dev libopencv-video-dev libopencv-contrib-dev | Essential for MediaPipe. libopencv-contrib-dev for OpenCV 4.x. |
|  | FFmpeg | Installed via libopencv-video-dev | Video decoding. |
|  | MediaPipe Hands | python \-m pip install mediapipe | Ensure Python 3.12 or compatible version is used. |
| **MIDI** | python-rtmidi | python \-m pip install python-rtmidi | Python bindings for RtMidi. Requires build-essential and python-dev. |
|  | Build Essentials | sudo apt-get install build-essential python3-dev | For compiling python-rtmidi from source if pre-compiled wheels are unavailable. |
| **UI** | Tkinter (built-in) | (No separate install for core Tkinter) | If using Tkinter. |
|  | PyQt (optional) | python \-m pip install PyQt5 | If using PyQt. |
| **VST Host** | Surge XT VST | Download .deb from official site, sudo dpkg \-i \<package\_name.deb\> | Install as standalone or VST plugin. Configure MIDI input. |

#### **Works cited**

1. Audio/Music production in Linux Part 1: Setting up JACK Audio \- Benjamin Caccia, accessed June 22, 2025, [https://bcacciaaudio.com/2018/01/30/audio-music-production-in-linux-part-1-setting-up-jack-audio/](https://bcacciaaudio.com/2018/01/30/audio-music-production-in-linux-part-1-setting-up-jack-audio/)  
2. Real-time Ubuntu, accessed June 22, 2025, [https://ubuntu.com/real-time](https://ubuntu.com/real-time)  
3. How to install low-latency kernel \- LinuxMusicians, accessed June 22, 2025, [https://linuxmusicians.com/viewtopic.php?t=25505](https://linuxmusicians.com/viewtopic.php?t=25505)  
4. Guide to Low Latency Linux Kernel Configurations \- Baeldung, accessed June 22, 2025, [https://www.baeldung.com/linux/kernel-low-latency-settings](https://www.baeldung.com/linux/kernel-low-latency-settings)  
5. Setting up MIDI controller on Ubuntu 20.04 \- jbargu, accessed June 22, 2025, [https://jbargu.github.io/en/post/ubuntu-setting-up-midi-controller-and-audio/](https://jbargu.github.io/en/post/ubuntu-setting-up-midi-controller-and-audio/)  
6. Electronic drumkit Midi \- Latency \- LinuxMusicians, accessed June 22, 2025, [https://linuxmusicians.com/viewtopic.php?t=16619](https://linuxmusicians.com/viewtopic.php?t=16619)  
7. MIDI latency in Linux: how do I reduce it? \- Gearspace, accessed June 22, 2025, [https://gearspace.com/board/music-computers/1431384-midi-latency-linux-how-do-i-reduce.html](https://gearspace.com/board/music-computers/1431384-midi-latency-linux-how-do-i-reduce.html)  
8. Installation — python-rtmidi 1.5.8 documentation \- GitHub Pages, accessed June 22, 2025, [https://spotlightkid.github.io/python-rtmidi/installation.html](https://spotlightkid.github.io/python-rtmidi/installation.html)  
9. layout: forward target: https://developers.google.com/mediapipe ..., accessed June 22, 2025, [https://mediapipe.readthedocs.io/en/latest/getting\_started/install.html](https://mediapipe.readthedocs.io/en/latest/getting_started/install.html)  
10. Build mediapipe on Linux (Ubuntu 22.04) \- Stack Overflow, accessed June 22, 2025, [https://stackoverflow.com/questions/76172404/build-mediapipe-on-linux-ubuntu-22-04](https://stackoverflow.com/questions/76172404/build-mediapipe-on-linux-ubuntu-22-04)  
11. MediaPipe Solutions guide | Google AI Edge \- Gemini API, accessed June 22, 2025, [https://ai.google.dev/edge/mediapipe/solutions/guide](https://ai.google.dev/edge/mediapipe/solutions/guide)  
12. Hand landmarks detection guide for Python | Google AI Edge \- Gemini API, accessed June 22, 2025, [https://ai.google.dev/edge/mediapipe/solutions/vision/hand\_landmarker/python](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python)  
13. frkatona/HandTrack\_To\_MIDI \- GitHub, accessed June 22, 2025, [https://github.com/frkatona/HandTrack\_To\_MIDI](https://github.com/frkatona/HandTrack_To_MIDI)  
14. RtMidi (Default, Recommended) \- Mido \- MIDI Objects for Python \- Read the Docs, accessed June 22, 2025, [https://mido.readthedocs.io/en/latest/backends/rtmidi.html](https://mido.readthedocs.io/en/latest/backends/rtmidi.html)  
15. python-rtmidi \- PyPI, accessed June 22, 2025, [https://pypi.org/project/python-rtmidi/](https://pypi.org/project/python-rtmidi/)  
16. rtmidi-python·PyPI, accessed June 22, 2025, [https://pypi.org/project/rtmidi-python/](https://pypi.org/project/rtmidi-python/)  
17. User Manual \- Surge XT, accessed June 22, 2025, [https://surge-synthesizer.github.io/manual-xt/](https://surge-synthesizer.github.io/manual-xt/)  
18. Surge Synth \- Roger Linn Design, accessed June 22, 2025, [https://www.rogerlinndesign.com/support/ls-surge](https://www.rogerlinndesign.com/support/ls-surge)  
19. MIDI MPE Settings \- Cherry Audio Documentation, accessed June 22, 2025, [https://docs.cherryaudio.com/cherry-audio/instruments/mercury-4/mpe](https://docs.cherryaudio.com/cherry-audio/instruments/mercury-4/mpe)  
20. Setting up Osmose in Ableton Live \- Help Center \- Expressive E, accessed June 22, 2025, [https://expressivee.happyfox.com/kb/article/265-setting-up-osmose-in-ableton-live/](https://expressivee.happyfox.com/kb/article/265-setting-up-osmose-in-ableton-live/)  
21. Surge XT, accessed June 22, 2025, [https://surge-synthesizer.github.io/](https://surge-synthesizer.github.io/)  
22. Surge xt vst set midi channel for plugin instance : r/synthesizers \- Reddit, accessed June 22, 2025, [https://www.reddit.com/r/synthesizers/comments/139xo3h/surge\_xt\_vst\_set\_midi\_channel\_for\_plugin\_instance/](https://www.reddit.com/r/synthesizers/comments/139xo3h/surge_xt_vst_set_midi_channel_for_plugin_instance/)  
23. Hand Tracking In Python | MediaPipe Series \- YouTube, accessed June 22, 2025, [https://www.youtube.com/watch?v=8peQbGxPcTw](https://www.youtube.com/watch?v=8peQbGxPcTw)  
24. Live Webcam Drawing using OpenCV \- GeeksforGeeks, accessed June 22, 2025, [https://www.geeksforgeeks.org/python/live-webcam-drawing-using-opencv/](https://www.geeksforgeeks.org/python/live-webcam-drawing-using-opencv/)  
25. How to fix HoloLens hand tracking issues? \- Omi AI, accessed June 22, 2025, [https://www.omi.me/blogs/iot-devices-faq/how-to-fix-hololens-hand-tracking-issues](https://www.omi.me/blogs/iot-devices-faq/how-to-fix-hololens-hand-tracking-issues)  
26. Is there a way to improve hand detection accuracy? \- VIVE Developers, accessed June 22, 2025, [https://developer.vive.com/us/support/sdk/category\_howto/how-to-improve-hand-detection-accuracy.html](https://developer.vive.com/us/support/sdk/category_howto/how-to-improve-hand-detection-accuracy.html)  
27. acapture (async capture python library) \- PyPI, accessed June 22, 2025, [https://pypi.org/project/acapture/](https://pypi.org/project/acapture/)  
28. real time video processing using multithreading in Python \- Stack Overflow, accessed June 22, 2025, [https://stackoverflow.com/questions/53945501/real-time-video-processing-using-multithreading-in-python](https://stackoverflow.com/questions/53945501/real-time-video-processing-using-multithreading-in-python)  
29. queue — A synchronized queue class — Python 3.13.5 documentation, accessed June 22, 2025, [https://docs.python.org/3/library/queue.html](https://docs.python.org/3/library/queue.html)  
30. Hand landmarks detection guide for Web | Google AI Edge \- Gemini API, accessed June 22, 2025, [https://ai.google.dev/edge/mediapipe/solutions/vision/hand\_landmarker/web\_js](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/web_js)  
31. how does z define the depth information of the key point? · Issue \#5075 · google-ai-edge/mediapipe \- GitHub, accessed June 22, 2025, [https://github.com/google-ai-edge/mediapipe/issues/5075](https://github.com/google-ai-edge/mediapipe/issues/5075)  
32. Exponential Moving Averages (EMA): A Guide for Traders \- ThinkMarkets, accessed June 22, 2025, [https://www.thinkmarkets.com/en/trading-academy/forex/exponential-moving-averages/](https://www.thinkmarkets.com/en/trading-academy/forex/exponential-moving-averages/)  
33. What is EMA? How to Use Exponential Moving Average With Formula \- Investopedia, accessed June 22, 2025, [https://www.investopedia.com/terms/e/ema.asp](https://www.investopedia.com/terms/e/ema.asp)  
34. Exponential Moving Average: Formula, Settings and How to Use it | IFCM Hong Kong, accessed June 22, 2025, [https://www.ifcmarkets.hk/en/ntx-indicators/exponential-moving-average](https://www.ifcmarkets.hk/en/ntx-indicators/exponential-moving-average)  
35. EMA Trading: Mastering the Exponential Moving Average Indicator \- Forex Tester, accessed June 22, 2025, [https://forextester.com/blog/exponential-moving-average](https://forextester.com/blog/exponential-moving-average)  
36. Exponential Smoothing \- Explore Analytics: The Wiki, accessed June 22, 2025, [https://www.exploreanalytics.com/wiki/index.php/Exponential\_Smoothing](https://www.exploreanalytics.com/wiki/index.php/Exponential_Smoothing)  
37. Exponential Filter \- Greg Stanley and Associates, accessed June 22, 2025, [https://gregstanleyandassociates.com/whitepapers/FaultDiagnosis/Filtering/Exponential-Filter/exponential-filter.htm](https://gregstanleyandassociates.com/whitepapers/FaultDiagnosis/Filtering/Exponential-Filter/exponential-filter.htm)  
38. 3 dB cut-off frequency of exponentially weighted moving average filter, accessed June 22, 2025, [https://dsp.stackexchange.com/questions/28308/3-db-cut-off-frequency-of-exponentially-weighted-moving-average-filter](https://dsp.stackexchange.com/questions/28308/3-db-cut-off-frequency-of-exponentially-weighted-moving-average-filter)  
39. Development and Evaluation of a Low-Jitter Hand Tracking System for Improving Typing Efficiency in a Virtual Reality Workspace \- MDPI, accessed June 22, 2025, [https://www.mdpi.com/2414-4088/9/1/4](https://www.mdpi.com/2414-4088/9/1/4)  
40. Development and Evaluation of Low-Jitter Hand Tracking System for Improving Typing Efficiency in Virtual Reality Workspace \- ResearchGate, accessed June 22, 2025, [https://www.researchgate.net/publication/376418865\_Development\_and\_Evaluation\_of\_Low-Jitter\_Hand\_Tracking\_System\_for\_Improving\_Typing\_Efficiency\_in\_Virtual\_Reality\_Workspace](https://www.researchgate.net/publication/376418865_Development_and_Evaluation_of_Low-Jitter_Hand_Tracking_System_for_Improving_Typing_Efficiency_in_Virtual_Reality_Workspace)  
41. Python OpenCV | cv2.rectangle() method \- GeeksforGeeks, accessed June 22, 2025, [https://www.geeksforgeeks.org/python/python-opencv-cv2-rectangle-method/](https://www.geeksforgeeks.org/python/python-opencv-cv2-rectangle-method/)  
42. Use OpenCV to draw grid lines on an image. \- GitHub Gist, accessed June 22, 2025, [https://gist.github.com/mathandy/389ddbad48810d188bdc997c3a1dab0c](https://gist.github.com/mathandy/389ddbad48810d188bdc997c3a1dab0c)  
43. Finger counter using MediaPipe \- Educative.io, accessed June 22, 2025, [https://www.educative.io/answers/finger-counter-using-mediapipe](https://www.educative.io/answers/finger-counter-using-mediapipe)  
44. Hand landmarks detection guide | Google AI Edge \- Gemini API, accessed June 22, 2025, [https://ai.google.dev/edge/mediapipe/solutions/vision/hand\_landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)  
45. point inside rect \- OpenCV Q\&A Forum, accessed June 22, 2025, [https://answers.opencv.org/question/225203/point-inside-rect/](https://answers.opencv.org/question/225203/point-inside-rect/)  
46. Detect Polygons in Image using OpenCV Python \- Tutorialspoint, accessed June 22, 2025, [https://www.tutorialspoint.com/how-to-detect-polygons-in-image-using-opencv-python](https://www.tutorialspoint.com/how-to-detect-polygons-in-image-using-opencv-python)  
47. Python | Detect Polygons in an Image using OpenCV \- GeeksforGeeks, accessed June 22, 2025, [https://www.geeksforgeeks.org/python-detect-polygons-in-an-image-using-opencv/](https://www.geeksforgeeks.org/python-detect-polygons-in-an-image-using-opencv/)  
48. MPE \- MIDI Polyphonic Expression · probonopd MiniDexed · Discussion \#591 \- GitHub, accessed June 22, 2025, [https://github.com/probonopd/MiniDexed/discussions/591](https://github.com/probonopd/MiniDexed/discussions/591)  
49. MPE \- MIDI Polyphonic Expression \- StudioCode.dev, accessed June 22, 2025, [https://studiocode.dev/resources/mpe/](https://studiocode.dev/resources/mpe/)  
50. Tutorial: Understanding MPE zones \- JUCE, accessed June 22, 2025, [https://juce.com/tutorials/tutorial\_mpe\_zones/](https://juce.com/tutorials/tutorial_mpe_zones/)  
51. Calculate speed, distance and time \- GeeksforGeeks, accessed June 22, 2025, [https://www.geeksforgeeks.org/dsa/calculate-speed-distance-time/](https://www.geeksforgeeks.org/dsa/calculate-speed-distance-time/)  
52. Calculate speed/velocity of an object \- Processing 2.x and 3.x Forum, accessed June 22, 2025, [https://forum.processing.org/two/discussion/27789/calculate-speed-velocity-of-an-object.html](https://forum.processing.org/two/discussion/27789/calculate-speed-velocity-of-an-object.html)  
53. Calculate velocity of a point between frames \- python \- Stack Overflow, accessed June 22, 2025, [https://stackoverflow.com/questions/79658724/calculate-velocity-of-a-point-between-frames](https://stackoverflow.com/questions/79658724/calculate-velocity-of-a-point-between-frames)  
54. Python \- Facial and hand recognition using MediaPipe Holistic \- GeeksforGeeks, accessed June 22, 2025, [https://www.geeksforgeeks.org/machine-learning/python-facial-and-hand-recognition-using-mediapipe-holistic/](https://www.geeksforgeeks.org/machine-learning/python-facial-and-hand-recognition-using-mediapipe-holistic/)  
55. How do we calculate the Euclidean distance between two data points using basic Python operations? \- EITCA Academy, accessed June 22, 2025, [https://eitca.org/artificial-intelligence/eitc-ai-mlp-machine-learning-with-python/programming-machine-learning/programming-own-k-nearest-neighbors-algorithm/examination-review-programming-own-k-nearest-neighbors-algorithm/how-do-we-calculate-the-euclidean-distance-between-two-data-points-using-basic-python-operations/](https://eitca.org/artificial-intelligence/eitc-ai-mlp-machine-learning-with-python/programming-machine-learning/programming-own-k-nearest-neighbors-algorithm/examination-review-programming-own-k-nearest-neighbors-algorithm/how-do-we-calculate-the-euclidean-distance-between-two-data-points-using-basic-python-operations/)  
56. How to Compute Euclidean Distance in Python \- Shiksha Online, accessed June 22, 2025, [https://www.shiksha.com/online-courses/articles/how-to-compute-euclidean-distance-in-python/](https://www.shiksha.com/online-courses/articles/how-to-compute-euclidean-distance-in-python/)  
57. Managing MIDI pitchbend messages \- UCI Sites \- UC Irvine, accessed June 22, 2025, [https://sites.uci.edu/camp2014/2014/04/30/managing-midi-pitchbend-messages/](https://sites.uci.edu/camp2014/2014/04/30/managing-midi-pitchbend-messages/)  
58. MIDI Pitch Bend | Sound Examples \- GitHub Pages, accessed June 22, 2025, [https://tigoe.github.io/SoundExamples/midi-pitch-bend.html](https://tigoe.github.io/SoundExamples/midi-pitch-bend.html)  
59. Pitch bend range \- moForte, accessed June 22, 2025, [https://www.moforte.com/geoShredAssets7000/help/pitchBendRange.html](https://www.moforte.com/geoShredAssets7000/help/pitchBendRange.html)  
60. Face and Hand Landmarks Detection using Python \- Mediapipe, OpenCV \- GeeksforGeeks, accessed June 22, 2025, [https://www.geeksforgeeks.org/machine-learning/face-and-hand-landmarks-detection-using-python-mediapipe-opencv/](https://www.geeksforgeeks.org/machine-learning/face-and-hand-landmarks-detection-using-python-mediapipe-opencv/)  
61. MediaPipe \- Warudo Handbook, accessed June 22, 2025, [https://docs.warudo.app/docs/mocap/mediapipe](https://docs.warudo.app/docs/mocap/mediapipe)  
62. Limb movement recognition method based on Mediapipe Pose \- International Journal of Trend in Research and Development, accessed June 22, 2025, [https://www.ijtrd.com/papers/IJTRD28767.pdf](https://www.ijtrd.com/papers/IJTRD28767.pdf)  
63. rtmidi package — python-rtmidi 1.5.8 documentation \- GitHub Pages, accessed June 22, 2025, [https://spotlightkid.github.io/python-rtmidi/rtmidi.html](https://spotlightkid.github.io/python-rtmidi/rtmidi.html)  
64. lvdopqt/midi2gpio: Python application that hosts a virtual MIDI port using rtmidi and sends received messages to Raspberry's GPIO \- GitHub, accessed June 22, 2025, [https://github.com/nugluke/midi2gpio](https://github.com/nugluke/midi2gpio)  
65. MIDI Program Change message | RecordingBlogs, accessed June 22, 2025, [https://www.recordingblogs.com/wiki/midi-program-change-message](https://www.recordingblogs.com/wiki/midi-program-change-message)  
66. MIDI Program Changes \- a quick reference guide and resource : r/synthesizers \- Reddit, accessed June 22, 2025, [https://www.reddit.com/r/synthesizers/comments/tfsfvj/midi\_program\_changes\_a\_quick\_reference\_guide\_and/](https://www.reddit.com/r/synthesizers/comments/tfsfvj/midi_program_changes_a_quick_reference_guide_and/)  
67. Python Video Processing: 6 Useful Libraries and a Quick Tutorial \- Cloudinary, accessed June 22, 2025, [https://cloudinary.com/guides/front-end-development/python-video-processing-6-useful-libraries-and-a-quick-tutorial](https://cloudinary.com/guides/front-end-development/python-video-processing-6-useful-libraries-and-a-quick-tutorial)  
68. Multithreading in Python \- GeeksforGeeks, accessed June 22, 2025, [https://www.geeksforgeeks.org/python/multithreading-python-set-1/](https://www.geeksforgeeks.org/python/multithreading-python-set-1/)  
69. Python Multithreading: Benefits, Use Cases, and Comparison \- Pieces for Developers, accessed June 22, 2025, [https://pieces.app/blog/python-multithreading-benefits-use-cases-and-comparison](https://pieces.app/blog/python-multithreading-benefits-use-cases-and-comparison)  
70. Object detection guide for Python | Google AI Edge \- Gemini API, accessed June 22, 2025, [https://ai.google.dev/edge/mediapipe/solutions/vision/object\_detector/python](https://ai.google.dev/edge/mediapipe/solutions/vision/object_detector/python)  
71. yushulx/python-lite-camera: A lightweight, cross-platform library for capturing RGB frames from cameras \- GitHub, accessed June 22, 2025, [https://github.com/yushulx/python-lite-camera](https://github.com/yushulx/python-lite-camera)  
72. Python Tkinter \- GeeksforGeeks, accessed June 22, 2025, [https://www.geeksforgeeks.org/python/python-gui-tkinter/](https://www.geeksforgeeks.org/python/python-gui-tkinter/)  
73. Welcome to the World of PyQt Buttons\! \- HeyCoach | Blogs, accessed June 22, 2025, [https://blog.heycoach.in/pyqt-buttons/](https://blog.heycoach.in/pyqt-buttons/)  
74. Use a Drag & Drop Editor to Make Tkinter Python GUI Applications\! \- YouTube, accessed June 22, 2025, [https://m.youtube.com/watch?v=oLxFqpUbaAE\&pp=ygUII2d1aWJsb2I%3D](https://m.youtube.com/watch?v=oLxFqpUbaAE&pp=ygUII2d1aWJsb2I%3D)  
75. how to drag entire contents in a rectangle using tkinter python? \- Stack Overflow, accessed June 22, 2025, [https://stackoverflow.com/questions/60584611/how-to-drag-entire-contents-in-a-rectangle-using-tkinter-python](https://stackoverflow.com/questions/60584611/how-to-drag-entire-contents-in-a-rectangle-using-tkinter-python)  
76. Moving rectangle on a Tkinter Canvas by using move() in two directions by using a button, accessed June 22, 2025, [https://www.youtube.com/watch?v=2msviFNKo-Y](https://www.youtube.com/watch?v=2msviFNKo-Y)  
77. PyQt Event Handling \- Tutorialspoint, accessed June 22, 2025, [https://www.tutorialspoint.com/pyqt/pyqt\_event\_handling.htm](https://www.tutorialspoint.com/pyqt/pyqt_event_handling.htm)  
78. Python PyQt custom widget event handling \- w3resource, accessed June 22, 2025, [https://www.w3resource.com/python-exercises/pyqt/python-pyqt-basic-exercise-9.php](https://www.w3resource.com/python-exercises/pyqt/python-pyqt-basic-exercise-9.php)  
79. Customizing Tkinter slider widget with unique theme \- w3resource, accessed June 22, 2025, [https://www.w3resource.com/python-exercises/tkinter/python-tkinter-custom-widgets-and-themes-exercise-5.php](https://www.w3resource.com/python-exercises/tkinter/python-tkinter-custom-widgets-and-themes-exercise-5.php)  
80. Tkinter Scale to set and get value by moving slider with orient & other options and methods, accessed June 22, 2025, [https://www.youtube.com/watch?v=5uO91Ti1vUo](https://www.youtube.com/watch?v=5uO91Ti1vUo)  
81. Sliders in Python PyQt5, accessed June 22, 2025, [https://pythonprogramminglanguage.com/pyqt5-sliders/](https://pythonprogramminglanguage.com/pyqt5-sliders/)  
82. Python PyQt slider application \- w3resource, accessed June 22, 2025, [https://www.w3resource.com/python-exercises/pyqt/python-pyqt-connecting-signals-to-slots-exercise-4.php](https://www.w3resource.com/python-exercises/pyqt/python-pyqt-connecting-signals-to-slots-exercise-4.php)  
83. PyQt QSlider Widget Signals \- Tutorialspoint, accessed June 22, 2025, [https://www.tutorialspoint.com/pyqt/pyqt\_qslider\_widget\_signal.htm](https://www.tutorialspoint.com/pyqt/pyqt_qslider_widget_signal.htm)  
84. My (successful) experience with low latency audio in Linux : r/linuxaudio \- Reddit, accessed June 22, 2025, [https://www.reddit.com/r/linuxaudio/comments/1iknlnz/my\_successful\_experience\_with\_low\_latency\_audio/](https://www.reddit.com/r/linuxaudio/comments/1iknlnz/my_successful_experience_with_low_latency_audio/)  
85. Out Of Sync Audio & Midi : LOGIC PRO X : SINGLE FUNCTIONS \- YouTube, accessed June 22, 2025, [https://www.youtube.com/watch?v=GkGSUDucsl8](https://www.youtube.com/watch?v=GkGSUDucsl8)  
86. MIDI Clock Doesn't Work (and a Guide to What You Can Do About It) \- YouTube, accessed June 22, 2025, [https://www.youtube.com/watch?v=mBSrSHLLqPA](https://www.youtube.com/watch?v=mBSrSHLLqPA)  
87. MediaPipe Development Team \- Moravio, accessed June 22, 2025, [https://www.moravio.com/technologies/mediapipe](https://www.moravio.com/technologies/mediapipe)  
88. Exploring MediaPipe optimization strategies for real-time sign language recognition, accessed June 22, 2025, [https://ctujs.ctu.edu.vn/index.php/ctujs/article/view/716](https://ctujs.ctu.edu.vn/index.php/ctujs/article/view/716)  
89. Gesture recognition task guide | Google AI Edge \- Gemini API, accessed June 22, 2025, [https://ai.google.dev/edge/mediapipe/solutions/vision/gesture\_recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer)  
90. Hand Gesture Recognition using MediaPipe \- GitHub, accessed June 22, 2025, [https://github.com/baukk/Gesture-Recognition](https://github.com/baukk/Gesture-Recognition)  
91. Gesture recognition guide for Python | Google AI Edge \- Gemini API, accessed June 22, 2025, [https://ai.google.dev/edge/mediapipe/solutions/vision/gesture\_recognizer/python](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/python)