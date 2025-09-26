import os
from pathlib import Path
from typing import Any, Dict

import yaml

def load_config() -> Dict[str, Any]:
    """
    Loads the agent configuration from the `agents_config.yaml` file.

    The path to the YAML file is resolved relative to this script's location.

    Returns:
        A dictionary containing the agent configurations.
        Returns an empty dictionary if the file is not found or is invalid.
    """
    config_path = Path(__file__).parent / "agents_config.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            return config.get("agents", {})
    except yaml.YAMLError as e:
        # In a real application, you might want to log this error.
        raise ValueError(f"Error parsing YAML configuration: {e}") from e

# Load the configuration once when the module is imported.
# Other modules can import this variable directly.
AGENTS_CONFIG: Dict[str, Any] = load_config()