"""Bank Identifier Agent (STUB) - Identifies bank-related issues.

FUTURE PHASE: This agent will identify if an issue is related to a bank.
"""

from typing import Any

from src.agents.base_agent import BaseServiceDeskAgent
from src.state.base_state import ServiceDeskState


class BankIdentifierAgent(BaseServiceDeskAgent):
    """Bank Identifier Agent (Stub).

    FUTURE - Will identify if the issue is bank-related.

    Inputs:
        - email_components.signature: Email signature
        - email_components.sender_domain: Sender domain

    Outputs:
        - bank_info: BankInfo with identification details

    Tools:
        - match_bank_signatures: Compare against known bank signatures
        - lookup_bank_domains: Verify known bank domains
        - extract_bank_keywords: Find bank-related keywords in content
    """

    def __init__(self) -> None:
        """Initialize Bank Identifier Agent stub."""
        super().__init__(
            name="bank_identifier_agent",
            description="[STUB] Identifies bank-related issues",
            system_prompt="Eres un agente que identifica si un problema está relacionado con un banco.",
            tools=None,
        )

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """STUB: Returns simulated bank identification.

        Args:
            state: Current graph state.

        Returns:
            Simulated bank identification info.
        """
        user_input = state.get("current_input", "").lower()
        email_components = state.get("email_components", {})
        sender_domain = email_components.get("sender_domain", "")

        # Simple keyword detection for stub
        bank_keywords = [
            "banco",
            "bank",
            "bancario",
            "transferencia",
            "spei",
            "clabe",
        ]
        is_bank_related = any(kw in user_input for kw in bank_keywords)

        # Check for known bank domains (stub list)
        bank_domains = ["bancomer.com", "banamex.com", "santander.com.mx", "hsbc.com.mx"]
        domain_match = any(bd in sender_domain for bd in bank_domains)

        identified_by = None
        if domain_match:
            identified_by = "domain"
        elif is_bank_related:
            identified_by = "keywords"

        return {
            "bank_info": {
                "is_bank_related": is_bank_related or domain_match,
                "bank_name": None,
                "identified_by": identified_by,
                "confidence_score": 0.5 if (is_bank_related or domain_match) else 0.0,
            },
            "errors": ["BankIdentifierAgent es un stub - implementación pendiente"],
        }
