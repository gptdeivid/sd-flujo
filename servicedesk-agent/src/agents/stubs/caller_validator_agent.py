"""Caller Validator Agent (STUB) - Validates authorized callers.

FUTURE PHASE: This agent will validate callers against an authorization matrix.
"""

from typing import Any

from src.agents.base_agent import BaseServiceDeskAgent
from src.state.base_state import ServiceDeskState


class CallerValidatorAgent(BaseServiceDeskAgent):
    """Caller Validator Agent (Stub).

    FUTURE - Will validate callers against authorization matrix.

    Inputs:
        - email_components.sender_domain: Domain to validate
        - current_time: For schedule validation

    Outputs:
        - caller_info: CallerInfo with authorization details

    Tools:
        - lookup_caller_matrix: Query caller authorization matrix (XLS)
        - check_schedule: Verify authorization schedule
        - get_caller_history: Get caller interaction history
    """

    def __init__(self) -> None:
        """Initialize Caller Validator Agent stub."""
        super().__init__(
            name="caller_validator_agent",
            description="[STUB] Validates callers against authorization matrix",
            system_prompt="Eres un agente que valida si un caller está autorizado.",
            tools=None,
        )

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """STUB: Returns simulated validation.

        Args:
            state: Current graph state.

        Returns:
            Simulated caller validation info.
        """
        email_components = state.get("email_components", {})
        sender_domain = email_components.get("sender_domain", "unknown")

        return {
            "caller_info": {
                "is_authorized": True,  # Stub: always authorized
                "caller_id": "STUB-001",
                "company": f"Empresa ({sender_domain})",
                "authorization_schedule": "24/7",
                "validation_timestamp": "2026-03-25T10:00:00Z",
            },
            "errors": ["CallerValidatorAgent es un stub - implementación pendiente"],
        }
