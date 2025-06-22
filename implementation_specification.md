# Hand-Tracking VST Controller Implementation Specification

## 1. Project Architecture

### 1.1 Directory Structure
```
hand_tracking_vst/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── hand_tracker.py           # MediaPipe hand detection
│   │   ├── midi_controller.py        # MIDI/MPE output management
│   │   ├── zone_mapper.py            # Grid layout & note mapping
│   │   ├── expression_engine.py      # Parameter extraction & processing
│   │   └── event_manager.py          # Event coordination & timing
│   ├── smoothing/
│   │   ├── __init__.py
│   │   ├── base_smoother.py          # Abstract smoothing interface
│   │   ├── ema_smoother.py           # Exponential Moving Average
│   │   └── kalman_smoother.py        # Future: Kalman filter option
│   ├── layouts/
│   │   ├── __init__.py
│   │   ├── base_layout.py            # Abstract layout interface
│   │   ├── grid_layout.py            # 3x4 grid implementation
│   │   └── radial_layout.py          # Future: radial layout option
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_manager.py         # Configuration persistence
│   │   ├── calibration.py            # Zone calibration utilities
│   │   └── validator.py              # Configuration validation
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py            # Primary application window
│   │   ├── calibration_ui.py         # Calibration interface
│   │   ├── settings_dialog.py        # Settings configuration
│   │   └── monitor_widget.py         # Real-time monitoring display
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── math_utils.py             # Mathematical utilities
│   │   ├── midi_utils.py             # MIDI helper functions
│   │   └── performance.py            # Performance monitoring
│   └── main.py                       # Application entry point
├── config/
│   ├── default_config.json           # Factory default settings
│   ├── user_config.json              # User customizations
│   └── calibration_data.json         # Stored calibration data
├── tests/
│   ├── test_hand_tracker.py
│   ├── test_midi_controller.py
│   ├── test_zone_mapper.py
│   └── test_config_manager.py
├── pyproject.toml                    # uv project configuration
├── uv.lock                          # Dependency lock file
└── README.md
```

## 2. Core Components

### 2.1 HandTracker Class
```python
class HandTracker:
    """MediaPipe-based hand detection and landmark extraction"""
    
    def __init__(self, config: Dict):
        self.mp_hands = mediapipe.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=config.get('detection_confidence', 0.7),
            min_tracking_confidence=config.get('tracking_confidence', 0.5)
        )
        self.smoother = create_smoother(config['smoothing'])
        
    def process_frame(self, frame: np.ndarray) -> List[HandLandmarks]:
        """Process video frame and return smoothed hand landmarks"""
        
    def get_fingertip_positions(self, landmarks: HandLandmarks) -> Dict[str, Point3D]:
        """Extract fingertip positions with Z-depth for pressure"""
```

### 2.2 MidiController Class
```python
class MidiController:
    """MPE-compatible MIDI output management"""
    
    def __init__(self, config: Dict):
        self.midi_out = rtmidi.MidiOut()
        self.channel_manager = ChannelManager(max_channels=16)
        self.active_notes = {}  # Track per-channel note states
        
    def trigger_note(self, note: int, velocity: int, expression: ExpressionData):
        """Trigger note with MPE expression on dedicated channel"""
        
    def update_expression(self, channel: int, expression: ExpressionData):
        """Update real-time expression parameters"""
        
    def release_note(self, channel: int):
        """Release note and free channel"""
```

