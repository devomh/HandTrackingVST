import rtmidi
from typing import Dict, Optional, Set
import time


class MidiController:
    """MPE-compatible MIDI output management."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.active_notes: Dict[int, Dict] = {}  # channel -> note info
        self.available_channels: Set[int] = set(range(2, 17))  # MPE channels 2-16
        self.used_channels: Set[int] = set()

        # Initialize MIDI output
        self.midi_out = rtmidi.MidiOut()

        # Create virtual MIDI port
        port_name = config.get("virtual_port_name", "HandTracker")
        self.midi_out.open_virtual_port(port_name)

        # MPE configuration
        self.mpe_enabled = config.get("mpe_enabled", True)

        # MIDI message constants
        self.NOTE_ON = 0x90
        self.NOTE_OFF = 0x80
        self.CC = 0xB0
        self.PITCH_BEND = 0xE0
        self.CHANNEL_PRESSURE = 0xD0

        # CC numbers for expression
        # self.CC_MODULATION = 1
        # self.CC_PRESSURE = 74
        # self.CC_VERTICAL = 11  # Expression controller

        # For manual CC mapping
        self.CC_MODULATION = 20
        self.CC_PRESSURE = 21
        self.CC_VERTICAL = 22  # Expression controller
        # Note: The Z-axis (depth) seems to not be working


        print(f"MIDI virtual port '{port_name}' created successfully")

    def trigger_note(self, note: int, velocity: int, expression: dict) -> Optional[int]:
        """Trigger note with expression on a dedicated channel."""
        if not self.available_channels:
            print("Warning: No available MIDI channels for new note")
            return None

        # Allocate channel
        channel = self.available_channels.pop()
        self.used_channels.add(channel)

        # Clamp values to MIDI range
        note = max(0, min(127, note))
        velocity = max(1, min(127, velocity))  # Note velocity should be 1-127

        # Send note on
        note_on_msg = [self.NOTE_ON | (channel - 1), note, velocity]
        self.midi_out.send_message(note_on_msg)

        # Store note info
        self.active_notes[channel] = {
            "note": note,
            "velocity": velocity,
            "start_time": time.time(),
        }

        # Send initial expression data
        if expression:
            self.update_expression(channel, expression)

        return channel

    def update_expression(self, channel: int, expression: dict) -> None:
        """Update real-time expression parameters."""
        if channel not in self.active_notes:
            return

        midi_channel = channel - 1  # Convert to 0-based MIDI channel

        # Pressure (aftertouch or CC74)
        if "pressure" in expression:
            pressure = max(0, min(127, int(expression["pressure"])))
            if self.mpe_enabled:
                # Use channel pressure for MPE
                pressure_msg = [self.CHANNEL_PRESSURE | midi_channel, pressure]
                self.midi_out.send_message(pressure_msg)
            else:
                # Use CC74 for non-MPE
                cc_msg = [self.CC | midi_channel, self.CC_PRESSURE, pressure]
                self.midi_out.send_message(cc_msg)

        # Pitch bend
        if "pitch_bend" in expression:
            pitch_bend_value = expression["pitch_bend"]
            # Convert from -8192 to 8191 range to 0-16383 MIDI range
            midi_pitch_bend = max(0, min(16383, pitch_bend_value + 8192))

            # MIDI pitch bend is 14-bit: LSB, MSB
            lsb = midi_pitch_bend & 0x7F
            msb = (midi_pitch_bend >> 7) & 0x7F

            pitch_bend_msg = [self.PITCH_BEND | midi_channel, lsb, msb]
            self.midi_out.send_message(pitch_bend_msg)

        # Modulation (CC1)
        if "modulation" in expression:
            modulation = max(0, min(127, int(expression["modulation"])))
            mod_msg = [self.CC | midi_channel, self.CC_MODULATION, modulation]
            self.midi_out.send_message(mod_msg)

        # Vertical CC (expression controller)
        if "vertical_cc" in expression:
            vertical_cc = max(0, min(127, int(expression["vertical_cc"])))
            cc_msg = [self.CC | midi_channel, self.CC_VERTICAL, vertical_cc]
            self.midi_out.send_message(cc_msg)

    def release_note(self, channel: int) -> None:
        """Release note and free channel."""
        if channel not in self.active_notes:
            return

        note_info = self.active_notes[channel]
        note = note_info["note"]

        # Send note off
        midi_channel = channel - 1
        note_off_msg = [self.NOTE_OFF | midi_channel, note, 0]
        self.midi_out.send_message(note_off_msg)

        # Free the channel
        del self.active_notes[channel]
        self.used_channels.discard(channel)
        self.available_channels.add(channel)

    def release_all_notes(self) -> None:
        """Release all active notes."""
        channels_to_release = list(self.active_notes.keys())
        for channel in channels_to_release:
            self.release_note(channel)

    def send_all_notes_off(self) -> None:
        """Send all notes off CC message to all channels."""
        for channel in range(1, 17):
            midi_channel = channel - 1
            all_notes_off_msg = [
                self.CC | midi_channel,
                123,
                0,
            ]  # CC123 = All Notes Off
            self.midi_out.send_message(all_notes_off_msg)

    def get_active_note_count(self) -> int:
        """Get the number of currently active notes."""
        return len(self.active_notes)

    def get_available_channel_count(self) -> int:
        """Get the number of available channels."""
        return len(self.available_channels)

    def is_channel_active(self, channel: int) -> bool:
        """Check if a channel has an active note."""
        return channel in self.active_notes

    def get_note_info(self, channel: int) -> Optional[Dict]:
        """Get information about the note on a specific channel."""
        return self.active_notes.get(channel)

    def cleanup(self) -> None:
        """Clean up MIDI resources."""
        try:
            # Release all notes before closing
            self.release_all_notes()
            self.send_all_notes_off()

            # Close MIDI port
            if hasattr(self, "midi_out") and self.midi_out:
                self.midi_out.close_port()
                print("MIDI port closed successfully")
        except Exception as e:
            print(f"Error during MIDI cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
