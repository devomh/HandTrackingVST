import json
import pytest
from hand_tracking_vst.src.config.config_manager import ConfigManager


def test_load_empty_config(tmp_path):
    config_path = tmp_path / "user_config.json"
    config_path.write_text("{}")
    manager = ConfigManager(str(config_path))
    assert manager.config == {}


def test_load_config_with_data(tmp_path):
    config_path = tmp_path / "user_config.json"
    test_config = {
        "camera": {"device_id": 1, "width": 1280},
        "midi": {"virtual_port_name": "TestPort"},
    }
    config_path.write_text(json.dumps(test_config))
    manager = ConfigManager(str(config_path))
    assert manager.config == test_config


def test_get_nested_key():
    config = {
        "camera": {"device_id": 1, "width": 1280},
        "midi": {"virtual_port_name": "TestPort"},
    }
    manager = ConfigManager()
    manager.config = config

    assert manager.get("camera.device_id") == 1
    assert manager.get("camera.width") == 1280
    assert manager.get("midi.virtual_port_name") == "TestPort"
    assert manager.get("nonexistent.key", "default") == "default"


def test_set_nested_key():
    manager = ConfigManager()
    manager.config = {}

    manager.set("camera.device_id", 2)
    manager.set("midi.virtual_port_name", "NewPort")

    assert manager.config["camera"]["device_id"] == 2
    assert manager.config["midi"]["virtual_port_name"] == "NewPort"


def test_save_and_reload(tmp_path):
    config_path = tmp_path / "test_config.json"
    manager = ConfigManager(str(config_path))

    manager.set("test.key", "test_value")
    manager.save()

    # Create new manager and reload
    new_manager = ConfigManager(str(config_path))
    assert new_manager.get("test.key") == "test_value"


def test_layout_presets():
    config = {
        "layout": {
            "presets": {"test_preset": {"rows": 2, "columns": 6, "base_note": 72}}
        }
    }
    manager = ConfigManager()
    manager.config = config

    presets = manager.get_layout_presets()
    assert "test_preset" in presets
    assert presets["test_preset"]["rows"] == 2


def test_apply_layout_preset():
    config = {
        "layout": {
            "rows": 3,
            "columns": 4,
            "presets": {"test_preset": {"rows": 2, "columns": 6, "base_note": 72}},
        }
    }
    manager = ConfigManager()
    manager.config = config

    manager.apply_layout_preset("test_preset")
    assert manager.get("layout.rows") == 2
    assert manager.get("layout.columns") == 6
    assert manager.get("layout.base_note") == 72


def test_apply_nonexistent_preset():
    manager = ConfigManager()
    manager.config = {"layout": {"presets": {}}}

    with pytest.raises(ValueError):
        manager.apply_layout_preset("nonexistent")