### 2.3 ZoneMapper Class
```python
class ZoneMapper:
    """Grid layout and note mapping management"""
    
    def __init__(self, layout: BaseLayout, config: Dict):
        self.layout = layout
        self.note_mapping = self._create_note_mapping(config)
        self.calibration_data = load_calibration(config)
        self.config = config
        
    def get_active_zones(self, fingertips: Dict[str, Point3D]) -> List[ZoneActivation]:
        """Determine which zones are activated by fingertips"""
        
    def map_zone_to_note(self, zone_id: int) -> int:
        """Convert zone ID to MIDI note number using configured mapping"""
        return self.layout.get_note_for_zone(zone_id)
        
    def reconfigure_layout(self, new_config: Dict):
        """Dynamically reconfigure layout and note mapping"""
        self.config.update(new_config)
        self.layout.configure(self.config)
        self.note_mapping = self._create_note_mapping(self.config)
        
    def _create_note_mapping(self, config: Dict) -> Dict[int, int]:
        """Create zone-to-note mapping based on configuration"""
        base_note = config.get('base_note', 60)
        interval_type = config.get('note_interval', 1)
        fill_order = config.get('fill_order', 'row_major')
        
        if isinstance(interval_type, str):
            if interval_type == 'pentatonic':
                scale_pattern = config.get('scale_pattern', [0, 2, 4, 7, 9])
                return self._create_scale_mapping(base_note, scale_pattern, fill_order)
            elif interval_type == 'major':
                return self._create_scale_mapping(base_note, [0, 2, 4, 5, 7, 9, 11], fill_order)
            elif interval_type == 'minor':
                return self._create_scale_mapping(base_note, [0, 2, 3, 5, 7, 8, 10], fill_order)
        else:
            # Numeric interval (chromatic, fourths, etc.)
            return self._create_interval_mapping(base_note, interval_type, fill_order)
        
    def get_current_layout_info(self) -> Dict:
        """Return current layout configuration info"""
        return {
            'grid_size': f"{self.config.get('rows', 3)}x{self.config.get('columns', 4)}",
            'total_zones': self.layout.get_zone_count(),
            'base_note': self.config.get('base_note', 60),
            'note_interval': self.config.get('note_interval', 1),
            'note_range': self._get_note_range()
        }
        
    def _get_note_range(self) -> str:
        """Get the MIDI note range as a readable string"""
        zone_count = self.layout.get_zone_count()
        if zone_count == 0:
            return "No zones"
            
        lowest_note = self.note_mapping.get(0, 60)
        highest_note = self.note_mapping.get(zone_count - 1, 60)
        
        def note_to_name(midi_note: int) -> str:
            notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = (midi_note // 12) - 1
            note_name = notes[midi_note % 12]
            return f"{note_name}{octave}"
            
        return f"{note_to_name(lowest_note)} - {note_to_name(highest_note)}"
            
    def _create_interval_mapping(self, base_note: int, interval: int, fill_order: str) -> Dict[int, int]:
        """Create mapping with fixed interval between notes"""
        mapping = {}
        zone_count = self.layout.get_zone_count()
        
        if fill_order == 'column_major':
            # Fill columns first, then rows
            rows = self.config.get('rows', 3)
            cols = self.config.get('columns', 4)
            for zone_id in range(zone_count):
                col = zone_id // rows
                row = zone_id % rows
                sequential_id = col + (row * cols)
                mapping[zone_id] = base_note + (sequential_id * interval)
        else:  # row_major (default)
            for zone_id in range(zone_count):
                mapping[zone_id] = base_note + (zone_id * interval)
                
        return mapping
        
    def _create_scale_mapping(self, base_note: int, scale_pattern: List[int], fill_order: str) -> Dict[int, int]:
        """Create mapping following a musical scale pattern"""
        mapping = {}
        zone_count = self.layout.get_zone_count()
        
        for zone_id in range(zone_count):
            octave = zone_id // len(scale_pattern)
            scale_degree = zone_id % len(scale_pattern)
            mapping[zone_id] = base_note + (octave * 12) + scale_pattern[scale_degree]
            
        return mapping
```

### 2.4 ExpressionEngine Class
```python
class ExpressionEngine:
    """Extract and process expression parameters"""
    
    def __init__(self, config: Dict):
        self.velocity_calculator = VelocityCalculator(config)
        self.pressure_calculator = PressureCalculator(config)
        self.pitch_bend_detector = PitchBendDetector(config)
        
    def extract_expression(self, current_frame: HandData, 
                          previous_frame: HandData) -> ExpressionData:
        """Extract all expression parameters from hand movement"""
        
    def calculate_velocity(self, movement: Vector2D, time_delta: float) -> int:
        """Convert 2D movement to MIDI velocity (0-127)"""
        
    def calculate_pressure(self, z_depth: float) -> int:
        """Convert Z-depth to pressure value (0-127)"""
        
    def detect_pitch_bend(self, trajectory: List[Point2D]) -> int:
        """Detect swipe gestures for pitch bend (-8192 to 8191)"""
```

## 3. Configuration System

