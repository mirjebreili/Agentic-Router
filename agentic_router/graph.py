import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

# Import the node functions from their respective modules
from .nodes.classify import classify
from .nodes.discover import discover
from .nodes.forward import forward
from .nodes.format import format_response

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """
    Represents the state of the agentic router graph.

    Attributes:
        input_text: The initial user query.
        agent_key: The key of the agent selected by the classification node (e.g., "gitlab").
        assistant_id: The unique ID of the assistant, discovered from its service.
        host: The hostname of the target agent service.
        port: The port number of the target agent service.
        thread_id: The conversation thread ID, for maintaining context.
        response: The final text response from the agent.
    """
    input_text: str
    agent_key: Optional[str]
    assistant_id: Optional[str]
    host: Optional[str]
    port: Optional[int]
    thread_id: Optional[str]
    response: Optional[str]

# Initialize the state graph
workflow = StateGraph(AgentState)

# Add the nodes to the graph
logger.info("Adding nodes to the graph...")
workflow.add_node("classify", classify)
workflow.add_node("discover", discover)
workflow.add_node("forward", forward)
workflow.add_node("format", format_response)

# Define the sequence of operations
logger.info("Setting up graph edges...")
workflow.set_entry_point("classify")
workflow.add_edge("classify", "discover")
workflow.add_edge("discover", "forward")
workflow.add_edge("forward", "format")
workflow.add_edge("format", END)

# Compile the graph
logger.info("Compiling the graph...")
graph = workflow.compile()
logger.info("Graph compiled successfully. Ready for use.")

# To run this graph with langgraph dev:
# langgraph dev -m agentic_router.graph:graph