import cv2
import time
import signal
import sys
from pathlib import Path

from .config.config_manager import ConfigManager
from .core.hand_tracker import HandTracker
from .core.zone_mapper import ZoneMapper
from .core.midi_controller import MidiController
from .core.expression_engine import ExpressionEngine
from .core.event_manager import EventManager
from .layouts.grid_layout import GridLayout


class HandTrackingVSTApp:
    """Main application class for the Hand-Tracking VST Controller."""

    def __init__(self):
        self.running = False
        self.cap = None
        self.manager = None
        self.tracker = None
        self.midi = None

        # Load configuration
        config_path = Path(__file__).parent.parent / "config" / "user_config.json"
        self.config_manager = ConfigManager(str(config_path))
        self.config = self.config_manager.config

        # Merge with default config if user config is incomplete
        default_config_path = (
            Path(__file__).parent.parent / "config" / "default_config.json"
        )
        if default_config_path.exists():
            import json

            default_config = json.loads(default_config_path.read_text())
            # Merge configs (user config takes precedence)
            merged_config = {**default_config, **self.config}
            self.config = merged_config

        self.setup_components()

    def setup_components(self):
        """Initialize all system components."""
        print("Initializing Hand-Tracking VST Controller...")

        # Create layout
        layout_config = self.config.get("layout", {})
        layout = GridLayout(
            rows=layout_config.get("rows", 3),
            columns=layout_config.get("columns", 4),
            margin=layout_config.get("margin", 0.1),
        )

        # Initialize components
        self.tracker = HandTracker(self.config.get("hand_tracking", {}))
        mapper = ZoneMapper(layout, layout_config)
        self.midi = MidiController(self.config.get("midi", {}))
        expression = ExpressionEngine(self.config.get("expression", {}))

        # Create event manager
        self.manager = EventManager(self.tracker, mapper, self.midi, expression)

        print("✓ All components initialized successfully")

    def setup_camera(self):
        """Initialize camera capture."""
        camera_config = self.config.get("camera", {})
        device_id = camera_config.get("device_id", 0)
        width = camera_config.get("width", 640)
        height = camera_config.get("height", 480)
        fps = camera_config.get("fps", 30)

        print(f"Initializing camera (device {device_id}, {width}x{height}@{fps}fps)...")

        self.cap = cv2.VideoCapture(device_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera device {device_id}")

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

        print("✓ Camera initialized successfully")

    def draw_zones(self, frame, active_zones):
        """Draw zone grid overlay on frame."""
        layout_config = self.config.get("layout", {})
        rows = layout_config.get("rows", 3)
        columns = layout_config.get("columns", 4)
        margin = layout_config.get("margin", 0.1)
        base_note = layout_config.get("base_note", 60)
        note_interval = layout_config.get("note_interval", 1)

        h, w, _ = frame.shape

        # Calculate effective area (accounting for margins)
        margin_x = int(w * margin)
        margin_y = int(h * margin)
        effective_w = w - 2 * margin_x
        effective_h = h - 2 * margin_y

        # Draw grid
        for row in range(rows + 1):
            y = margin_y + int(row * effective_h / rows)
            cv2.line(frame, (margin_x, y), (w - margin_x, y), (255, 255, 255), 2)

        for col in range(columns + 1):
            x = margin_x + int(col * effective_w / columns)
            cv2.line(frame, (x, margin_y), (x, h - margin_y), (255, 255, 255), 2)

        # Draw zone labels for all zones
        for row in range(rows):
            for col in range(columns):
                zone_id = row * columns + col
                note_number = base_note + (zone_id * note_interval)
                
                x1 = margin_x + int(col * effective_w / columns)
                y1 = margin_y + int(row * effective_h / rows)
                x2 = margin_x + int((col + 1) * effective_w / columns)
                y2 = margin_y + int((row + 1) * effective_h / rows)
                
                # Calculate center of zone
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Convert MIDI note to note name
                note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                note_name = note_names[note_number % 12]
                octave = (note_number // 12) - 1
                note_text = f"{note_name}{octave}"
                
                # Draw zone background (semi-transparent)
                if zone_id in active_zones:
                    # Active zone - bright green
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)
                    cv2.addWeighted(frame, 0.6, overlay, 0.4, 0, frame)
                    text_color = (255, 255, 255)
                else:
                    # Inactive zone - subtle background
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), (100, 100, 100), -1)
                    cv2.addWeighted(frame, 0.9, overlay, 0.1, 0, frame)
                    text_color = (200, 200, 200)
                
                # Draw zone ID
                cv2.putText(
                    frame,
                    str(zone_id),
                    (x1 + 5, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    text_color,
                    1,
                )
                
                # Draw note name
                cv2.putText(
                    frame,
                    note_text,
                    (center_x - 15, center_y + 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    text_color,
                    2,
                )
                
                # Draw MIDI note number
                cv2.putText(
                    frame,
                    f"({note_number})",
                    (center_x - 20, center_y + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    text_color,
                    1,
                )

    def draw_status(self, frame, fps, active_zones):
        """Draw status information on frame."""
        # FPS counter
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        # Active zones count
        cv2.putText(
            frame,
            f"Active Zones: {len(active_zones)}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        # Active MIDI channels
        active_notes = self.midi.get_active_note_count()
        cv2.putText(
            frame,
            f"Active Notes: {active_notes}",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        # Activation mode
        mode_name = self.manager.zone_mapper.get_activation_mode_name()
        cv2.putText(
            frame,
            f"Mode: {mode_name}",
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        # Instructions
        cv2.putText(
            frame,
            "Press 'q' to quit, 's' to save, 'g' to toggle grid, 'f' for finger mode",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    def run(self):
        """Main application loop."""
        try:
            self.setup_camera()
            self.running = True

            print("Starting main loop... Press 'q' to quit")
            print("Controls:")
            print("  q: Quit application")
            print("  s: Save current configuration")
            print("  r: Reset hand tracking smoothing")
            print("  d: Toggle debug display")
            print("  g: Toggle grid overlay")
            print("  f: Cycle finger activation mode")

            # Performance tracking
            frame_count = 0
            fps_start_time = time.time()
            fps = 0.0
            show_debug = self.config.get("display", {}).get("debug_overlay", False)
            show_grid = self.config.get("display", {}).get("show_grid", True)

            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to read from camera")
                    break

                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)

                # Process frame through event manager
                self.manager.process(frame)

                # Get active zones for visualization
                hand_data = self.tracker.process_frame(frame)
                active_zones = []
                if hand_data:
                    fingertips = self.tracker.get_fingertip_positions(hand_data)
                    extended_fingers = self.tracker.get_extended_fingers(hand_data)
                    active_zones = self.manager.zone_mapper.get_active_zones(fingertips, extended_fingers)

                # Draw zone grid (always visible by default)
                if show_grid:
                    self.draw_zones(frame, active_zones)
                
                # Draw debug visualization if enabled
                if show_debug:
                    # Draw hand landmarks
                    if hand_data:
                        frame = self.tracker.draw_landmarks(frame, hand_data)

                # Calculate and display FPS
                frame_count += 1
                if frame_count % 30 == 0:  # Update FPS every 30 frames
                    current_time = time.time()
                    fps = 30.0 / (current_time - fps_start_time)
                    fps_start_time = current_time

                # Draw status overlay
                self.draw_status(frame, fps, active_zones)

                # Display frame
                cv2.imshow("Hand-Tracking VST Controller", frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print("Quit requested by user")
                    break
                elif key == ord("s"):
                    self.config_manager.save()
                    print("Configuration saved")
                elif key == ord("r"):
                    self.tracker.reset_smoother()
                    print("Hand tracking reset")
                elif key == ord("d"):
                    show_debug = not show_debug
                    print(f"Debug display: {'ON' if show_debug else 'OFF'}")
                elif key == ord("g"):
                    show_grid = not show_grid
                    print(f"Grid overlay: {'ON' if show_grid else 'OFF'}")
                elif key == ord("f"):
                    mode_name = self.manager.zone_mapper.cycle_activation_mode()
                    print(f"Finger activation mode: {mode_name}")

        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error during execution: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up...")
        self.running = False

        if self.manager:
            self.manager.cleanup()

        if self.midi:
            self.midi.cleanup()

        if self.tracker:
            self.tracker.cleanup()

        if self.cap:
            self.cap.release()

        cv2.destroyAllWindows()
        print("✓ Cleanup completed")

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        _ = frame  # Signal frame parameter required but unused
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False


def main() -> None:
    """Entry point for the Hand-Tracking VST Controller."""
    app = HandTrackingVSTApp()

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGTERM, app.signal_handler)

    try:
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
