"""Edge functions for the Service Desk Graph.

Defines functions that determine conditional routing between nodes.
"""

from typing import Literal

from src.state.base_state import ServiceDeskState


def route_by_classification(
    state: ServiceDeskState,
) -> Literal["it_support", "billing", "general_inquiry", "escalation", "unknown"]:
    """Determine next agent based on router classification.

    Args:
        state: Current graph state.

    Returns:
        Name of destination node.
    """
    classification = state.get("classification", "unknown")
    next_agent = state.get("next_agent")

    # If next_agent is explicitly set (e.g., for escalation), use it
    if next_agent and next_agent in {
        "it_support",
        "billing",
        "general_inquiry",
        "escalation",
    }:
        return next_agent  # type: ignore

    # Otherwise, use classification
    valid_routes = {"it_support", "billing", "general_inquiry", "escalation"}

    if classification in valid_routes:
        return classification  # type: ignore

    return "unknown"


def check_escalation_needed(
    state: ServiceDeskState,
) -> Literal["needs_escalation", "complete"]:
    """Check if escalation to human agent is needed.

    Args:
        state: Current graph state.

    Returns:
        "needs_escalation" if human required, "complete" otherwise.
    """
    if state.get("needs_human_escalation", False):
        return "needs_escalation"

    return "complete"
