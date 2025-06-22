class HandTracker:
    """MediaPipe-based hand detection and landmark extraction."""

    def __init__(self, config: dict) -> None:
        self.config = config
        # Placeholder for MediaPipe initialization

    def process_frame(self, frame):
        """Process video frame and return hand landmarks."""
        raise NotImplementedError

    def get_fingertip_positions(self, landmarks):
        """Extract fingertip positions with depth data."""
        raise NotImplementedError
