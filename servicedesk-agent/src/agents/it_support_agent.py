"""IT Support Agent - Handles technical issues."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseServiceDeskAgent
from src.config.prompts import IT_SUPPORT_SYSTEM_PROMPT
from src.state.base_state import ServiceDeskState
from src.tools.mock_tools import (
    check_system_status,
    create_it_ticket,
    get_troubleshooting_guide,
)


class ITSupportAgent(BaseServiceDeskAgent):
    """Agent for IT support issues.

    Specialized in:
    - Hardware (computers, peripherals)
    - Software (installations, errors, updates)
    - Networks (connectivity, VPN, WiFi)
    - Access (permissions, accounts, passwords)

    Inputs:
        - state.current_input: Technical problem description
        - state.sub_classification: Specific type (hardware, software, etc.)
        - state.messages: Conversation history

    Outputs:
        - response: Solution or troubleshooting guide
        - needs_human_escalation: True if issue is complex
        - escalation_reason: Escalation reason if applicable

    Tools:
        - check_system_status: Check system status
        - get_troubleshooting_guide: Get troubleshooting steps
        - create_it_ticket: Create support ticket
    """

    def __init__(self) -> None:
        """Initialize IT Support Agent."""
        super().__init__(
            name="it_support_agent",
            description="Resolves technical issues: hardware, software, networks, access",
            system_prompt=IT_SUPPORT_SYSTEM_PROMPT,
            tools=[check_system_status, get_troubleshooting_guide, create_it_ticket],
        )

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Process IT support request.

        Args:
            state: Current graph state.

        Returns:
            State updates with response and escalation info.
        """
        user_input = state.get("current_input", "")
        sub_class = state.get("sub_classification", "")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "human",
                    """PROBLEMA REPORTADO:
{input}

SUBCATEGORÍA: {sub_classification}

Proporciona una solución o guía de troubleshooting.
Si el problema requiere atención presencial o acceso administrativo, indica que necesita escalamiento.

Usa las herramientas disponibles si es necesario para verificar estado de sistemas o proporcionar guías.""",
                ),
            ]
        )

        chain = prompt | self.llm_with_tools

        result = chain.invoke(
            {
                "input": user_input,
                "sub_classification": sub_class or "no especificada",
            }
        )

        response_text = self._extract_content(result)

        # Detect if escalation is needed
        escalation_keywords = [
            "acceso administrativo",
            "revisión física",
            "urgente",
            "crítico",
            "técnico presencial",
            "hardware dañado",
            "pérdida de datos",
        ]
        needs_escalation = any(
            kw in response_text.lower() for kw in escalation_keywords
        )

        return {
            "response": response_text,
            "needs_human_escalation": needs_escalation,
            "escalation_reason": (
                "Requiere intervención manual de IT" if needs_escalation else None
            ),
        }
