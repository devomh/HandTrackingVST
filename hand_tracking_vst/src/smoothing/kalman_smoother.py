from .base_smoother import BaseSmoother
import numpy as np


class KalmanSmoother(BaseSmoother):
    """Placeholder for future Kalman filter implementation."""

    def __init__(self) -> None:
        pass

    def smooth(self, new_value: np.ndarray, timestamp: float) -> np.ndarray:
        raise NotImplementedError

    def reset(self) -> None:
        pass
