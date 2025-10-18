"""Load and validate configuration for downstream agents."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

import yaml


def validate_agent_config(agent_name: str, agent_data: Dict[str, Any]) -> None:
    """
    Validates a single agent configuration.

    Args:
        agent_name: The name of the agent
        agent_data: The configuration data for the agent

    Raises:
        ValueError: If the configuration is invalid
    """
    required_fields = ["description"]

    for field in required_fields:
        if field not in agent_data:
            raise ValueError(f"Agent '{agent_name}' is missing required field: {field}")

    if not isinstance(agent_data["description"], str):
        raise ValueError(f"Agent '{agent_name}': 'description' must be a string")

    if "tools" in agent_data:
        if not isinstance(agent_data["tools"], list):
            raise ValueError(f"Agent '{agent_name}': 'tools' must be a list")

        # Validate each tool
        for idx, tool in enumerate(agent_data["tools"]):
            if not isinstance(tool, dict):
                raise ValueError(f"Agent '{agent_name}': tool at index {idx} must be a dictionary")

            required_tool_fields = ["name", "description"]
            for field in required_tool_fields:
                if field not in tool:
                    raise ValueError(
                        f"Agent '{agent_name}': tool at index {idx} is missing required field: {field}"
                    )

            if not isinstance(tool["name"], str):
                raise ValueError(f"Agent '{agent_name}': tool at index {idx} 'name' must be a string")

            if not isinstance(tool["description"], str):
                raise ValueError(f"Agent '{agent_name}': tool at index {idx} 'description' must be a string")


def load_and_validate_config() -> Dict[str, Dict[str, Any]]:
    """
    Loads and validates the agent configurations from agents_config.yaml.

    This function reads the YAML file, parses it, and validates its
    structure.

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

        # Validate that config_data is a dictionary
        if not isinstance(config_data, dict):
            raise ValueError("Configuration must be a dictionary")

        # Check for 'agents' key
        if "agents" not in config_data:
            raise ValueError("Configuration must contain an 'agents' key")

        agents = config_data["agents"]
        if not isinstance(agents, dict):
            raise ValueError("'agents' must be a dictionary")

        # Validate each agent configuration
        for agent_name, agent_data in agents.items():
            validate_agent_config(agent_name, agent_data)

        return agents

    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML in {config_path}: {e}") from e
    except Exception as e:
        raise ValueError(f"An unexpected error occurred while loading the configuration: {e}") from e


# Load and validate the configuration when the module is imported.
# Other modules can import this validated configuration directly.
AGENTS_CONFIG: Dict[str, Dict[str, Any]] = load_and_validate_config()
