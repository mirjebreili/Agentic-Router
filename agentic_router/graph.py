import logging

from langgraph.graph import END, StateGraph

from .nodes.classify import classify
from .nodes.discover import discover
from .nodes.format import format_response
from .nodes.forward import forward
from .types import AgentState

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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