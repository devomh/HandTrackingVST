import cv2
import mediapipe as mp
import numpy as np
from typing import List, Dict, Optional, Tuple
from ..smoothing.ema_smoother import EmaSmoother


class HandTracker:
    """MediaPipe-based hand detection and landmark extraction."""

    def __init__(self, config: dict) -> None:
        self.config = config

        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.get("max_hands", 2),
            min_detection_confidence=config.get("detection_confidence", 0.7),
            min_tracking_confidence=config.get("tracking_confidence", 0.5),
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Initialize smoothing - use per-hand smoothers to avoid cross-contamination
        smoothing_config = config.get("smoothing", {})
        self.smoothing_alpha = smoothing_config.get("alpha", 0.3)
        self.hand_smoothers: Dict[str, EmaSmoother] = {}  # hand_id -> smoother

        # Fingertip landmark indices (MediaPipe hand landmarks)
        self.fingertip_indices = {
            "thumb": 4,
            "index": 8,
            "middle": 12,
            "ring": 16,
            "pinky": 20,
        }
        
        # Joint landmark indices for extension detection
        self.joint_indices = {
            "thumb": [2, 3, 4],    # thumb: mcp, ip, tip
            "index": [5, 6, 7, 8], # index: mcp, pip, dip, tip
            "middle": [9, 10, 11, 12], # middle: mcp, pip, dip, tip
            "ring": [13, 14, 15, 16],  # ring: mcp, pip, dip, tip
            "pinky": [17, 18, 19, 20], # pinky: mcp, pip, dip, tip
        }

    def process_frame(self, frame: np.ndarray) -> Optional[List[Dict]]:
        """Process video frame and return hand landmarks."""
        if frame is None:
            return None

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process frame with MediaPipe
        results = self.hands.process(rgb_frame)

        if not results.multi_hand_landmarks:
            return None

        hand_data = []
        detected_hand_ids = set()
        
        for i, (hand_landmarks, handedness) in enumerate(zip(
            results.multi_hand_landmarks, results.multi_handedness
        )):
            # Create consistent hand ID based on handedness
            hand_label = handedness.classification[0].label
            hand_id = f"{hand_label.lower()}"
            detected_hand_ids.add(hand_id)
            
            # Convert landmarks to numpy array
            landmarks_array = np.array(
                [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]
            )

            # Get or create smoother for this specific hand
            if hand_id not in self.hand_smoothers:
                self.hand_smoothers[hand_id] = EmaSmoother(alpha=self.smoothing_alpha)
            
            # Apply per-hand smoothing
            smoothed_landmarks = self.hand_smoothers[hand_id].smooth(
                landmarks_array, 0.0
            )  # timestamp not used in EMA

            hand_info = {
                "landmarks": smoothed_landmarks,
                "handedness": hand_label,
                "confidence": handedness.classification[0].score,
                "hand_id": hand_id,
            }
            hand_data.append(hand_info)
        
        # Clean up smoothers for hands that are no longer detected
        self._cleanup_unused_smoothers(detected_hand_ids)

        return hand_data

    def get_fingertip_positions(
        self, hand_data: List[Dict]
    ) -> Dict[str, Dict[str, Tuple[float, float, float]]]:
        """Extract fingertip positions with depth data."""
        if not hand_data:
            return {}

        fingertip_positions: Dict[str, Dict[str, Tuple[float, float, float]]] = {}

        for i, hand_info in enumerate(hand_data):
            landmarks = hand_info["landmarks"]
            hand_id = hand_info.get("hand_id", f"{hand_info['handedness'].lower()}_{i}")

            fingertip_positions[hand_id] = {}

            for finger_name, landmark_idx in self.fingertip_indices.items():
                if landmark_idx < len(landmarks):
                    x, y, z = landmarks[landmark_idx]
                    fingertip_positions[hand_id][finger_name] = (
                        float(x),
                        float(y),
                        float(z),
                    )

        return fingertip_positions

    def get_extended_fingers(
        self, hand_data: List[Dict]
    ) -> Dict[str, Dict[str, bool]]:
        """Detect which fingers are extended/pointing."""
        if not hand_data:
            return {}

        extended_fingers: Dict[str, Dict[str, bool]] = {}
        
        for i, hand_info in enumerate(hand_data):
            landmarks = hand_info["landmarks"]
            hand_id = hand_info.get("hand_id", f"{hand_info['handedness'].lower()}_{i}")
            
            extended_fingers[hand_id] = {}
            
            for finger_name, joint_indices in self.joint_indices.items():
                is_extended = self._is_finger_extended(landmarks, finger_name, joint_indices)
                extended_fingers[hand_id][finger_name] = is_extended
                
        return extended_fingers
    
    def _is_finger_extended(self, landmarks: np.ndarray, finger_name: str, joint_indices: List[int]) -> bool:
        """Check if a specific finger is extended based on joint angles."""
        if len(joint_indices) < 3:
            return False
            
        try:
            # Special case for thumb (different anatomy)
            if finger_name == "thumb":
                # For thumb: check if tip is farther from wrist than joints
                wrist = landmarks[0]  # Wrist landmark
                tip = landmarks[joint_indices[-1]]
                joint = landmarks[joint_indices[1]]  # IP joint
                
                # Calculate distances from wrist
                tip_dist = np.linalg.norm(tip[:2] - wrist[:2])
                joint_dist = np.linalg.norm(joint[:2] - wrist[:2])
                
                return tip_dist > joint_dist * 1.1  # 10% margin
            else:
                # For other fingers: check if finger is pointing outward
                # Compare consecutive joint positions
                mcp = landmarks[joint_indices[0]]  # Metacarpophalangeal joint
                pip = landmarks[joint_indices[1]]  # Proximal interphalangeal joint
                tip = landmarks[joint_indices[-1]]  # Fingertip
                
                # Calculate vectors
                vec1 = pip[:2] - mcp[:2]  # base to middle joint
                vec2 = tip[:2] - pip[:2]  # middle joint to tip
                
                # Calculate dot product to check alignment
                dot_product = np.dot(vec1, vec2)
                magnitude1 = np.linalg.norm(vec1)
                magnitude2 = np.linalg.norm(vec2)
                
                if magnitude1 == 0 or magnitude2 == 0:
                    return False
                
                # Cosine of angle between vectors
                cos_angle = dot_product / (magnitude1 * magnitude2)
                
                # Extended if angle is less than 45 degrees (cos > 0.7)
                return cos_angle > 0.7
                
        except (IndexError, ValueError):
            return False

    def _cleanup_unused_smoothers(self, detected_hand_ids: set) -> None:
        """Remove smoothers for hands that are no longer detected."""
        hands_to_remove = []
        for hand_id in self.hand_smoothers.keys():
            if hand_id not in detected_hand_ids:
                hands_to_remove.append(hand_id)
        
        for hand_id in hands_to_remove:
            del self.hand_smoothers[hand_id]

    def draw_landmarks(self, frame: np.ndarray, hand_data: List[Dict]) -> np.ndarray:
        """Draw hand landmarks on frame for debugging/visualization."""
        if not hand_data:
            return frame

        annotated_frame = frame.copy()

        for hand_info in hand_data:
            landmarks = hand_info["landmarks"]

            # Convert normalized coordinates back to pixel coordinates
            h, w, _ = frame.shape
            landmark_list = []
            for landmark in landmarks:
                x_px = int(landmark[0] * w)
                y_px = int(landmark[1] * h)
                landmark_list.append([x_px, y_px])

            # Draw landmarks (simplified version)
            for x, y in landmark_list:
                cv2.circle(annotated_frame, (x, y), 3, (0, 255, 0), -1)

            # Highlight fingertips
            for finger_name, idx in self.fingertip_indices.items():
                if idx < len(landmark_list):
                    x, y = landmark_list[idx]
                    cv2.circle(annotated_frame, (x, y), 5, (255, 0, 0), -1)
                    cv2.putText(
                        annotated_frame,
                        finger_name[:1].upper(),
                        (x - 10, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )

        return annotated_frame

    def reset_smoother(self) -> None:
        """Reset all smoother states."""
        for smoother in self.hand_smoothers.values():
            smoother.reset()

    def cleanup(self) -> None:
        """Clean up MediaPipe resources."""
        if hasattr(self, "hands"):
            self.hands.close()
