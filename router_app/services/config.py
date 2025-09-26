"""
Configuration loading and management service.

This module handles loading, validation, and hot-reloading of the `agents_config.yaml` file.
"""
import os
import yaml
from pathlib import Path
from typing import Optional
from pydantic import ValidationError

from router_app.types import Config
from .logging import setup_logging

logger = setup_logging(__name__)

DEFAULT_CONFIG_PATH = Path("agents_config.yaml")
_config: Optional[Config] = None
_config_path: Optional[Path] = None
_last_mtime: Optional[float] = None


def get_config() -> Config:
    """
    Loads the agent configuration from a YAML file, validates it, and caches it.

    Supports hot-reloading by checking the file's last modification time.
    The config file path is determined by the `AGENTS_CONFIG_PATH` environment
    variable, falling back to `agents_config.yaml` in the current directory.

    Returns:
        The validated configuration object.

    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        ValidationError: If the configuration file has an invalid schema.
    """
    global _config, _config_path, _last_mtime

    env_path = os.getenv("AGENTS_CONFIG_PATH")
    current_path = Path(env_path) if env_path else DEFAULT_CONFIG_PATH

    if not current_path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {current_path}")

    # Check for hot-reload
    mtime = current_path.stat().st_mtime
    if _config is None or current_path != _config_path or mtime != _last_mtime:
        logger.info(f"Loading or reloading configuration from: {current_path}")
        try:
            with open(current_path, "r") as f:
                data = yaml.safe_load(f)

            _config = Config.model_validate(data)
            _config_path = current_path
            _last_mtime = mtime
            logger.info("Configuration loaded successfully.")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading config: {e}")
            raise

    return _config