import numpy as np
from typing import Dict, Optional, Tuple
from collections import deque


class ExpressionEngine:
    """Extract and process expression parameters."""

    def __init__(self, config: dict) -> None:
        self.config = config

        # Expression scaling factors
        self.velocity_scaling = config.get("velocity_scaling", 1.0)
        self.pressure_scaling = config.get("pressure_scaling", 1.0)
        self.pitch_bend_sensitivity = config.get("pitch_bend_sensitivity", 2.0)
        self.vertical_cc_scaling = config.get("vertical_cc_scaling", 1.0)

        # Trajectory tracking for pitch bend detection
        self.trajectory_length = config.get("trajectory_length", 5)
        self.hand_trajectories: Dict[str, deque] = {}  # hand_key -> deque of positions

        # Pressure calibration (Z-depth ranges)
        self.pressure_min = config.get("pressure_min", -0.1)  # Closer to camera
        self.pressure_max = config.get("pressure_max", 0.1)  # Further from camera

        # Velocity calculation parameters
        self.velocity_threshold = config.get("velocity_threshold", 0.01)
        self.max_velocity = config.get("max_velocity", 0.5)

        # Pitch bend parameters
        self.pitch_bend_threshold = config.get("pitch_bend_threshold", 0.05)
        self.pitch_bend_max = 8191  # MIDI pitch bend range: -8192 to 8191

    def extract_expression(
        self, current_fingertips: Dict, previous_fingertips: Optional[Dict]
    ) -> Dict:
        """Extract expression data from hand movement."""
        if not current_fingertips or not previous_fingertips:
            return {}

        expression_data = {}

        for hand_key, current_fingers in current_fingertips.items():
            if hand_key not in previous_fingertips:
                continue

            previous_fingers = previous_fingertips[hand_key]
            hand_expressions = {}

            for finger_name, current_pos in current_fingers.items():
                if finger_name not in previous_fingers:
                    continue

                previous_pos = previous_fingers[finger_name]

                # Calculate individual finger expressions
                finger_expression = self._calculate_finger_expression(
                    current_pos, previous_pos, f"{hand_key}_{finger_name}"
                )
                hand_expressions[finger_name] = finger_expression

            if hand_expressions:
                expression_data[hand_key] = hand_expressions

        return expression_data

    def _calculate_finger_expression(
        self,
        current_pos: Tuple[float, float, float],
        previous_pos: Tuple[float, float, float],
        finger_id: str,
    ) -> Dict:
        """Calculate expression parameters for a single finger."""
        current_x, current_y, current_z = current_pos
        previous_x, previous_y, previous_z = previous_pos

        # Calculate 2D movement for velocity
        movement_2d = np.array([current_x - previous_x, current_y - previous_y])
        movement_magnitude = np.linalg.norm(movement_2d)

        # Calculate velocity (assume ~30fps, so time_delta ≈ 0.033s)
        time_delta = 1.0 / 30.0  # Approximate frame time
        velocity = self.calculate_velocity(float(movement_magnitude), time_delta)

        # Calculate pressure from Z-depth
        pressure = self.calculate_pressure(current_z)

        # Update trajectory for pitch bend detection
        self._update_trajectory(finger_id, (current_x, current_y))
        pitch_bend = self.detect_pitch_bend(finger_id)

        # Calculate vertical CC from Y movement
        vertical_movement = current_y - previous_y
        vertical_cc = self._calculate_vertical_cc(vertical_movement)

        return {
            "velocity": velocity,
            "pressure": pressure,
            "pitch_bend": pitch_bend,
            "vertical_cc": vertical_cc,
            "modulation": self._calculate_modulation(float(movement_magnitude)),
        }

    def calculate_velocity(self, movement_magnitude: float, time_delta: float) -> int:
        """Convert movement to MIDI velocity (0-127)."""
        if time_delta <= 0:
            return 64  # Default velocity

        # Calculate speed (units per second)
        speed = movement_magnitude / time_delta

        # Apply threshold - small movements don't generate velocity
        if speed < self.velocity_threshold:
            return 64  # Default velocity for slow movements

        # Scale and clamp to MIDI range
        normalized_speed = min(speed / self.max_velocity, 1.0)
        velocity = int(normalized_speed * 127 * self.velocity_scaling)

        return max(1, min(127, velocity))  # Ensure valid MIDI velocity range

    def calculate_pressure(self, z_depth: float) -> int:
        """Convert Z-depth to pressure value (0-127)."""
        # MediaPipe Z is relative depth - negative values are closer to camera
        # Map the depth range to pressure
        if z_depth <= self.pressure_min:
            pressure_normalized = 1.0  # Maximum pressure (closest to camera)
        elif z_depth >= self.pressure_max:
            pressure_normalized = 0.0  # Minimum pressure (furthest from camera)
        else:
            # Linear interpolation between min and max
            pressure_normalized = 1.0 - (
                (z_depth - self.pressure_min) / (self.pressure_max - self.pressure_min)
            )

        # Apply scaling and convert to MIDI range
        pressure = int(pressure_normalized * 127 * self.pressure_scaling)
        return max(0, min(127, pressure))

    def detect_pitch_bend(self, finger_id: str) -> int:
        """Detect swipe gesture for pitch bend (-8192 to 8191)."""
        if finger_id not in self.hand_trajectories:
            return 0

        trajectory = self.hand_trajectories[finger_id]
        if len(trajectory) < 2:
            return 0

        # Calculate horizontal movement trend over trajectory
        positions = list(trajectory)
        x_positions = [pos[0] for pos in positions]

        if len(x_positions) < 2:
            return 0

        # Calculate linear trend (simple slope)
        x_indices = np.arange(len(x_positions))
        slope = np.polyfit(x_indices, x_positions, 1)[0]

        # Convert slope to pitch bend
        # Positive slope = rightward swipe = positive pitch bend
        if abs(slope) < self.pitch_bend_threshold:
            return 0  # No significant horizontal movement

        # Scale slope to pitch bend range
        pitch_bend_normalized = slope * self.pitch_bend_sensitivity
        pitch_bend = int(pitch_bend_normalized * self.pitch_bend_max)

        return max(-8192, min(8191, pitch_bend))

    def _update_trajectory(self, finger_id: str, position: Tuple[float, float]) -> None:
        """Update position trajectory for a finger."""
        if finger_id not in self.hand_trajectories:
            self.hand_trajectories[finger_id] = deque(maxlen=self.trajectory_length)

        self.hand_trajectories[finger_id].append(position)

    def _calculate_vertical_cc(self, vertical_movement: float) -> int:
        """Calculate vertical CC value from Y movement."""
        # Map vertical movement to CC range
        # Positive Y movement (downward) -> higher CC values
        # Negative Y movement (upward) -> lower CC values

        # Scale movement and add to center point (64)
        cc_offset = (
            vertical_movement * 1000 * self.vertical_cc_scaling
        )  # Scale up small movements
        cc_value = int(64 + cc_offset)  # Center around 64

        return max(0, min(127, cc_value))

    def _calculate_modulation(self, movement_magnitude: float) -> int:
        """Calculate modulation value from overall movement."""
        # Use movement magnitude as modulation source
        modulation_normalized = min(
            movement_magnitude * 10, 1.0
        )  # Scale up small movements
        modulation = int(modulation_normalized * 127)

        return max(0, min(127, modulation))

    def reset_trajectories(self) -> None:
        """Reset all trajectory data."""
        self.hand_trajectories.clear()

    def get_expression_info(self) -> Dict:
        """Get current configuration and state info."""
        return {
            "velocity_scaling": self.velocity_scaling,
            "pressure_scaling": self.pressure_scaling,
            "pitch_bend_sensitivity": self.pitch_bend_sensitivity,
            "active_trajectories": len(self.hand_trajectories),
            "trajectory_length": self.trajectory_length,
        }
