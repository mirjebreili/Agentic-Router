# Agentic Router

This project implements an agentic router using LangGraph. The router classifies user input and forwards it to the appropriate specialized agent based on a configuration file.

## Features

- **Dynamic Agent Routing**: Classifies user requests and routes them to the correct agent.
- **Agent Discovery**: Automatically discovers `assistant_id` from target agent services.
- **Extensible Configuration**: Easily add or modify agents in `agents_config.yaml`.
- **LangGraph Integration**: Exposes a `graph` object for use with `langgraph dev`.

## Project Structure

```
agentic_router/
  ├── __init__.py
  ├── graph.py            # Exposes `graph` for langgraph dev
  ├── config.py           # Loads agents_config.yaml
  ├── nodes/
  │   ├── classify.py     # Chooses agent key by prompting LLM with descriptions
  │   ├── discover.py     # Queries target host:port to get assistant_id
  │   ├── forward.py      # Sends A2A JSON-RPC message/send
  │   └── format.py       # Returns response_text
  └── agents_config.yaml
requirements.txt
README.md
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd agentic_router
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    You need to have an `OPENAI_API_KEY` environment variable set to use the classification service.
    ```bash
    export OPENAI_API_KEY="your-openai-api-key"
    ```

## Usage

1.  **Update Configuration:**
    Modify `agentic_router/agents_config.yaml` to define your agents. Each agent needs a `name`, `description`, `host`, and `port`.

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

2.  **Run the LangGraph Dev Server:**
    From the root directory of the project, run the following command:
    ```bash
    langgraph dev -m agentic_router.graph:graph
    ```
    This will start the LangGraph development server, typically available at `http://127.0.0.1:8000`. You can use this interface to test the agentic router.

## How It Works

The graph follows these steps:
1.  **`classify`**: Takes the user input and uses an LLM to decide which agent (`gitlab` or `jira`) is best suited to handle the request based on the descriptions in `agents_config.yaml`.
2.  **`discover`**: Connects to the chosen agent's service to find its unique `assistant_id`.
3.  **`forward`**: Sends the user's request in a standard A2A (Agent-to-Agent) JSON-RPC format to the agent.
4.  **`format`**: Extracts the final text response from the agent's reply and returns it to the user.