import pytest
from unittest.mock import Mock, patch
from hand_tracking_vst.src.core.midi_controller import MidiController


@pytest.fixture
def mock_midi_out():
    with patch("hand_tracking_vst.src.core.midi_controller.rtmidi.MidiOut") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


def test_midi_controller_initialization(mock_midi_out):
    config = {"virtual_port_name": "TestPort", "mpe_enabled": True}

    controller = MidiController(config)

    # Check that MIDI port was opened
    mock_midi_out.open_virtual_port.assert_called_once_with("TestPort")

    # Check initial state
    assert len(controller.available_channels) == 15  # Channels 2-16
    assert len(controller.used_channels) == 0
    assert len(controller.active_notes) == 0


def test_trigger_note(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Trigger a note
    expression = {"pressure": 100, "pitch_bend": 1000}
    channel = controller.trigger_note(60, 100, expression)

    # Check that a channel was allocated
    assert channel is not None
    assert 2 <= channel <= 16  # MPE channels
    assert channel in controller.active_notes
    assert channel in controller.used_channels
    assert channel not in controller.available_channels

    # Check that MIDI messages were sent
    assert mock_midi_out.send_message.called


def test_trigger_note_no_channels(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Use up all channels
    controller.available_channels = set()

    # Try to trigger a note
    channel = controller.trigger_note(60, 100, {})

    # Should return None when no channels available
    assert channel is None


def test_update_expression(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # First trigger a note to get a channel
    channel = controller.trigger_note(60, 100, {})
    mock_midi_out.send_message.reset_mock()

    # Update expression
    expression = {
        "pressure": 80,
        "pitch_bend": 2000,
        "modulation": 50,
        "vertical_cc": 90,
    }
    controller.update_expression(channel, expression)

    # Check that expression messages were sent
    assert mock_midi_out.send_message.call_count >= 1


def test_release_note(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Trigger a note
    channel = controller.trigger_note(60, 100, {})
    initial_active_count = len(controller.active_notes)

    # Release the note
    controller.release_note(channel)

    # Check that note was released
    assert channel not in controller.active_notes
    assert channel not in controller.used_channels
    assert channel in controller.available_channels
    assert len(controller.active_notes) == initial_active_count - 1


def test_release_all_notes(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Trigger multiple notes
    channels = []
    for i in range(3):
        channel = controller.trigger_note(60 + i, 100, {})
        channels.append(channel)

    # Release all notes
    controller.release_all_notes()

    # Check that all notes were released
    assert len(controller.active_notes) == 0
    assert len(controller.used_channels) == 0
    assert len(controller.available_channels) == 15


def test_mpe_vs_non_mpe_pressure(mock_midi_out):
    # Test MPE mode
    controller_mpe = MidiController({"mpe_enabled": True})
    channel = controller_mpe.trigger_note(60, 100, {})
    mock_midi_out.send_message.reset_mock()

    controller_mpe.update_expression(channel, {"pressure": 80})

    # In MPE mode, should use channel pressure
    calls = mock_midi_out.send_message.call_args_list
    pressure_call = None
    for call in calls:
        msg = call[0][0]
        if (msg[0] & 0xF0) == 0xD0:  # Channel pressure message
            pressure_call = msg
            break

    assert pressure_call is not None

    # Test non-MPE mode
    controller_non_mpe = MidiController({"mpe_enabled": False})
    channel = controller_non_mpe.trigger_note(60, 100, {})
    mock_midi_out.send_message.reset_mock()

    controller_non_mpe.update_expression(channel, {"pressure": 80})

    # In non-MPE mode, should use CC74
    calls = mock_midi_out.send_message.call_args_list
    cc_call = None
    for call in calls:
        msg = call[0][0]
        if (msg[0] & 0xF0) == 0xB0 and len(msg) >= 3 and msg[1] == 74:  # CC74
            cc_call = msg
            break

    assert cc_call is not None


def test_pitch_bend_conversion(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})
    channel = controller.trigger_note(60, 100, {})
    mock_midi_out.send_message.reset_mock()

    # Test pitch bend at center (0)
    controller.update_expression(channel, {"pitch_bend": 0})

    # Test positive pitch bend
    controller.update_expression(channel, {"pitch_bend": 4000})

    # Test negative pitch bend
    controller.update_expression(channel, {"pitch_bend": -4000})

    # Check that pitch bend messages were sent
    pitch_bend_calls = []
    for call in mock_midi_out.send_message.call_args_list:
        msg = call[0][0]
        if (msg[0] & 0xF0) == 0xE0:  # Pitch bend message
            pitch_bend_calls.append(msg)

    assert len(pitch_bend_calls) >= 1


def test_note_info_tracking(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Trigger a note
    channel = controller.trigger_note(60, 100, {})

    # Check note info
    note_info = controller.get_note_info(channel)
    assert note_info is not None
    assert note_info["note"] == 60
    assert note_info["velocity"] == 100
    assert "start_time" in note_info

    # Check active note count
    assert controller.get_active_note_count() == 1
    assert controller.get_available_channel_count() == 14


def test_invalid_channel_operations(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Try to update expression on non-existent channel
    controller.update_expression(99, {"pressure": 80})  # Should not crash

    # Try to release non-existent channel
    controller.release_note(99)  # Should not crash

    # Try to get info for non-existent channel
    info = controller.get_note_info(99)
    assert info is None


def test_midi_value_clamping(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Test note value clamping
    channel1 = controller.trigger_note(-10, 150, {})  # Negative note, high velocity
    channel2 = controller.trigger_note(200, 0, {})  # High note, zero velocity

    # Both should succeed (values should be clamped)
    assert channel1 is not None
    assert channel2 is not None


def test_cleanup(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Trigger some notes
    for i in range(3):
        controller.trigger_note(60 + i, 100, {})

    # Cleanup
    controller.cleanup()

    # Check that all notes were released and port was closed
    assert len(controller.active_notes) == 0
    mock_midi_out.close_port.assert_called_once()


def test_all_notes_off(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Send all notes off
    controller.send_all_notes_off()

    # Check that CC123 (All Notes Off) was sent to all channels
    all_notes_off_calls = []
    for call in mock_midi_out.send_message.call_args_list:
        msg = call[0][0]
        if (msg[0] & 0xF0) == 0xB0 and len(msg) >= 3 and msg[1] == 123:  # CC123
            all_notes_off_calls.append(msg)

    assert len(all_notes_off_calls) == 16  # All 16 MIDI channels


def test_channel_state_methods(mock_midi_out):
    controller = MidiController({"mpe_enabled": True})

    # Initially no active channels
    assert not controller.is_channel_active(2)

    # Trigger a note
    channel = controller.trigger_note(60, 100, {})

    # Check channel is now active
    assert controller.is_channel_active(channel)
    assert not controller.is_channel_active(99)  # Non-existent channel

    # Release note
    controller.release_note(channel)

    # Check channel is no longer active
    assert not controller.is_channel_active(channel)
