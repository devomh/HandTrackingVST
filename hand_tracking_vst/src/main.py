from .config.config_manager import ConfigManager
from .core.hand_tracker import HandTracker
from .core.zone_mapper import ZoneMapper
from .core.midi_controller import MidiController
from .core.expression_engine import ExpressionEngine
from .core.event_manager import EventManager
from .layouts.grid_layout import GridLayout


def main() -> None:
    config = ConfigManager().config
    layout = GridLayout(
        rows=config.get("layout", {}).get("rows", 3),
        columns=config.get("layout", {}).get("columns", 4),
    )
    tracker = HandTracker(config.get("hand_tracking", {}))
    mapper = ZoneMapper(layout, config.get("layout", {}))
    midi = MidiController(config.get("midi", {}))
    expression = ExpressionEngine(config.get("expression", {}))
    manager = EventManager(tracker, mapper, midi, expression)
    # Placeholder main loop
    print("Hand-Tracking VST Controller initialized")


if __name__ == "__main__":
    main()
