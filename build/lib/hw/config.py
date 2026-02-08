"""Configuration file management for hw"""

import sys
from pathlib import Path
from typing import Dict

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


DEFAULT_LEAD_TIMES = {
    "exam": 10,
    "project": 7,
    "homework": 2,
    "quiz": 2,
    "reading": 1,
}

DEFAULT_CONFIG_CONTENT = """[lead_times]
exam = 10
project = 7
homework = 2
quiz = 2
reading = 1
"""


def get_config_dir() -> Path:
    """Get the config directory path (~/.hw/)"""
    return Path.home() / ".hw"


def get_config_path() -> Path:
    """Get the config file path (~/.hw/config.toml)"""
    return get_config_dir() / "config.toml"


def ensure_config_exists() -> None:
    """Create config directory and file with defaults if they don't exist"""
    config_dir = get_config_dir()
    config_path = get_config_path()

    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create config file with defaults if it doesn't exist
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG_CONTENT)


def load_lead_times() -> Dict[str, int]:
    """Load lead times from config file, creating it if necessary"""
    ensure_config_exists()

    config_path = get_config_path()
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    return config.get("lead_times", DEFAULT_LEAD_TIMES)
