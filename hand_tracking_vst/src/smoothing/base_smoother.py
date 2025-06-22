from abc import ABC, abstractmethod
import numpy as np

class BaseSmoother(ABC):
    """Abstract base class for smoothing algorithms."""

    @abstractmethod
    def smooth(self, new_value: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply smoothing to new measurement."""

    @abstractmethod
    def reset(self) -> None:
        """Reset smoother state."""
