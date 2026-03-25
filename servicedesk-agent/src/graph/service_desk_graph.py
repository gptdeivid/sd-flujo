"""Service Desk Graph - LangGraph StateGraph main orchestration.

This module defines the state graph that orchestrates all agents
in the Service Desk system.
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.graph.edges import check_escalation_needed, route_by_classification
from src.graph.nodes import (
    billing_node,
    escalation_handler_node,
    escalation_node,
    general_inquiry_node,
    input_node,
    it_support_node,
    response_formatter_node,
    router_node,
    unknown_handler_node,
)
from src.state.base_state import ServiceDeskState


def create_service_desk_graph() -> StateGraph:
    """Create and configure the Service Desk graph.

    Returns:
        Configured StateGraph (not yet compiled).
    """
    # Create graph with defined state
    graph = StateGraph(ServiceDeskState)

    # === ADD NODES ===

    # Input node - prepares initial state
    graph.add_node("input_processor", input_node)

    # Router - classifies the request
    graph.add_node("router", router_node)

    # Specialized agents
    graph.add_node("it_support", it_support_node)
    graph.add_node("billing", billing_node)
    graph.add_node("general_inquiry", general_inquiry_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("unknown", unknown_handler_node)

    # Output nodes
    graph.add_node("response_formatter", response_formatter_node)
    graph.add_node("escalation_handler", escalation_handler_node)

    # === DEFINE EDGES ===

    # START -> Input Processor
    graph.add_edge(START, "input_processor")

    # Input Processor -> Router
    graph.add_edge("input_processor", "router")

    # Router -> Specialized agent (conditional edge)
    graph.add_conditional_edges(
        "router",
        route_by_classification,
        {
            "it_support": "it_support",
            "billing": "billing",
            "general_inquiry": "general_inquiry",
            "escalation": "escalation",
            "unknown": "unknown",
        },
    )

    # Specialized agents -> Response Formatter
    graph.add_edge("it_support", "response_formatter")
    graph.add_edge("billing", "response_formatter")
    graph.add_edge("general_inquiry", "response_formatter")
    graph.add_edge("escalation", "response_formatter")
    graph.add_edge("unknown", "response_formatter")

    # Response Formatter -> Check Escalation (conditional edge)
    graph.add_conditional_edges(
        "response_formatter",
        check_escalation_needed,
        {
            "needs_escalation": "escalation_handler",
            "complete": END,
        },
    )

    # Escalation Handler -> END
    graph.add_edge("escalation_handler", END)

    return graph


def compile_graph(with_checkpointer: bool = False):
    """Compile the graph for execution.

    Args:
        with_checkpointer: Whether to include checkpointer for persistence.

    Returns:
        Compiled graph.
    """
    graph = create_service_desk_graph()

    if with_checkpointer:
        # For production, use PostgresSaver or SqliteSaver
        checkpointer = MemorySaver()
        return graph.compile(checkpointer=checkpointer)

    return graph.compile()


# Global compiled graph instance (lazy initialization)
_service_desk_app = None


def get_service_desk_app():
    """Get or create the compiled Service Desk app.

    Returns:
        Compiled LangGraph app.
    """
    global _service_desk_app
    if _service_desk_app is None:
        _service_desk_app = compile_graph()
    return _service_desk_app


# For backwards compatibility
service_desk_app = None  # Will be initialized on first import if needed


def invoke_service_desk(
    user_input: str,
    session_id: str = "default",
) -> dict:
    """Invoke the Service Desk graph with user input.

    Args:
        user_input: User's message/request.
        session_id: Session identifier.

    Returns:
        Final state after graph execution.
    """
    app = get_service_desk_app()

    initial_state = {
        "current_input": user_input,
        "session_id": session_id,
        "messages": [],
        "agent_trace": [],
        "errors": [],
    }

    result = app.invoke(initial_state)
    return result
