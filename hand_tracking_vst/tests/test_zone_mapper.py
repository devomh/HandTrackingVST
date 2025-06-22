from hand_tracking_vst.src.core.zone_mapper import ZoneMapper
from hand_tracking_vst.src.layouts.grid_layout import GridLayout


def test_mapping_interval():
    layout = GridLayout(rows=2, columns=2)
    config = {"base_note": 60, "note_interval": 2}
    mapper = ZoneMapper(layout, config)
    assert mapper.map_zone_to_note(0) == 60
    assert mapper.map_zone_to_note(3) == 66
