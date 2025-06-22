from typing import Dict, List

class ZoneMapper:
    """Grid layout and note mapping management."""

    def __init__(self, layout, config: Dict) -> None:
        self.layout = layout
        self.config = config
        self.note_mapping = self._create_note_mapping(config)

    def get_active_zones(self, fingertips) -> List[int]:
        """Determine active zones from fingertip positions."""
        raise NotImplementedError

    def map_zone_to_note(self, zone_id: int) -> int:
        """Convert zone ID to MIDI note number."""
        return self.note_mapping.get(zone_id, 60)

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
