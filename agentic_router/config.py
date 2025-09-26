from pathlib import Path
from typing import Dict

import yaml
from pydantic import ValidationError

from .types import AgentsConfig, ToolConfig


def load_and_validate_config() -> Dict[str, ToolConfig]:
    """
    Loads and validates the agent configurations from agents_config.yaml.

    This function reads the YAML file, parses it, and validates its
    structure using the Pydantic models defined in `agentic_router.types`.

    Returns:
        A dictionary of validated agent configurations.

    Raises:
        FileNotFoundError: If agents_config.yaml is not found.
        ValueError: If the configuration is invalid or fails validation.
    """
    config_path = Path(__file__).parent / "agents_config.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        # Validate the entire structure
        validated_config = AgentsConfig(**config_data)
        return validated_config.agents

    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML in {config_path}: {e}") from e
    except ValidationError as e:
        raise ValueError(f"Invalid configuration in {config_path}: {e}") from e
    except Exception as e:
        raise ValueError(f"An unexpected error occurred while loading the configuration: {e}") from e


# Load and validate the configuration when the module is imported.
# Other modules can import this validated configuration directly.
AGENTS_CONFIG: Dict[str, ToolConfig] = load_and_validate_config()