### 3.1 Configuration Structure
```json
{
  "display": {
    "window_title": "Hand-Tracking VST Controller",
    "fps_display": true,
    "debug_overlay": false
  },
  "camera": {
    "device_id": 0,
    "width": 640,
    "height": 480,
    "fps": 30
  },
  "hand_tracking": {
    "detection_confidence": 0.7,
    "tracking_confidence": 0.5,
    "max_hands": 2
  },
  "smoothing": {
    "type": "ema",
    "alpha": 0.3,
    "position_alpha": 0.3,
    "velocity_alpha": 0.5
  },
  "layout": {
    "type": "grid",
    "rows": 3,
    "columns": 4,
    "base_note": 60,
    "note_interval": 1,
    "interval_direction": "chromatic",
    "fill_order": "row_major",
    "margin": 0.1,
    "presets": {
      "chromatic_3x4": {
        "rows": 3,
        "columns": 4,
        "base_note": 60,
        "note_interval": 1,
        "interval_direction": "chromatic"
      },
      "chromatic_2x6": {
        "rows": 2,
        "columns": 6,
        "base_note": 60,
        "note_interval": 1,
        "interval_direction": "chromatic"
      },
      "pentatonic_3x4": {
        "rows": 3,
        "columns": 4,
        "base_note": 60,
        "note_interval": "pentatonic",
        "scale_pattern": [0, 2, 4, 7, 9]
      },
      "fourths_2x6": {
        "rows": 2,
        "columns": 6,
        "base_note": 60,
        "note_interval": 5,
        "interval_direction": "up"
      },
      "octaves_3x4": {
        "rows": 3,
        "columns": 4,
        "base_note": 36,
        "note_interval": 12,
        "interval_direction": "up"
      }
    }
  },
  "midi": {
    "virtual_port_name": "HandTracker",
    "mpe_enabled": true,
    "velocity_curve": "linear",
    "pressure_sensitivity": 1.0
  },
  "expression": {
    "velocity_scaling": 1.0,
    "pressure_scaling": 1.0,
    "pitch_bend_sensitivity": 2.0,
    "vertical_cc_number": 74,
    "vertical_cc_scaling": 1.0
  },
  "calibration": {
    "auto_calibrate": true,
    "zone_overlap": 0.1,
    "activation_threshold": 0.02
  }
}
```

### 3.2 Configuration Management
```python
class ConfigManager:
    """Configuration persistence and validation"""
    
    def __init__(self, config_path: str = "config/user_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.validators = self._setup_validators()
        
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'midi.velocity_curve')"""
        
    def set(self, key_path: str, value):
        """Set configuration value and validate"""
        
    def save(self):
        """Persist configuration to disk"""
        
    def reload(self):
        """Reload configuration from disk"""
        
    def get_layout_presets(self) -> Dict[str, Dict]:
        """Return available layout presets"""
        return self.config.get('layout.presets', {})
        
    def apply_layout_preset(self, preset_name: str) -> Dict:
        """Apply a layout preset and return the configuration"""
        presets = self.get_layout_presets()
        if preset_name in presets:
            preset_config = presets[preset_name].copy()
            for key, value in preset_config.items():
                self.set(f'layout.{key}', value)
            return preset_config
        raise ValueError(f"Preset '{preset_name}' not found")
```

### 3.3 Dynamic Layout Configuration

The layout system supports real-time reconfiguration through several mechanisms:

#### Grid Size Configuration
- **Supported configurations**: 2x6, 3x4, 4x3, 6x2, 1x12, 12x1, custom NxM
- **Runtime switching**: Change grid dimensions without restarting
- **Automatic zone recalculation**: Zones automatically resize to maintain coverage

#### Note Interval Mapping Options

1. **Chromatic (default)**: Sequential semitones (interval = 1)
   - Example: C4, C#4, D4, D#4, E4...
   
2. **Custom Intervals**: Fixed interval between notes
   - Fourths (interval = 5): C4, F4, Bb4, Eb5...
   - Octaves (interval = 12): C4, C5, C6, C7...
   - Perfect fifths (interval = 7): C4, G4, D5, A5...
   
3. **Scale-based Mapping**: Follow musical scale patterns
   - Pentatonic: Uses scale_pattern [0, 2, 4, 7, 9]
   - Major scale: [0, 2, 4, 5, 7, 9, 11]
   - Minor scale: [0, 2, 3, 5, 7, 8, 10]
   - Custom scales: User-defined patterns

