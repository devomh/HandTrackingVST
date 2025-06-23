import pytest
import numpy as np
from unittest.mock import Mock, patch
from hand_tracking_vst.src.core.hand_tracker import HandTracker


@pytest.fixture
def mock_mediapipe():
    with patch("hand_tracking_vst.src.core.hand_tracker.mp") as mock_mp:
        # Mock the MediaPipe solutions
        mock_hands = Mock()
        mock_mp.solutions.hands = mock_hands
        mock_mp.solutions.drawing_utils = Mock()

        # Mock the Hands class
        mock_hands_instance = Mock()
        mock_hands.Hands.return_value = mock_hands_instance

        yield mock_hands_instance


def test_hand_tracker_initialization(mock_mediapipe):
    config = {
        "max_hands": 2,
        "detection_confidence": 0.8,
        "tracking_confidence": 0.6,
        "smoothing": {"alpha": 0.2},
    }

    tracker = HandTracker(config)

    # Check MediaPipe initialization
    assert hasattr(tracker, "hands")
    assert hasattr(tracker, "smoother")
    assert tracker.config == config


def test_process_frame_no_hands(mock_mediapipe):
    tracker = HandTracker({})

    # Mock MediaPipe to return no hands
    mock_mediapipe.process.return_value.multi_hand_landmarks = None

    # Create a dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    result = tracker.process_frame(frame)

    assert result is None


def test_process_frame_with_hands(mock_mediapipe):
    tracker = HandTracker({})

    # Mock MediaPipe landmarks
    mock_landmark = Mock()
    mock_landmark.x = 0.5
    mock_landmark.y = 0.5
    mock_landmark.z = 0.0

    mock_hand_landmarks = Mock()
    mock_hand_landmarks.landmark = [mock_landmark] * 21  # 21 landmarks per hand

    mock_handedness = Mock()
    mock_handedness.classification = [Mock()]
    mock_handedness.classification[0].label = "Left"
    mock_handedness.classification[0].score = 0.9

    # Mock MediaPipe to return hands
    mock_results = Mock()
    mock_results.multi_hand_landmarks = [mock_hand_landmarks]
    mock_results.multi_handedness = [mock_handedness]
    mock_mediapipe.process.return_value = mock_results

    # Create a dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    result = tracker.process_frame(frame)

    assert result is not None
    assert len(result) == 1
    assert "landmarks" in result[0]
    assert "handedness" in result[0]
    assert "confidence" in result[0]
    assert result[0]["handedness"] == "Left"


def test_process_frame_none_input():
    tracker = HandTracker({})

    result = tracker.process_frame(None)

    assert result is None


def test_get_fingertip_positions(mock_mediapipe):
    tracker = HandTracker({})

    # Create mock hand data
    landmarks = np.array([[i * 0.05, i * 0.05, i * 0.01] for i in range(21)])
    hand_data = [{"landmarks": landmarks, "handedness": "Left", "confidence": 0.9}]

    fingertips = tracker.get_fingertip_positions(hand_data)

    assert "left_0" in fingertips
    assert len(fingertips["left_0"]) == 5  # 5 fingertips

    # Check specific fingertips
    assert "thumb" in fingertips["left_0"]
    assert "index" in fingertips["left_0"]
    assert "middle" in fingertips["left_0"]
    assert "ring" in fingertips["left_0"]
    assert "pinky" in fingertips["left_0"]

    # Check coordinates are correct (thumb is landmark 4)
    thumb_pos = fingertips["left_0"]["thumb"]
    expected_thumb = landmarks[4]
    assert thumb_pos[0] == float(expected_thumb[0])
    assert thumb_pos[1] == float(expected_thumb[1])
    assert thumb_pos[2] == float(expected_thumb[2])


def test_get_fingertip_positions_empty():
    tracker = HandTracker({})

    # Test with empty hand data
    fingertips = tracker.get_fingertip_positions([])
    assert fingertips == {}

    # Test with None
    fingertips = tracker.get_fingertip_positions(None)
    assert fingertips == {}


def test_get_fingertip_positions_multiple_hands(mock_mediapipe):
    tracker = HandTracker({})

    # Create mock hand data for two hands
    landmarks1 = np.array([[i * 0.05, i * 0.05, i * 0.01] for i in range(21)])
    landmarks2 = np.array([[i * 0.03, i * 0.03, i * 0.02] for i in range(21)])

    hand_data = [
        {"landmarks": landmarks1, "handedness": "Left", "confidence": 0.9},
        {"landmarks": landmarks2, "handedness": "Right", "confidence": 0.8},
    ]

    fingertips = tracker.get_fingertip_positions(hand_data)

    assert "left_0" in fingertips
    assert "right_1" in fingertips
    assert len(fingertips) == 2


