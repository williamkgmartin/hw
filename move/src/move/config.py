"""Configuration / paths for move."""

import os
from pathlib import Path


def get_config_dir() -> Path:
    """Where move stores its database. Override via MOVE_CONFIG_DIR for tests."""
    override = os.environ.get("MOVE_CONFIG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".move"
