import numpy as np
from .base_smoother import BaseSmoother

class EmaSmoother(BaseSmoother):
    """Exponential moving average smoother."""

    def __init__(self, alpha: float = 0.3) -> None:
        self.alpha = alpha
        self.value = None

    def smooth(self, new_value: np.ndarray, timestamp: float) -> np.ndarray:
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

    def reset(self) -> None:
        self.value = None
