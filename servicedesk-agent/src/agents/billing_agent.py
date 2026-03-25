"""Billing Agent - Handles billing and payment queries."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseServiceDeskAgent
from src.config.prompts import BILLING_SYSTEM_PROMPT
from src.state.base_state import ServiceDeskState
from src.tools.mock_tools import (
    check_payment_status,
    lookup_invoice,
    request_invoice_copy,
)


class BillingAgent(BaseServiceDeskAgent):
    """Agent for billing inquiries.

    Specialized in:
    - Invoices (queries, copy requests, clarifications)
    - Payments (status, confirmations, methods)
    - Refunds (requests, status, policies)
    - Pricing (quotes, plans, discounts)

    Inputs:
        - state.current_input: Billing query
        - state.sub_classification: Type (invoice, payment, refund, pricing)

    Outputs:
        - response: Billing information or next steps
        - needs_human_escalation: True for disputes or complex cases

    Tools:
        - lookup_invoice: Search invoices
        - check_payment_status: Verify payments
        - request_invoice_copy: Request invoice copies
    """

    def __init__(self) -> None:
        """Initialize Billing Agent."""
        super().__init__(
            name="billing_agent",
            description="Resolves billing, payment, and refund queries",
            system_prompt=BILLING_SYSTEM_PROMPT,
            tools=[lookup_invoice, check_payment_status, request_invoice_copy],
        )

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Process billing query.

        Args:
            state: Current graph state.

        Returns:
            State updates with response and escalation info.
        """
        user_input = state.get("current_input", "")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "human",
                    """CONSULTA DE FACTURACIÓN:
{input}

Proporciona la información solicitada o los pasos a seguir.
Para disputas de cobro o reembolsos mayores, indica que se requiere revisión manual.

Usa las herramientas disponibles para buscar facturas o verificar pagos si es necesario.""",
                ),
            ]
        )

        chain = prompt | self.llm_with_tools
        result = chain.invoke({"input": user_input})

        response_text = self._extract_content(result)

        # Detect cases requiring escalation
        escalation_triggers = [
            "disputa",
            "reembolso",
            "error de cobro",
            "cargo no reconocido",
            "doble cobro",
            "fraude",
            "cancelación",
        ]
        needs_escalation = any(
            trigger in user_input.lower() for trigger in escalation_triggers
        )

        return {
            "response": response_text,
            "needs_human_escalation": needs_escalation,
            "escalation_reason": (
                "Caso de facturación requiere revisión manual"
                if needs_escalation
                else None
            ),
        }
