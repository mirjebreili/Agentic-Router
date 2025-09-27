# Agentic Router

This project implements an agentic router using LangGraph, designed for full compatibility with the LangGraph Command-Line Interface (CLI). The router classifies user input based on keywords and forwards it to the appropriate specialized agent, whose configuration is defined in `agents_config.yaml`.

## Features

- **Keyword-Based Routing**: Classifies requests by searching for keywords (e.g., "gitlab," "jira") in the input.
- **Dynamic Agent Discovery**: Automatically discovers the `assistant_id` from target agent services before forwarding requests.
- **Validated Configuration**: Uses Pydantic models to validate `agents_config.yaml`, ensuring a correct setup.
- **LangGraph CLI Compatible**: Exposes a `graph` object for seamless integration with `langgraph dev` and `langgraph dcli`.

## Project Structure

The project follows LangGraph's recommended Python module structure under `src/` so the CLI can automatically load the graph:

```
src/
  agentic_router/
    ├── __init__.py        # Exposes the compiled graph object
    ├── agents_config.yaml # Agent definitions
    ├── config.py          # Loads and validates agents_config.yaml
    ├── graph.py           # Builds and compiles the LangGraph workflow
    ├── types.py           # Contains Pydantic models for state and configuration
    └── nodes/
        ├── __init__.py
        ├── classify.py    # Classifies input and selects an agent
        ├── discover.py    # Discovers the agent's assistant_id
        ├── forward.py     # Forwards the request to the target agent
        └── format.py      # Formats the final response
langgraph.json
pyproject.toml
README.md
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -e .
    ```

## How to Run and Test

### Running with `langgraph dev`

The `langgraph dev` command starts a local development server with a web interface, allowing you to interact with the graph in real-time.

From the project's root directory, run:
```bash
langgraph dev -m ./src/agentic_router/graph.py:graph
```
The server will be accessible at `http://127.0.0.1:8000`. You can use the web UI to send requests and visualize the graph's execution flow.

### Testing with `langgraph dcli`

The `langgraph dcli` command-line tool is ideal for scripting, testing, and direct interaction from your terminal.

**1. Invoke (Single Turn)**

Use `invoke` to send a single request and receive the final response.

```bash
langgraph dcli -m ./src/agentic_router/graph.py:graph invoke \
  --input '{"input_text": "can you check jira for the status of ticket T-123?"}'
```

**2. Stream Events (Real-Time Updates)**

Use `astream-events` to see the full sequence of events as the graph processes the request, including state changes at each node.

```bash
langgraph dcli -m ./src/agentic_router/graph.py:graph astream-events \
  --input '{"input_text": "what are the latest commits in the gitlab project?"}' \
  --output-keys 'response'
```

## Configuration

Agent routing behavior is defined in `src/agentic_router/agents_config.yaml`.

### Example `agents_config.yaml`

```yaml
agents:
  gitlab:
    name: "GitLab Assistant"
    description: "Handles GitLab project queries"
    host: "127.0.0.1"
    port: 2024
  jira:
    name: "Jira Assistant"
    description: "Handles Jira ticket queries"
    host: "127.0.0.1"
    port: 2025
```

- **`agents`**: The root key.
- **`gitlab` / `jira`**: These are the `agent_key`s. The `classify` node uses these keys to identify the agent. The keyword search is hard-coded to match these keys.
- **`name`**: The official name of the assistant. This is used during the discovery phase to find the correct `assistant_id`.
- **`host` / `port`**: The address of the target agent's service.

### Adding a New Agent

1.  **Define the Agent in `agents_config.yaml`**:
    Add a new entry under `agents`. Choose a simple, descriptive `agent_key` (e.g., `notion`).

    ```yaml
    agents:
      # ... existing agents
      notion:
        name: "Notion Assistant"
        description: "Handles Notion page queries"
        host: "127.0.0.1"
        port: 2026
    ```

2.  **Update the `classify` Node**:
    Open `src/agentic_router/nodes/classify.py` and add a condition to recognize keywords for your new agent.

    ```python
    # In classify.py
    # ...
    if "gitlab" in lower_input:
        agent_key = "gitlab"
    elif "jira" in lower_input:
        agent_key = "jira"
    elif "notion" in lower_input: # Add this
        agent_key = "notion"
    # ...
    ```

## Troubleshooting

- **`FileNotFoundError: agents_config.yaml not found`**: Ensure the YAML file exists in the `src/agentic_router/` directory and that you are running `langgraph` commands from the project's root directory.
- **`ValidationError` on startup**: Check `agents_config.yaml` for missing fields (`name`, `host`, `port`) or incorrect data types (e.g., `port` should be a number).
- **`No matching agent found`**: The `classify` node could not find any of its hard-coded keywords (e.g., "gitlab," "jira") in your input text. Make sure your input contains one of these keywords.
- **`Discovery failed: Assistant not found`**: The router connected to the agent's service but could not find an assistant with the expected `name`. Verify the `name` in `agents_config.yaml` matches the name configured in the target agent.
- **`Could not connect to agent`**: The router failed to establish a connection. Check if the target agent is running and if the `host` and `port` in `agents_config.yaml` are correct.