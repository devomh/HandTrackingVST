class ExpressionEngine:
    """Extract and process expression parameters."""

    def __init__(self, config: dict) -> None:
        self.config = config

    def extract_expression(self, current_frame, previous_frame):
        """Extract expression data from hand movement."""
        raise NotImplementedError

    def calculate_velocity(self, movement, time_delta: float) -> int:
        """Convert movement to MIDI velocity (0-127)."""
        raise NotImplementedError

    def calculate_pressure(self, z_depth: float) -> int:
        """Convert Z-depth to pressure value (0-127)."""
        raise NotImplementedError

    def detect_pitch_bend(self, trajectory) -> int:
        """Detect swipe gesture for pitch bend (-8192 to 8191)."""
        raise NotImplementedError
