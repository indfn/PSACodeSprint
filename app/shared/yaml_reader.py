"""Shared YAML reader utility.

Provides a single entry point for loading YAML files across the prototype.
Used by config_manager.py and module-level data loaders.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_yaml(file_path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Args:
        file_path: Absolute path to the YAML file.

    Returns:
        Parsed YAML content, or empty dict on error.
    """
    try:
        with open(file_path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("YAML file not found: %s", file_path)
        return {}
    except yaml.YAMLError as exc:
        logger.error("Failed to parse YAML file %s: %s", file_path, exc)
        return {}


def load_yaml_with_defaults(
    file_path: Path,
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load a YAML file, merging with provided defaults.

    Default values are overridden by YAML content where keys overlap.

    Args:
        file_path: Absolute path to the YAML file.
        defaults: Optional dict of default values.

    Returns:
        Merged dict of defaults + YAML content.
    """
    result = (defaults or {}).copy()
    yaml_data = load_yaml(file_path)
    result.update(yaml_data)
    return result
