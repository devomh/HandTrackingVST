import json
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Configuration persistence and validation."""

    def __init__(self, config_path: str = "config/user_config.json") -> None:
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.is_file():
            return json.loads(self.config_path.read_text())
        return {}

    def get(self, key_path: str, default=None):
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
            if value is None:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split(".")
        target = self.config
        for key in keys[:-1]:
            target = target.setdefault(key, {})
        target[keys[-1]] = value

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.config, indent=2))

    def reload(self) -> None:
        self.config = self._load_config()

    def get_layout_presets(self) -> Dict[str, Dict]:
        return self.config.get("layout", {}).get("presets", {})

    def apply_layout_preset(self, preset_name: str) -> Dict:
        presets = self.get_layout_presets()
        if preset_name in presets:
            preset_config = presets[preset_name].copy()
            for key, value in preset_config.items():
                self.set(f"layout.{key}", value)
            return preset_config
        raise ValueError(f"Preset '{preset_name}' not found")
