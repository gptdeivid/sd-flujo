"""Email Parser Agent (STUB) - Parses email components.

FUTURE PHASE: This agent will be activated when Gmail integration is added.
"""

from typing import Any

from src.agents.base_agent import BaseServiceDeskAgent
from src.state.base_state import ServiceDeskState


class EmailParserAgent(BaseServiceDeskAgent):
    """Email Parser Agent (Stub).

    FUTURE - Inputs:
        - raw_email: Raw email from Gmail API

    FUTURE - Outputs:
        - email_components: EmailComponents with sender, subject, body, etc.

    FUTURE - Tools:
        - extract_signature: Detect and extract signatures
        - detect_domain: Identify corporate domain
        - parse_attachments: List and categorize attachments
    """

    def __init__(self) -> None:
        """Initialize Email Parser Agent stub."""
        super().__init__(
            name="email_parser_agent",
            description="[STUB] Parses incoming email components",
            system_prompt="Eres un agente especializado en parsear emails empresariales.",
            tools=None,
        )

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """STUB: Returns simulated data.

        Args:
            state: Current graph state.

        Returns:
            Simulated email components.
        """
        return {
            "email_components": {
                "sender": "stub@example.com",
                "sender_name": "Usuario Stub",
                "sender_domain": "example.com",
                "subject": "Solicitud de prueba",
                "body": state.get("current_input", ""),
                "signature": None,
                "attachments": [],
                "received_at": "2026-03-25T10:00:00Z",
            },
            "errors": ["EmailParserAgent es un stub - implementación pendiente"],
        }
