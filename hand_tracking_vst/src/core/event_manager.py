class EventManager:
    """Coordinate frame processing and MIDI events."""

    def __init__(self, tracker, zone_mapper, midi_controller, expression_engine):
        self.tracker = tracker
        self.zone_mapper = zone_mapper
        self.midi_controller = midi_controller
        self.expression_engine = expression_engine
        self.previous_frame = None

    def process(self, frame) -> None:
        """Process a single video frame."""
        landmarks = self.tracker.process_frame(frame)
        if self.previous_frame is not None:
            expression = self.expression_engine.extract_expression(
                landmarks, self.previous_frame
            )
            zones = self.zone_mapper.get_active_zones(landmarks)
            for zone_id in zones:
                note = self.zone_mapper.map_zone_to_note(zone_id)
                self.midi_controller.trigger_note(note, 100, expression)
        self.previous_frame = landmarks
