from hand_tracking_vst.src.core.zone_mapper import ZoneMapper
from hand_tracking_vst.src.layouts.grid_layout import GridLayout


def test_zone_mapping_chromatic():
    layout = GridLayout(rows=2, columns=2)
    config = {"base_note": 60, "note_interval": 1}
    mapper = ZoneMapper(layout, config)
    assert mapper.map_zone_to_note(0) == 60
    assert mapper.map_zone_to_note(1) == 61
    assert mapper.map_zone_to_note(2) == 62
    assert mapper.map_zone_to_note(3) == 63


def test_zone_mapping_intervals():
    layout = GridLayout(rows=2, columns=2)
    config = {"base_note": 60, "note_interval": 2}
    mapper = ZoneMapper(layout, config)
    assert mapper.map_zone_to_note(0) == 60
    assert mapper.map_zone_to_note(1) == 62
    assert mapper.map_zone_to_note(2) == 64
    assert mapper.map_zone_to_note(3) == 66


def test_active_zones_detection():
    layout = GridLayout(rows=2, columns=2)
    config = {"base_note": 60, "margin": 0.1}
    mapper = ZoneMapper(layout, config)

    # Test fingertips in different zones
    fingertips = {
        "left_0": {
            "index": (0.3, 0.3, 0.0),  # Top-left zone (zone 0)
            "middle": (0.7, 0.3, 0.0),  # Top-right zone (zone 1)
        }
    }

    active_zones = mapper.get_active_zones(fingertips)
    assert 0 in active_zones
    assert 1 in active_zones
    assert len(active_zones) == 2


def test_active_zones_with_margins():
    layout = GridLayout(rows=2, columns=2)
    config = {"base_note": 60, "margin": 0.2}
    mapper = ZoneMapper(layout, config)

    # Test fingertip outside margin area
    fingertips = {
        "left_0": {
            "index": (0.1, 0.1, 0.0),  # In margin area, should be ignored
        }
    }

    active_zones = mapper.get_active_zones(fingertips)
    assert len(active_zones) == 0


def test_active_zones_edge_cases():
    layout = GridLayout(rows=3, columns=3)
    config = {"base_note": 60, "margin": 0.1}
    mapper = ZoneMapper(layout, config)

    # Test coordinates at exact boundaries
    fingertips = {
        "left_0": {
            "index": (0.5, 0.5, 0.0),  # Center zone
            "middle": (0.9, 0.9, 0.0),  # Bottom-right corner
        }
    }

    active_zones = mapper.get_active_zones(fingertips)
    assert len(active_zones) >= 1


def test_reconfigure_layout():
    layout = GridLayout(rows=2, columns=2)
    config = {"base_note": 60, "note_interval": 1}
    mapper = ZoneMapper(layout, config)

    # Initial configuration
    assert mapper.map_zone_to_note(0) == 60

    # Reconfigure
    new_config = {"base_note": 72, "note_interval": 2}
    mapper.reconfigure_layout(new_config)

    # Check new mapping
    assert mapper.map_zone_to_note(0) == 72
    assert mapper.map_zone_to_note(1) == 74


def test_empty_fingertips():
    layout = GridLayout(rows=2, columns=2)
    config = {"base_note": 60, "margin": 0.1}
    mapper = ZoneMapper(layout, config)

    # Test with no fingertips
    active_zones = mapper.get_active_zones({})
    assert len(active_zones) == 0

    # Test with None
    active_zones = mapper.get_active_zones(None)
    assert len(active_zones) == 0


def test_multiple_hands():
    layout = GridLayout(rows=2, columns=3)
    config = {"base_note": 60, "margin": 0.1}
    mapper = ZoneMapper(layout, config)

    # Test with multiple hands
    # For a 2x3 grid: zones are 0,1,2 (top row) and 3,4,5 (bottom row)
    fingertips = {
        "left_0": {
            "index": (0.25, 0.25, 0.0),  # Should map to zone 0 (top-left)
        },
        "right_0": {
            "index": (0.75, 0.75, 0.0),  # Should map to zone 5 (bottom-right)
        },
    }

    active_zones = mapper.get_active_zones(fingertips)
    assert 0 in active_zones
    assert 5 in active_zones  # Bottom-right zone in 2x3 grid


def test_note_mapping_bounds():
    layout = GridLayout(rows=2, columns=2)
    config = {"base_note": 60, "note_interval": 1}
    mapper = ZoneMapper(layout, config)

    # Test valid zone IDs
    assert mapper.map_zone_to_note(0) == 60
    assert mapper.map_zone_to_note(3) == 63

    # Test invalid zone ID (should return default)
    assert mapper.map_zone_to_note(10) == 60
