from typing import Dict, List
from enum import Enum


class ActivationMode(Enum):
    """Different modes for finger activation of zones."""
    ALL_FINGERS = "all_fingers"
    INDEX_ONLY = "index_only" 
    INDEX_THUMB = "index_thumb"
    EXTENDED_ONLY = "extended_only"


class ZoneMapper:
    """Grid layout and note mapping management."""

    def __init__(self, layout, config: Dict) -> None:
        self.layout = layout
        self.config = config
        self.note_mapping = self._create_note_mapping(config)
        
        # Initialize activation mode
        mode_str = config.get("activation_mode", "index_only")
        try:
            self.activation_mode = ActivationMode(mode_str)
        except ValueError:
            self.activation_mode = ActivationMode.INDEX_ONLY

    def get_active_zones(self, fingertips: Dict, extended_fingers: Dict = None) -> List[int]:
        """Determine active zones from fingertip positions based on activation mode."""
        if not fingertips:
            return []

        active_zones = []

        for hand_key, fingers in fingertips.items():
            for finger_name, position in fingers.items():
                # Filter fingers based on activation mode
                if not self._should_activate_finger(finger_name, hand_key, extended_fingers):
                    continue
                    
                x, y, z = position

                # Convert normalized coordinates (0-1) to grid coordinates
                # Account for margin
                margin = self.config.get("margin", 0.1)

                # Adjust for margin - create active area within the margins
                effective_x = (x - margin) / (1.0 - 2 * margin)
                effective_y = (y - margin) / (1.0 - 2 * margin)

                # Skip if outside the effective zone area
                if (
                    effective_x < 0
                    or effective_x > 1
                    or effective_y < 0
                    or effective_y > 1
                ):
                    continue

                # Map to grid coordinates
                rows = self.layout.rows
                columns = self.layout.columns

                grid_x = int(effective_x * columns)
                grid_y = int(effective_y * rows)

                # Clamp to valid grid bounds
                grid_x = max(0, min(columns - 1, grid_x))
                grid_y = max(0, min(rows - 1, grid_y))

                # Convert grid coordinates to zone ID
                zone_id = self.layout.point_to_zone((grid_x, grid_y))

                if zone_id is not None and zone_id not in active_zones:
                    active_zones.append(zone_id)

        return active_zones

    def map_zone_to_note(self, zone_id: int) -> int:
        """Convert zone ID to MIDI note number."""
        return self.note_mapping.get(zone_id, 60)

    def cycle_activation_mode(self) -> str:
        """Cycle to the next activation mode and return the mode name."""
        modes = list(ActivationMode)
        current_idx = modes.index(self.activation_mode)
        next_idx = (current_idx + 1) % len(modes)
        self.activation_mode = modes[next_idx]
        
        # Update config
        self.config["activation_mode"] = self.activation_mode.value
        
        # Return human-readable mode name
        mode_names = {
            ActivationMode.ALL_FINGERS: "All fingers",
            ActivationMode.INDEX_ONLY: "Index finger only", 
            ActivationMode.INDEX_THUMB: "Index + Thumb",
            ActivationMode.EXTENDED_ONLY: "Extended fingers"
        }
        return mode_names[self.activation_mode]
    
    def get_activation_mode_name(self) -> str:
        """Get human-readable name of current activation mode."""
        mode_names = {
            ActivationMode.ALL_FINGERS: "All fingers",
            ActivationMode.INDEX_ONLY: "Index finger only",
            ActivationMode.INDEX_THUMB: "Index + Thumb", 
            ActivationMode.EXTENDED_ONLY: "Extended fingers"
        }
        return mode_names[self.activation_mode]

    def _should_activate_finger(self, finger_name: str, hand_key: str, extended_fingers: Dict = None) -> bool:
        """Determine if a finger should activate zones based on current mode."""
        if self.activation_mode == ActivationMode.ALL_FINGERS:
            return True
        elif self.activation_mode == ActivationMode.INDEX_ONLY:
            return finger_name == "index"
        elif self.activation_mode == ActivationMode.INDEX_THUMB:
            return finger_name in ["index", "thumb"]
        elif self.activation_mode == ActivationMode.EXTENDED_ONLY:
            # Check if finger is extended (requires extended_fingers data)
            if extended_fingers is None:
                return False
            return extended_fingers.get(hand_key, {}).get(finger_name, False)
        
        return False

    def reconfigure_layout(self, new_config: Dict) -> None:
        """Dynamically reconfigure layout and note mapping."""
        self.config.update(new_config)
        self.layout.configure(self.config)
        self.note_mapping = self._create_note_mapping(self.config)

    def _create_note_mapping(self, config: Dict) -> Dict[int, int]:
        base_note = config.get("base_note", 60)
        interval = config.get("note_interval", 1)
        mapping = {}
        zone_count = self.layout.get_zone_count()
        for zone_id in range(zone_count):
            mapping[zone_id] = base_note + zone_id * interval
        return mapping
