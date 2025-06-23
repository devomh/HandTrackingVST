from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class BaseLayout(ABC):
    """Abstract base class for zone layouts."""

    @abstractmethod
    def get_zone_bounds(self) -> List[Tuple[int, int, int, int]]:
        """Return list of zone boundaries."""

    @abstractmethod
    def point_to_zone(self, point: Tuple[int, int]) -> Optional[int]:
        """Convert screen point to zone ID."""

    @abstractmethod
    def get_zone_count(self) -> int:
        """Return total number of zones."""

    @abstractmethod
    def configure(self, config: Dict) -> None:
        """Reconfigure layout parameters."""

    @abstractmethod
    def get_note_for_zone(self, zone_id: int) -> int:
        """Get MIDI note number for zone."""
