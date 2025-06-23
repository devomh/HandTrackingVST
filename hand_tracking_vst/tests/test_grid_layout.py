from hand_tracking_vst.src.layouts.grid_layout import GridLayout


def test_grid_layout_initialization():
    layout = GridLayout(rows=3, columns=4, margin=0.1)

    assert layout.rows == 3
    assert layout.columns == 4
    assert layout.margin == 0.1
    assert isinstance(layout.note_mapping, dict)


def test_grid_layout_defaults():
    layout = GridLayout()

    assert layout.rows == 3
    assert layout.columns == 4
    assert layout.margin == 0.1


def test_get_zone_count():
    layout = GridLayout(rows=2, columns=3)

    assert layout.get_zone_count() == 6  # 2 * 3


def test_point_to_zone():
    layout = GridLayout(rows=2, columns=2)

    # Test corner points
    assert layout.point_to_zone((0, 0)) == 0  # Top-left
    assert layout.point_to_zone((1, 0)) == 1  # Top-right
    assert layout.point_to_zone((0, 1)) == 2  # Bottom-left
    assert layout.point_to_zone((1, 1)) == 3  # Bottom-right

    # Test out of bounds
    assert layout.point_to_zone((-1, 0)) is None
    assert layout.point_to_zone((2, 0)) is None
    assert layout.point_to_zone((0, -1)) is None
    assert layout.point_to_zone((0, 2)) is None


def test_point_to_zone_larger_grid():
    layout = GridLayout(rows=3, columns=4)

    # Test various points in 3x4 grid
    assert layout.point_to_zone((0, 0)) == 0  # (0,0) -> zone 0
    assert layout.point_to_zone((3, 0)) == 3  # (3,0) -> zone 3
    assert layout.point_to_zone((0, 1)) == 4  # (0,1) -> zone 4
    assert layout.point_to_zone((3, 2)) == 11  # (3,2) -> zone 11

    # Test boundary cases
    assert layout.point_to_zone((4, 0)) is None  # Column 4 doesn't exist
    assert layout.point_to_zone((0, 3)) is None  # Row 3 doesn't exist


def test_get_zone_bounds():
    layout = GridLayout(rows=2, columns=2)

    bounds = layout.get_zone_bounds()

    assert len(bounds) == 4  # 2 * 2 zones

    # Each bound should be (x, y, width, height)
    for bound in bounds:
        assert len(bound) == 4
        assert bound[2] == 1  # width = 1
        assert bound[3] == 1  # height = 1


def test_configure():
    layout = GridLayout(rows=2, columns=2)

    # Initial configuration
    assert layout.rows == 2
    assert layout.columns == 2

    # Reconfigure
    new_config = {"rows": 3, "columns": 5, "margin": 0.2}
    layout.configure(new_config)

    # Check updated configuration
    assert layout.rows == 3
    assert layout.columns == 5
    assert layout.margin == 0.2


def test_configure_partial():
    layout = GridLayout(rows=2, columns=2, margin=0.1)

    # Configure with only some parameters
    partial_config = {"rows": 4}
    layout.configure(partial_config)

    # Should update only specified parameters
    assert layout.rows == 4
    assert layout.columns == 2  # Unchanged
    assert layout.margin == 0.1  # Unchanged


def test_get_note_for_zone():
    layout = GridLayout()

    # Test with empty note mapping
    note = layout.get_note_for_zone(0)
    assert note == 60  # Default value

    # Test with populated note mapping
    layout.note_mapping = {0: 72, 1: 74, 2: 76}
    assert layout.get_note_for_zone(0) == 72
    assert layout.get_note_for_zone(1) == 74
    assert layout.get_note_for_zone(5) == 60  # Non-existent zone returns default


def test_zone_calculation_consistency():
    layout = GridLayout(rows=3, columns=4)

    # Test that point_to_zone and zone counting are consistent
    total_zones = layout.get_zone_count()
    valid_zones = set()

    for row in range(layout.rows):
        for col in range(layout.columns):
            zone = layout.point_to_zone((col, row))
            if zone is not None:
                valid_zones.add(zone)

    assert len(valid_zones) == total_zones
    assert min(valid_zones) == 0
    assert max(valid_zones) == total_zones - 1


def test_zone_bounds_consistency():
    layout = GridLayout(rows=2, columns=3)

    bounds = layout.get_zone_bounds()
    zone_count = layout.get_zone_count()

    # Number of bounds should match zone count
    assert len(bounds) == zone_count

    # Each zone should have unique bounds
    bound_set = set(bounds)
    assert len(bound_set) == len(bounds)


def test_edge_coordinates():
    layout = GridLayout(rows=2, columns=2)

    # Test exact boundary coordinates
    assert layout.point_to_zone((0, 0)) == 0
    assert layout.point_to_zone((1, 1)) == 3

    # Test coordinates at the edge of validity
    assert layout.point_to_zone((1, 0)) == 1
    assert layout.point_to_zone((0, 1)) == 2


def test_large_grid():
    layout = GridLayout(rows=10, columns=12)

    assert layout.get_zone_count() == 120

    # Test some points in large grid
    assert layout.point_to_zone((0, 0)) == 0
    assert layout.point_to_zone((11, 9)) == 119  # Last zone

    # Test out of bounds
    assert layout.point_to_zone((12, 0)) is None
    assert layout.point_to_zone((0, 10)) is None


def test_single_row_grid():
    layout = GridLayout(rows=1, columns=5)

    assert layout.get_zone_count() == 5

    for col in range(5):
        assert layout.point_to_zone((col, 0)) == col

    # Second row doesn't exist
    assert layout.point_to_zone((0, 1)) is None


def test_single_column_grid():
    layout = GridLayout(rows=5, columns=1)

    assert layout.get_zone_count() == 5

    for row in range(5):
        assert layout.point_to_zone((0, row)) == row

    # Second column doesn't exist
    assert layout.point_to_zone((1, 0)) is None


def test_minimum_grid():
    layout = GridLayout(rows=1, columns=1)

    assert layout.get_zone_count() == 1
    assert layout.point_to_zone((0, 0)) == 0
    assert layout.point_to_zone((1, 0)) is None
    assert layout.point_to_zone((0, 1)) is None


def test_configure_maintains_bounds():
    layout = GridLayout(rows=2, columns=2)

    # Get initial bounds
    initial_bounds = layout.get_zone_bounds()

    # Reconfigure
    layout.configure({"rows": 3, "columns": 3})

    # Get new bounds
    new_bounds = layout.get_zone_bounds()

    # Should have different number of zones
    assert len(new_bounds) != len(initial_bounds)
    assert len(new_bounds) == 9  # 3 * 3


def test_zero_dimensions():
    # Test edge case with zero dimensions
    layout = GridLayout(rows=0, columns=5)

    assert layout.get_zone_count() == 0
    assert layout.point_to_zone((0, 0)) is None

    layout = GridLayout(rows=5, columns=0)

    assert layout.get_zone_count() == 0
    assert layout.point_to_zone((0, 0)) is None