def test_draw_landmarks():
    tracker = HandTracker({})

    # Create a test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Create mock hand data
    landmarks = np.array([[i * 0.05, i * 0.05, i * 0.01] for i in range(21)])
    hand_data = [{"landmarks": landmarks, "handedness": "Left", "confidence": 0.9}]

    # Draw landmarks (should not crash)
    annotated_frame = tracker.draw_landmarks(frame, hand_data)

    assert annotated_frame.shape == frame.shape
    assert annotated_frame.dtype == frame.dtype


def test_draw_landmarks_empty_data():
    tracker = HandTracker({})

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Test with empty hand data
    annotated_frame = tracker.draw_landmarks(frame, [])
    assert np.array_equal(annotated_frame, frame)  # Should return unchanged frame

    # Test with None
    annotated_frame = tracker.draw_landmarks(frame, None)
    assert np.array_equal(annotated_frame, frame)


def test_smoother_integration():
    tracker = HandTracker({"smoothing": {"alpha": 0.5}})

    # Mock the smoother
    tracker.smoother = Mock()
    tracker.smoother.smooth.return_value = np.array([[0.5, 0.5, 0.0]] * 21)

    # Create mock MediaPipe results
    with patch.object(tracker, "hands") as mock_hands:
        mock_landmark = Mock()
        mock_landmark.x = 0.6
        mock_landmark.y = 0.6
        mock_landmark.z = 0.1

        mock_hand_landmarks = Mock()
        mock_hand_landmarks.landmark = [mock_landmark] * 21

        mock_handedness = Mock()
        mock_handedness.classification = [Mock()]
        mock_handedness.classification[0].label = "Left"
        mock_handedness.classification[0].score = 0.9

        mock_results = Mock()
        mock_results.multi_hand_landmarks = [mock_hand_landmarks]
        mock_results.multi_handedness = [mock_handedness]
        mock_hands.process.return_value = mock_results

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = tracker.process_frame(frame)

        # Check that smoother was called
        tracker.smoother.smooth.assert_called_once()

        # Check that smoothed landmarks were used
        assert result is not None
        smoothed_landmarks = result[0]["landmarks"]
        assert np.allclose(smoothed_landmarks[0], [0.5, 0.5, 0.0])


def test_reset_smoother():
    tracker = HandTracker({})
    tracker.smoother = Mock()

    tracker.reset_smoother()

    tracker.smoother.reset.assert_called_once()


def test_cleanup():
    tracker = HandTracker({})
    tracker.hands = Mock()

    tracker.cleanup()

    tracker.hands.close.assert_called_once()


def test_fingertip_indices():
    tracker = HandTracker({})

    # Check that all expected fingertip indices are present
    expected_fingers = ["thumb", "index", "middle", "ring", "pinky"]
    for finger in expected_fingers:
        assert finger in tracker.fingertip_indices

    # Check specific landmark indices (based on MediaPipe hand model)
    assert tracker.fingertip_indices["thumb"] == 4
    assert tracker.fingertip_indices["index"] == 8
    assert tracker.fingertip_indices["middle"] == 12
    assert tracker.fingertip_indices["ring"] == 16
    assert tracker.fingertip_indices["pinky"] == 20


def test_color_conversion():
    tracker = HandTracker({})

    # Test that BGR to RGB conversion is handled
    with patch("hand_tracking_vst.src.core.hand_tracker.cv2.cvtColor") as mock_cvt:
        mock_cvt.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

        # Mock MediaPipe results
        mock_results = Mock()
        mock_results.multi_hand_landmarks = None
        tracker.hands.process = Mock(return_value=mock_results)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        tracker.process_frame(frame)

        # Check that color conversion was called
        mock_cvt.assert_called_once()


def test_landmarks_to_fingertips_edge_cases():
    tracker = HandTracker({})

    # Test with insufficient landmarks
    landmarks = np.array(
        [[i * 0.05, i * 0.05, i * 0.01] for i in range(10)]
    )  # Only 10 landmarks
    hand_data = [{"landmarks": landmarks, "handedness": "Left", "confidence": 0.9}]

    fingertips = tracker.get_fingertip_positions(hand_data)

    # Should only extract fingertips for available landmarks
    assert "left_0" in fingertips
    # Some fingertips might be missing due to insufficient landmarks
