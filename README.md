# Hand Tracking VST Controller

This project provides a minimal framework for a webcam‑based MIDI controller
using hand tracking. The application structure follows the included design and
implementation specifications.

## Development

Create a Python environment and install dependencies using `uv` or `pip`:

```bash
pip install mediapipe opencv-python python-rtmidi numpy
```

Run the application:

```bash
python -m hand_tracking_vst.src.main
```

Run tests with `pytest`:

```bash
pytest
```
