"""
Assembles and exposes the main LangGraph for the Agentic Router.

This module defines the StateGraph, adds all the nodes, connects them with
conditional edges, and compiles the final graph instance that can be served
by `langgraph dev`.
"""
from langgraph.graph import StateGraph, END
from typing import Literal

from router_app.types import RouterState
from router_app.nodes.classify import classify_input
from router_app.nodes.resolve_agent import resolve_agent
from router_app.nodes.a2a_send import a2a_send
from router_app.nodes.format import format_output

# Define the graph
workflow = StateGraph(RouterState)

# Add nodes to the graph
workflow.add_node("classify", classify_input)
workflow.add_node("resolve_agent", resolve_agent)
workflow.add_node("a2a_send", a2a_send)
workflow.add_node("format_output", format_output)

# Set the entrypoint
workflow.set_entry_point("classify")


# Define conditional edges
def should_continue(state: RouterState) -> Literal["continue", "end"]:
    """Determines whether to continue to the next step or end due to an error."""
    return "end" if state.get("error") else "continue"


workflow.add_conditional_edges(
    "classify",
    should_continue,
    {
        "continue": "resolve_agent",
        "end": "format_output",
    },
)
workflow.add_conditional_edges(
    "resolve_agent",
    should_continue,
    {
        "continue": "a2a_send",
        "end": "format_output",
    },
)

# Define normal edges
workflow.add_edge("a2a_send", "format_output")
workflow.add_edge("format_output", END)

# Compile the graph and expose it for the dev server
graph = workflow.compile()

# To allow the server to run, we need to expose the graph instance.
# Example of how to run from the command line:
# langgraph dev -m router_app.graph:graph