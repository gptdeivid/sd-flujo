"""Escalation Agent - Handles cases for human agents."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseServiceDeskAgent
from src.config.prompts import ESCALATION_SYSTEM_PROMPT
from src.state.base_state import ServiceDeskState


class EscalationAgent(BaseServiceDeskAgent):
    """Agent that prepares cases for human handoff.

    Handles:
    - Complex cases outside automated scope
    - Explicit requests to speak with human
    - Emergencies
    - VIP or sensitive cases

    Inputs:
        - state.current_input: Original request
        - state.classification: Previous classification
        - state.escalation_reason: Escalation reason

    Outputs:
        - response: Escalation confirmation message
        - needs_human_escalation: Always True
        - escalation_reason: Detailed reason

    Tools:
        - None (prepares data for human handoff)
    """

    def __init__(self) -> None:
        """Initialize Escalation Agent."""
        super().__init__(
            name="escalation_agent",
            description="Prepares cases for human agent handoff",
            system_prompt=ESCALATION_SYSTEM_PROMPT,
            tools=None,
        )

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Prepare case for human escalation.

        Args:
            state: Current graph state.

        Returns:
            State updates with escalation info.
        """
        user_input = state.get("current_input", "")
        existing_reason = state.get("escalation_reason", "")
        classification = state.get("classification", "unknown")
        agent_trace = state.get("agent_trace", [])

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "human",
                    """SOLICITUD PARA ESCALAMIENTO:
{input}

CLASIFICACIÓN PREVIA: {classification}
RAZÓN DE ESCALAMIENTO: {reason}
AGENTES CONSULTADOS: {agents}

Genera:
1. Un mensaje amable informando al usuario que su caso será atendido por un agente humano
2. Qué debe esperar el usuario a continuación
3. Un resumen interno del caso para el agente que lo recibirá

El mensaje al usuario debe ser profesional y empático.""",
                ),
            ]
        )

        chain = prompt | self.llm
        result = chain.invoke(
            {
                "input": user_input,
                "classification": classification,
                "reason": existing_reason or "Solicitud de atención personalizada",
                "agents": ", ".join(agent_trace) if agent_trace else "ninguno",
            }
        )

        response_text = self._extract_content(result)

        # Build final escalation reason
        final_reason = existing_reason or "Derivado a atención humana por complejidad"

        return {
            "response": response_text,
            "needs_human_escalation": True,
            "escalation_reason": final_reason,
        }
