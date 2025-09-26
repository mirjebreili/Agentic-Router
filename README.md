# Agentic Router using LangGraph

This project implements an "Agentic Router," a LangGraph-based application that acts as a smart intermediary, forwarding requests to other agents based on configurable routing rules. It is designed to be run with the `langgraph dev` server.

## Features

- **Dynamic Routing**: Classifies incoming requests and routes them to the appropriate target agent (e.g., GitLab, Jira).
- **External Configuration**: Agent endpoints and routing logic are defined in `agents_config.yaml`, allowing for easy updates without code changes.
- **Dynamic Assistant Discovery**: Automatically discovers `assistant_id`s for target agents via a direct `/assistants/search` call or a central registry agent.
- **Thread Management**: Maintains conversational context (`thread_id`) for each target agent.
- **Asynchronous A2A Communication**: Uses `httpx` for non-blocking, agent-to-agent communication following the JSON-RPC 2.0 standard.
- **Hot-Reloading**: The configuration file is automatically reloaded on change.

## Project Structure

```
.
├── router_app/
│   ├── __init__.py
│   ├── graph.py            # Main LangGraph assembly and `graph` export
│   ├── types.py            # Pydantic models for state and config
│   ├── nodes/              # LangGraph node implementations
│   │   ├── classify.py
│   │   ├── resolve_agent.py
│   │   ├── a2a_send.py
│   │   └── format.py
│   └── services/           # Helper services
│       ├── config.py         # YAML config loading
│       ├── discovery.py      # Assistant ID discovery
│       ├── a2a_client.py     # A2A HTTP client
│       └── logging.py        # Structured logging
├── agents_config.yaml    # External configuration for agents and routing
├── requirements.txt      # Project dependencies
└── README.md             # This file
```

## Setup and Installation

1.  **Clone the repository** (if applicable).

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

The application is served using LangGraph's development server.

1.  **Start the server**:
    From the root directory of the project, run the following command:
    ```bash
    langgraph dev -m router_app.graph:graph
    ```
    This command tells the server to load the `graph` object from the `router_app.graph` module.

2.  **Access the UI**:
    Once the server is running, you can access the LangGraph UI in your browser, typically at `http://127.0.0.1:8000`. From there, you can send requests to the router.

## Configuration (`agents_config.yaml`)

All configuration is managed in the `agents_config.yaml` file.

### Adding a New Agent

To add a new agent, add a new entry under the `agents` map. For example, to add a `confluence` agent:

```yaml
agents:
  # ... existing agents
  confluence:
    host: "127.0.0.1"
    port: 2027
    name: "confluence-agent"  # Name to match in /assistants/search
    registry_enabled: false
    assistant_id: ""          # Leave blank for discovery
```

### Configuration Fields

-   `agents`: A map of agent keys to their configurations.
    -   `host`, `port`: The address of the target agent.
    -   `name`: The name to match when using `/assistants/search` for discovery.
    -   `registry_enabled`: If `true`, the router will ask the `registry` agent to find this agent.
    -   `assistant_id`: Optional. If provided, discovery is skipped.
-   `registry`: Configuration for the central discovery agent.
-   `routing`:
    -   `mode`: Currently supports `keywords`. `llm` and `semantic` are placeholders.
    -   `default_agent`: An agent key to use if no other agent is matched.
-   `timeouts`, `retries`: Network configuration for the HTTP client.

## Example Usage (`curl`)

Here are some examples of how you might interact with the ecosystem.

### 1. Verify Assistant on Target Agent

You can check if a target agent (e.g., the `gitlab` agent running on port 2024) has a discoverable assistant:

```bash
curl -X POST http://127.0.0.1:2024/assistants/search \
  -H "Accept: application/json" \
  -d '{}'
```
This should return a list of assistants on that server. The router looks for one with a `name` matching the one in `agents_config.yaml`.

### 2. Send a Request to the Router

To send a message to the router, you need to use the A2A endpoint of the router itself. First, find the router's own `assistant_id` from the `langgraph dev` server startup logs or its UI.

Let's assume the router's `assistant_id` is `router-assistant-id`.

```bash
curl -X POST http://127.0.0.1:8000/a2a/router-assistant-id \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [
          {
            "kind": "text",
            "text": "Can you check the status of the latest gitlab pipeline?"
          }
        ]
      }
    }
  }'
```

The router will receive this, classify it as a `gitlab` request, forward it to the GitLab agent, and return the GitLab agent's response. On subsequent requests for GitLab, it will reuse the `thread_id` to maintain context.