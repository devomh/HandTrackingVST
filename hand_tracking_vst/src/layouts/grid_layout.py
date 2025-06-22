from typing import Dict, List, Optional, Tuple

from .base_layout import BaseLayout

class GridLayout(BaseLayout):
    """Simple rectangular grid layout."""

    def __init__(self, rows: int = 3, columns: int = 4, margin: float = 0.1) -> None:
        self.rows = rows
        self.columns = columns
        self.margin = margin
        self.note_mapping: Dict[int, int] = {}

    def get_zone_bounds(self) -> List[Tuple[int, int, int, int]]:
        bounds = []
        for r in range(self.rows):
            for c in range(self.columns):
                bounds.append((c, r, 1, 1))
        return bounds

    def point_to_zone(self, point: Tuple[int, int]) -> Optional[int]:
        x, y = point
        if 0 <= x < self.columns and 0 <= y < self.rows:
            return y * self.columns + x
        return None

    def get_zone_count(self) -> int:
        return self.rows * self.columns

    def configure(self, config: Dict) -> None:
        self.rows = config.get("rows", self.rows)
        self.columns = config.get("columns", self.columns)
        self.margin = config.get("margin", self.margin)

    def get_note_for_zone(self, zone_id: int) -> int:
        return self.note_mapping.get(zone_id, 60)
