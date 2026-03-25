"""Node functions for the Service Desk Graph.

Each function receives state and returns partial state updates.
"""

from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage

from src.agents.billing_agent import BillingAgent
from src.agents.escalation_agent import EscalationAgent
from src.agents.general_inquiry_agent import GeneralInquiryAgent
from src.agents.it_support_agent import ITSupportAgent
from src.agents.router_agent import RouterAgent
from src.state.base_state import ServiceDeskState


# Initialize agents (lazy loading would be better for production)
_router_agent: RouterAgent | None = None
_it_support_agent: ITSupportAgent | None = None
_billing_agent: BillingAgent | None = None
_general_inquiry_agent: GeneralInquiryAgent | None = None
_escalation_agent: EscalationAgent | None = None


def _get_router_agent() -> RouterAgent:
    """Get or create RouterAgent instance."""
    global _router_agent
    if _router_agent is None:
        _router_agent = RouterAgent()
    return _router_agent


def _get_it_support_agent() -> ITSupportAgent:
    """Get or create ITSupportAgent instance."""
    global _it_support_agent
    if _it_support_agent is None:
        _it_support_agent = ITSupportAgent()
    return _it_support_agent


def _get_billing_agent() -> BillingAgent:
    """Get or create BillingAgent instance."""
    global _billing_agent
    if _billing_agent is None:
        _billing_agent = BillingAgent()
    return _billing_agent


def _get_general_inquiry_agent() -> GeneralInquiryAgent:
    """Get or create GeneralInquiryAgent instance."""
    global _general_inquiry_agent
    if _general_inquiry_agent is None:
        _general_inquiry_agent = GeneralInquiryAgent()
    return _general_inquiry_agent


def _get_escalation_agent() -> EscalationAgent:
    """Get or create EscalationAgent instance."""
    global _escalation_agent
    if _escalation_agent is None:
        _escalation_agent = EscalationAgent()
    return _escalation_agent


def input_node(state: ServiceDeskState) -> dict[str, Any]:
    """Process input and prepare initial state.

    Args:
        state: Current graph state.

    Returns:
        Initial state updates.
    """
    user_input = state.get("current_input", "")

    # Add user message to history
    messages = [HumanMessage(content=user_input)]

    return {
        "messages": messages,
        "timestamp": datetime.now().isoformat(),
        "agent_trace": ["input_processor"],
    }


def router_node(state: ServiceDeskState) -> dict[str, Any]:
    """Route request to appropriate agent.

    Args:
        state: Current graph state.

    Returns:
        Classification and routing updates.
    """
    agent = _get_router_agent()
    return agent(state)


def it_support_node(state: ServiceDeskState) -> dict[str, Any]:
    """Handle IT support requests.

    Args:
        state: Current graph state.

    Returns:
        IT support response updates.
    """
    agent = _get_it_support_agent()
    return agent(state)


def billing_node(state: ServiceDeskState) -> dict[str, Any]:
    """Handle billing requests.

    Args:
        state: Current graph state.

    Returns:
        Billing response updates.
    """
    agent = _get_billing_agent()
    return agent(state)


def general_inquiry_node(state: ServiceDeskState) -> dict[str, Any]:
    """Handle general inquiries.

    Args:
        state: Current graph state.

    Returns:
        General inquiry response updates.
    """
    agent = _get_general_inquiry_agent()
    return agent(state)


def escalation_node(state: ServiceDeskState) -> dict[str, Any]:
    """Handle escalation to human.

    Args:
        state: Current graph state.

    Returns:
        Escalation response updates.
    """
    agent = _get_escalation_agent()
    return agent(state)


def unknown_handler_node(state: ServiceDeskState) -> dict[str, Any]:
    """Handle unknown/unclassified requests.

    Args:
        state: Current graph state.

    Returns:
        Unknown handler response updates.
    """
    return {
        "response": (
            "No pude clasificar tu solicitud correctamente. "
            "Por favor, proporciona más detalles o intenta reformular tu pregunta. "
            "Si prefieres, puedo transferirte con un agente humano."
        ),
        "needs_human_escalation": False,
        "agent_trace": ["unknown_handler"],
    }


def response_formatter_node(state: ServiceDeskState) -> dict[str, Any]:
    """Format final response.

    Args:
        state: Current graph state.

    Returns:
        Formatted response updates.
    """
    response = state.get("response", "")

    # Add standard footer if not already present
    if response and "Service Desk" not in response:
        response = f"{response}\n\n---\nService Desk - Estamos para ayudarte"

    return {
        "response": response,
        "agent_trace": ["response_formatter"],
    }


def escalation_handler_node(state: ServiceDeskState) -> dict[str, Any]:
    """Handle final escalation processing.

    Args:
        state: Current graph state.

    Returns:
        Final escalation updates.
    """
    response = state.get("response", "")
    escalation_reason = state.get("escalation_reason", "")

    # Add escalation notice to response if not present
    if "agente humano" not in response.lower():
        escalation_notice = (
            "\n\n⚠️ Tu caso ha sido marcado para atención prioritaria "
            "por un agente humano. Te contactaremos pronto."
        )
        response = f"{response}{escalation_notice}"

    return {
        "response": response,
        "needs_human_escalation": True,
        "agent_trace": ["escalation_handler"],
    }
