import logging

import yaml
from prototype.path_config import CONFIG_DIR

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
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        defaults.update(config)
    except FileNotFoundError:
        logging.warning("Config not found at %s, using defaults", config_path)
    return defaults