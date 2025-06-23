from hand_tracking_vst.src.core.expression_engine import ExpressionEngine


def test_expression_engine_initialization():
    config = {
        "velocity_scaling": 1.0,
        "pressure_scaling": 1.0,
        "pitch_bend_sensitivity": 2.0,
    }
    engine = ExpressionEngine(config)
    assert engine.velocity_scaling == 1.0
    assert engine.pressure_scaling == 1.0
    assert engine.pitch_bend_sensitivity == 2.0


def test_velocity_calculation():
    engine = ExpressionEngine({})

    # Test zero movement
    velocity = engine.calculate_velocity(0.0, 1.0)
    assert velocity == 64  # Default velocity for no movement

    # Test small movement below threshold
    velocity = engine.calculate_velocity(0.005, 1.0)
    assert velocity == 64  # Should use default for small movements

    # Test normal movement (adjusted for actual velocity scaling)
    velocity = engine.calculate_velocity(0.1, 1.0)
    assert 1 <= velocity <= 127  # Should be valid MIDI velocity

    # Test large movement
    velocity = engine.calculate_velocity(1.0, 1.0)
    assert velocity == 127  # Should cap at max velocity


def test_pressure_calculation():
    engine = ExpressionEngine({})

    # Test at minimum depth (closest to camera)
    pressure = engine.calculate_pressure(-0.2)
    assert pressure == 127  # Maximum pressure

    # Test at maximum depth (furthest from camera)
    pressure = engine.calculate_pressure(0.2)
    assert pressure == 0  # Minimum pressure

    # Test at neutral depth
    pressure = engine.calculate_pressure(0.0)
    assert 0 < pressure < 127  # Should be somewhere in middle


def test_pitch_bend_detection():
    engine = ExpressionEngine({"pitch_bend_threshold": 0.01})
    finger_id = "test_finger"

    # Add trajectory points for rightward swipe
    engine._update_trajectory(finger_id, (0.1, 0.5))
    engine._update_trajectory(finger_id, (0.2, 0.5))
    engine._update_trajectory(finger_id, (0.3, 0.5))
    engine._update_trajectory(finger_id, (0.4, 0.5))

    pitch_bend = engine.detect_pitch_bend(finger_id)
    assert pitch_bend > 0  # Rightward swipe should give positive pitch bend

    # Test leftward swipe
    engine.reset_trajectories()
    engine._update_trajectory(finger_id, (0.4, 0.5))
    engine._update_trajectory(finger_id, (0.3, 0.5))
    engine._update_trajectory(finger_id, (0.2, 0.5))
    engine._update_trajectory(finger_id, (0.1, 0.5))

    pitch_bend = engine.detect_pitch_bend(finger_id)
    assert pitch_bend < 0  # Leftward swipe should give negative pitch bend


def test_vertical_cc_calculation():
    engine = ExpressionEngine({})

    # Test upward movement (negative Y)
    cc_value = engine._calculate_vertical_cc(-0.01)
    assert cc_value < 64  # Should be below center

    # Test downward movement (positive Y)
    cc_value = engine._calculate_vertical_cc(0.01)
    assert cc_value > 64  # Should be above center

    # Test no movement
    cc_value = engine._calculate_vertical_cc(0.0)
    assert cc_value == 64  # Should be at center


def test_expression_extraction():
    engine = ExpressionEngine({})

    current_fingertips = {
        "left_0": {"index": (0.5, 0.5, 0.0), "middle": (0.6, 0.5, -0.05)}
    }

    previous_fingertips = {
        "left_0": {"index": (0.4, 0.5, 0.0), "middle": (0.55, 0.5, -0.03)}
    }

    expression_data = engine.extract_expression(current_fingertips, previous_fingertips)

    assert "left_0" in expression_data
    assert "index" in expression_data["left_0"]
    assert "middle" in expression_data["left_0"]

    index_expr = expression_data["left_0"]["index"]
    assert "velocity" in index_expr
    assert "pressure" in index_expr
    assert "pitch_bend" in index_expr
    assert "vertical_cc" in index_expr


def test_expression_extraction_empty_data():
    engine = ExpressionEngine({})

    # Test with empty current fingertips
    expression_data = engine.extract_expression(
        {}, {"left_0": {"index": (0.5, 0.5, 0.0)}}
    )
    assert expression_data == {}

    # Test with no previous fingertips
    expression_data = engine.extract_expression(
        {"left_0": {"index": (0.5, 0.5, 0.0)}}, None
    )
    assert expression_data == {}


def test_trajectory_management():
    engine = ExpressionEngine({"trajectory_length": 3})
    finger_id = "test_finger"

    # Add more points than trajectory length
    for i in range(5):
        engine._update_trajectory(finger_id, (i * 0.1, 0.5))

    trajectory = engine.hand_trajectories[finger_id]
    assert len(trajectory) == 3  # Should be limited by maxlen

    # Reset trajectories
    engine.reset_trajectories()
    assert len(engine.hand_trajectories) == 0


def test_modulation_calculation():
    engine = ExpressionEngine({})

    # Test with small movement
    modulation = engine._calculate_modulation(0.01)
    assert 0 <= modulation <= 127

    # Test with large movement
    modulation = engine._calculate_modulation(0.5)
    assert modulation == 127  # Should cap at maximum


def test_expression_info():
    config = {
        "velocity_scaling": 1.5,
        "pressure_scaling": 0.8,
        "pitch_bend_sensitivity": 3.0,
        "trajectory_length": 10,
    }
    engine = ExpressionEngine(config)

    info = engine.get_expression_info()
    assert info["velocity_scaling"] == 1.5
    assert info["pressure_scaling"] == 0.8
    assert info["pitch_bend_sensitivity"] == 3.0
    assert info["trajectory_length"] == 10
    assert info["active_trajectories"] == 0


def test_edge_case_values():
    engine = ExpressionEngine({})

    # Test extreme Z-depth values
    pressure = engine.calculate_pressure(-1.0)  # Very close
    assert pressure == 127

    pressure = engine.calculate_pressure(1.0)  # Very far
    assert pressure == 0

    # Test zero time delta
    velocity = engine.calculate_velocity(0.1, 0.0)
    assert velocity == 64  # Should return default

    # Test negative time delta
    velocity = engine.calculate_velocity(0.1, -1.0)
    assert velocity == 64  # Should return default
