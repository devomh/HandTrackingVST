from typing import Dict, List


class EventManager:
    """Coordinate frame processing and MIDI events."""

    def __init__(self, tracker, zone_mapper, midi_controller, expression_engine):
        self.tracker = tracker
        self.zone_mapper = zone_mapper
        self.midi_controller = midi_controller
        self.expression_engine = expression_engine
        self.previous_fingertips = None
        self.active_zone_channels: Dict[int, int] = {}  # zone_id -> channel
        self.zone_last_seen: Dict[int, float] = {}  # zone_id -> timestamp

        # Configuration for note management
        self.note_release_delay = 0.1  # Seconds to wait before releasing note

    def process(self, frame) -> None:
        """Process a single video frame."""
        # Get hand landmarks from tracker
        hand_data = self.tracker.process_frame(frame)
        if not hand_data:
            # No hands detected - release all notes after delay
            self._handle_no_hands()
            return

        # Extract fingertip positions and extension data
        current_fingertips = self.tracker.get_fingertip_positions(hand_data)
        extended_fingers = self.tracker.get_extended_fingers(hand_data)

        # Get active zones from fingertip positions
        active_zones = self.zone_mapper.get_active_zones(current_fingertips, extended_fingers)

        # Extract expression data if we have previous frame
        expression_data = {}
        if self.previous_fingertips is not None:
            expression_data = self.expression_engine.extract_expression(
                current_fingertips, self.previous_fingertips
            )

        # Process active zones
        self._process_active_zones(active_zones, expression_data)

        # Update previous frame data
        self.previous_fingertips = current_fingertips

    def _process_active_zones(
        self, active_zones: List[int], expression_data: Dict
    ) -> None:
        """Process currently active zones and manage note triggering."""
        import time

        current_time = time.time()

        # Update last seen time for active zones
        for zone_id in active_zones:
            self.zone_last_seen[zone_id] = current_time

            # If zone is not already playing, trigger new note
            if zone_id not in self.active_zone_channels:
                note = self.zone_mapper.map_zone_to_note(zone_id)

                # Get expression for this zone (use average of all finger expressions)
                zone_expression = self._get_zone_expression(expression_data)
                velocity = zone_expression.get("velocity", 64)

                # Trigger note
                channel = self.midi_controller.trigger_note(
                    note, velocity, zone_expression
                )
                if channel is not None:
                    self.active_zone_channels[zone_id] = channel
            else:
                # Zone is already active - update expression
                channel = self.active_zone_channels[zone_id]
                zone_expression = self._get_zone_expression(expression_data)
                self.midi_controller.update_expression(channel, zone_expression)

        # Check for zones that should be released
        zones_to_release = []
        for zone_id, last_seen in self.zone_last_seen.items():
            if current_time - last_seen > self.note_release_delay:
                zones_to_release.append(zone_id)

        for zone_id in zones_to_release:
            self._release_zone(zone_id)

    def _get_zone_expression(self, expression_data: Dict) -> Dict:
        """Extract average expression parameters from all finger data."""
        if not expression_data:
            return {"pressure": 64, "velocity": 64, "pitch_bend": 0, "vertical_cc": 64}

        # Collect all expression values
        pressures = []
        velocities = []
        pitch_bends = []
        vertical_ccs = []
        modulations = []

        for hand_expressions in expression_data.values():
            for finger_expression in hand_expressions.values():
                pressures.append(finger_expression.get("pressure", 64))
                velocities.append(finger_expression.get("velocity", 64))
                pitch_bends.append(finger_expression.get("pitch_bend", 0))
                vertical_ccs.append(finger_expression.get("vertical_cc", 64))
                modulations.append(finger_expression.get("modulation", 0))

        # Calculate averages
        avg_expression = {
            "pressure": int(sum(pressures) / len(pressures)) if pressures else 64,
            "velocity": int(sum(velocities) / len(velocities)) if velocities else 64,
            "pitch_bend": (
                int(sum(pitch_bends) / len(pitch_bends)) if pitch_bends else 0
            ),
            "vertical_cc": (
                int(sum(vertical_ccs) / len(vertical_ccs)) if vertical_ccs else 64
            ),
            "modulation": (
                int(sum(modulations) / len(modulations)) if modulations else 0
            ),
        }

        return avg_expression

    def _release_zone(self, zone_id: int) -> None:
        """Release a zone and its associated MIDI note."""
        if zone_id in self.active_zone_channels:
            channel = self.active_zone_channels[zone_id]
            self.midi_controller.release_note(channel)
            del self.active_zone_channels[zone_id]

        if zone_id in self.zone_last_seen:
            del self.zone_last_seen[zone_id]

    def _handle_no_hands(self) -> None:
        """Handle the case when no hands are detected."""
        import time

        current_time = time.time()

        # Mark all zones as not seen
        zones_to_release = []
        for zone_id, last_seen in self.zone_last_seen.items():
            if current_time - last_seen > self.note_release_delay:
                zones_to_release.append(zone_id)

        for zone_id in zones_to_release:
            self._release_zone(zone_id)

    def release_all_notes(self) -> None:
        """Release all currently active notes."""
        zones_to_release = list(self.active_zone_channels.keys())
        for zone_id in zones_to_release:
            self._release_zone(zone_id)

        self.midi_controller.release_all_notes()

    def get_active_zone_count(self) -> int:
        """Get the number of currently active zones."""
        return len(self.active_zone_channels)

    def cleanup(self) -> None:
        """Clean up resources."""
        self.release_all_notes()
