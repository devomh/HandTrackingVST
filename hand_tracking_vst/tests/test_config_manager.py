from hand_tracking_vst.src.config.config_manager import ConfigManager


def test_load_default(tmp_path):
    config_path = tmp_path / "user_config.json"
    config_path.write_text("{}")
    manager = ConfigManager(str(config_path))
    assert manager.config == {}