#### Runtime Configuration UI
```python
class LayoutConfigWidget:
    """UI component for dynamic layout configuration"""
    
    def __init__(self, config_manager: ConfigManager, zone_mapper: ZoneMapper):
        self.config_manager = config_manager
        self.zone_mapper = zone_mapper
        self.setup_ui()
        
    def on_grid_size_changed(self, rows: int, cols: int):
        """Handle grid size change"""
        self.config_manager.set('layout.rows', rows)
        self.config_manager.set('layout.columns', cols)
        self.zone_mapper.reconfigure_layout(self.config_manager.config['layout'])
        
    def on_note_interval_changed(self, interval_type: str, custom_value: int = None):
        """Handle note interval change"""
        if interval_type == 'custom' and custom_value:
            self.config_manager.set('layout.note_interval', custom_value)
        else:
            self.config_manager.set('layout.note_interval', interval_type)
        self.zone_mapper.reconfigure_layout(self.config_manager.config['layout'])
        
    def on_preset_selected(self, preset_name: str):
        """Apply a layout preset"""
        try:
            preset_config = self.config_manager.apply_layout_preset(preset_name)
            self.zone_mapper.reconfigure_layout(preset_config)
            self.update_ui_from_config()
        except ValueError as e:
            self.show_error(str(e))
```

## 4. Modular Extension System

### 4.1 Abstract Base Classes

#### BaseSmoother
```python
class BaseSmoother(ABC):
    """Abstract base class for smoothing algorithms"""
    
    @abstractmethod
    def smooth(self, new_value: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply smoothing to new measurement"""
        
    @abstractmethod
    def reset(self):
        """Reset smoother state"""
```

#### BaseLayout
```python
class BaseLayout(ABC):
    """Abstract base class for zone layouts"""
    
    @abstractmethod
    def get_zone_bounds(self) -> List[Rectangle]:
        """Return list of zone boundaries"""
        
    @abstractmethod
    def point_to_zone(self, point: Point2D) -> Optional[int]:
        """Convert screen point to zone ID"""
        
    @abstractmethod
    def get_zone_count(self) -> int:
        """Return total number of zones"""
        
    @abstractmethod
    def configure(self, config: Dict):
        """Reconfigure layout parameters"""
        
    @abstractmethod
    def get_note_for_zone(self, zone_id: int) -> int:
        """Get MIDI note number for zone"""
```

### 4.2 Plugin Discovery System
```python
class PluginManager:
    """Automatic discovery and loading of extension modules"""
    
    def __init__(self):
        self.smoothers = self._discover_smoothers()
        self.layouts = self._discover_layouts()
        self.layout_presets = self._load_layout_presets()
        
    def create_smoother(self, smoother_type: str, config: Dict) -> BaseSmoother:
        """Factory method for smoother creation"""
        
    def create_layout(self, layout_type: str, config: Dict) -> BaseLayout:
        """Factory method for layout creation"""
        
    def get_layout_presets(self) -> Dict[str, Dict]:
        """Return available layout presets"""
        return self.layout_presets
        
    def apply_preset(self, preset_name: str, layout: BaseLayout) -> BaseLayout:
        """Apply a preset configuration to a layout"""
        if preset_name in self.layout_presets:
            layout.configure(self.layout_presets[preset_name])
        return layout
```

## 5. Implementation Details

### 5.1 Real-Time Processing Pipeline
1. **Frame Capture** (30 FPS target)
2. **Hand Detection** (MediaPipe processing)
3. **Landmark Smoothing** (EMA filtering)
4. **Zone Detection** (Spatial mapping)
5. **Expression Extraction** (Multi-parameter calculation)
6. **MIDI Generation** (MPE message creation)
7. **Output Transmission** (Virtual MIDI port)

### 5.2 Performance Optimizations
- **Frame Skipping**: Drop frames if processing falls behind
- **Landmark Caching**: Cache processed landmarks for expression calculation
- **MIDI Throttling**: Limit CC message frequency to prevent flooding
- **Memory Pooling**: Reuse objects to minimize garbage collection

### 5.3 Error Handling Strategy
- **Camera Failure**: Graceful degradation with error display
- **MIDI Port Issues**: Automatic port recreation attempts
- **MediaPipe Errors**: Frame skipping with error logging
- **Configuration Errors**: Fallback to default values with warnings

### 5.4 Calibration Procedure
1. **Automatic Detection**: Find hand boundaries in camera view
2. **Zone Adjustment**: Allow manual fine-tuning of zone positions
3. **Sensitivity Tuning**: Calibrate pressure and velocity responses
4. **Validation**: Test all zones with visual feedback

## 6. User Interface Design

