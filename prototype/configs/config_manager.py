import logging

from prototype.path_config import CONFIG_DIR
from prototype.shared.utils.yaml_reader import load_yaml_with_defaults

CONFIGS = {
    "container_readiness.yaml": {
        "defaults": {
            "min_container_count": 50
        }
    }
}


def load_config(config_path_str: str) -> dict:
    """Load config from YAML, falling back to defaults if file is missing."""
    config_path = CONFIG_DIR / config_path_str
    defaults = CONFIGS.get(config_path_str, {}).get("defaults", {}).copy()
    return load_yaml_with_defaults(config_path, defaults)
