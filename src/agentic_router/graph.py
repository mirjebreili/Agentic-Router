"""Definition of the Agentic Router LangGraph graph."""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from .nodes.classify import classify
from .nodes.discover import discover
from .nodes.format import format_response
from .nodes.forward import forward
from .types import AgentState

logger = logging.getLogger(__name__)

workflow = StateGraph(AgentState)
workflow.add_node("classify", classify)
workflow.add_node("discover", discover)
workflow.add_node("forward", forward)
workflow.add_node("format", format_response)

workflow.set_entry_point("classify")
workflow.add_edge("classify", "discover")
workflow.add_edge("discover", "forward")
workflow.add_edge("forward", "format")
workflow.add_edge("format", END)

graph = workflow.compile(name="Agentic Router")