### 6.1 Main Window Components
- **Camera View**: Live camera feed with zone overlay
- **Status Panel**: Connection status, FPS, active notes
- **Quick Controls**: Master volume, sensitivity sliders
- **Menu Bar**: File, Edit, View, Tools, Help

### 6.2 Settings Dialog Sections
- **Camera Settings**: Device selection, resolution, FPS
- **MIDI Configuration**: Port selection, channel assignment
- **Expression Parameters**: Scaling factors, curve types
- **Layout Options**: Grid size, note mapping, calibration
- **Performance Settings**: Smoothing parameters, optimization flags

## 7. Testing Strategy

### 7.1 Unit Tests
- **Component Isolation**: Test each class independently
- **Mock Dependencies**: Use mocks for hardware interfaces
- **Configuration Validation**: Test all config parameter ranges
- **Mathematical Functions**: Verify expression calculations

### 7.2 Integration Tests
- **End-to-End Pipeline**: Full processing chain validation
- **MIDI Output Verification**: Capture and validate MIDI messages
- **Performance Benchmarks**: Frame rate and latency measurements
- **Error Recovery**: Test failure scenarios and recovery

## 8. Future Extensions

### 8.1 Additional Smoothing Methods
- **Kalman Filter**: Advanced state estimation
- **Particle Filter**: Non-linear tracking
- **Custom Filters**: User-defined smoothing algorithms

### 8.2 Alternative Layouts
- **Radial Layout**: Circular zone arrangement
- **Chromatic Layout**: Piano-key style mapping
- **Custom Layouts**: User-defined zone configurations

### 8.3 Advanced Features
- **Gesture Recognition**: Complex hand gestures for special functions
- **Multi-Hand Orchestration**: Coordinate multiple hands
- **Recording/Playback**: Capture and replay performances
- **Network Sync**: Multi-device coordination

## 9. Development Environment Setup

### 9.1 uv Package Management
```bash
# Initialize project with uv
uv init hand-tracking-vst
cd hand-tracking-vst

# Add dependencies
uv add mediapipe opencv-python python-rtmidi numpy
uv add --dev pytest black ruff mypy

# Create virtual environment and install dependencies
uv sync

# Run application
uv run python src/main.py

# Run tests
uv run pytest

# Code formatting and linting
uv run black src/
uv run ruff check src/
uv run mypy src/
```

### 9.2 Project Configuration (pyproject.toml)
```toml
[project]
name = "hand-tracking-vst"
version = "0.1.0"
description = "Real-time hand tracking MIDI controller with MPE support"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Musicians",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "mediapipe>=0.10.0",
    "opencv-python>=4.8.0",
    "python-rtmidi>=1.5.0",
    "numpy>=1.24.0",
    "tkinter",  # Usually included with Python
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[project.scripts]
hand-tracking-vst = "src.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.ruff]
select = ["E", "F", "W", "C90", "I", "N", "UP", "YTT", "S", "BLE", "FBT", "B", "A", "COM", "C4", "DTZ", "T10", "EM", "EXE", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]
ignore = ["E501", "S101"]  # Line too long, assert statements
line-length = 88
target-version = "py38"

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term"
```

### 9.3 Development Workflow
```bash
# Setup development environment
uv sync --dev

# Run in development mode with hot reload
uv run python -m src.main --dev

# Run tests with coverage
uv run pytest --cov=src

# Format code
uv run black src/ tests/
uv run ruff --fix src/ tests/

# Type checking
uv run mypy src/

# Build distribution
uv build
```

## 10. Deployment and Distribution

### 10.1 Package Requirements
- Python 3.8+ compatibility
- Cross-platform support (Windows, macOS, Linux)
- Minimal dependency footprint
- Standalone executable option

### 10.2 Installation Methods
```bash
# Install from source with uv
git clone <repository-url>
cd hand-tracking-vst
uv sync
uv run python -m src.main

# Install as package (future PyPI release)
uv add hand-tracking-vst

# Build standalone executable
uv add --dev pyinstaller
uv run pyinstaller --onefile src/main.py --name hand-tracking-vst
```

### 10.3 Distribution Options
- **Source Distribution**: `uv build` creates wheel and sdist
- **Executable Bundle**: PyInstaller for standalone deployment
- **Docker Container**: Multi-stage build with uv
- **GitHub Releases**: Automated builds with GitHub Actions

This specification provides a complete blueprint for implementing a modular, extensible hand-tracking VST controller that meets all requirements from the design specification while maintaining flexibility for future enhancements.