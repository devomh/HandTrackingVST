# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a real-time hand-tracking MIDI controller that converts webcam-based hand gestures into MPE (MIDI Polyphonic Expression) messages. The system uses MediaPipe for hand detection and python-rtmidi for MIDI output, targeting low-latency musical performance.

## Development Commands

### Environment Setup
```bash
# Initialize with uv (preferred)
cd hand_tracking_vst/
uv sync

# Run application
uv run python -m src.main

# Alternative with pip
pip install mediapipe opencv-python python-rtmidi numpy
python -m hand_tracking_vst.src.main
```

### Development Tools
```bash
# Run tests
uv run pytest
pytest hand_tracking_vst/tests/

# Run single test
uv run pytest hand_tracking_vst/tests/test_config_manager.py

# Code formatting and linting
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/

# Build distribution
uv build
```

## Core Architecture

### Signal Flow
1. **Video Capture** → **HandTracker** (MediaPipe) → **Smoothing** (EMA)
2. **ZoneMapper** (grid layout) → **ExpressionEngine** (pressure, velocity, pitch-bend)
3. **MidiController** (MPE channel allocation) → **Virtual MIDI Port**

### Component Responsibilities

**HandTracker** (`src/core/hand_tracker.py`)
- MediaPipe integration for 21-landmark hand detection
- Applies configurable smoothing filters (EMA, future Kalman)
- Extracts fingertip positions with Z-depth for pressure sensing

**ZoneMapper** (`src/core/zone_mapper.py`)
- Maps 2D hand positions to configurable grid zones (3x4, 2x6, etc.)
- Handles note mapping with chromatic, interval, or scale-based assignments
- Supports runtime layout reconfiguration

**MidiController** (`src/core/midi_controller.py`)
- MPE implementation with dynamic channel allocation (channels 2-16)
- Per-note expression: pitch-bend, velocity, CC messages
- Virtual MIDI port management via python-rtmidi

**ExpressionEngine** (`src/core/expression_engine.py`)
- Converts hand kinematics to musical expression:
  - Z-depth → pressure/aftertouch
  - 2D speed → velocity
  - Swipe gestures → pitch-bend
  - Vertical motion → additional CC

### Configuration System

**ConfigManager** (`src/config/config_manager.py`)
- Hierarchical JSON configuration with dot notation access
- Runtime reconfiguration support
- Layout presets for common configurations
- Merges `default_config.json` with `user_config.json`

**Key Configuration Sections:**
- `camera`: device_id, resolution, fps
- `hand_tracking`: confidence thresholds, max_hands
- `smoothing`: type (ema/kalman), alpha parameters
- `layout`: grid dimensions, note mapping, presets
- `midi`: virtual port name, MPE settings

### Extension Points

**Abstract Base Classes:**
- `BaseSmoother` (`src/smoothing/`) - for new smoothing algorithms
- `BaseLayout` (`src/layouts/`) - for alternative zone layouts (radial, custom)

**Plugin Discovery:**
- Automatic detection of new smoothers/layouts in respective directories
- Factory pattern for dynamic instantiation

## Key Implementation Details

### MPE Channel Management
- Channel 1 reserved for global messages
- Channels 2-16 dynamically allocated per active note
- Automatic channel release on note-off events

### Layout Configurability
- Grid sizes: 3x4 (default), 2x6, 4x3, 6x2, custom NxM
- Note intervals: chromatic (1), fourths (5), octaves (12), custom scales
- Fill orders: row_major, column_major

### Real-time Performance
- Multi-threaded architecture: video capture, processing, MIDI output
- Non-blocking video capture recommended for low latency
- EMA smoothing tuned for ~5-8 frame responsiveness (α ≈ 0.1-0.2)

### Expression Parameter Mapping
- **Pressure**: fingertip Z-depth → CC74 or channel pressure
- **Velocity**: frame-to-frame 2D speed → note velocity (0-127)
- **Pitch-bend**: swipe detection across zones → 14-bit pitch-bend
- **Vertical CC**: upward/downward motion → configurable CC

## Configuration Examples

```json
// Pentatonic 2x6 layout
{
  "layout": {
    "rows": 2,
    "columns": 6,
    "base_note": 60,
    "note_interval": "pentatonic",
    "scale_pattern": [0, 2, 4, 7, 9]
  }
}

// Fourths tuning 3x4
{
  "layout": {
    "rows": 3,
    "columns": 4,
    "base_note": 60,
    "note_interval": 5
  }
}
```

## Testing Strategy

Tests focus on configuration management and zone mapping logic. MediaPipe and MIDI components use mocks for hardware-independent testing.

The application entry point (`src/main.py`) demonstrates the component wiring pattern for the real-time processing pipeline.