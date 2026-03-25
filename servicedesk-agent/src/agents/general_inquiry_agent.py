"""General Inquiry Agent - Handles FAQs and general information."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseServiceDeskAgent
from src.config.prompts import GENERAL_INQUIRY_SYSTEM_PROMPT
from src.state.base_state import ServiceDeskState
from src.tools.mock_tools import get_office_info, search_faq


class GeneralInquiryAgent(BaseServiceDeskAgent):
    """Agent for general inquiries.

    Handles:
    - FAQs
    - Office hours and contact info
    - General procedures
    - Non-specific queries

    Inputs:
        - state.current_input: General question

    Outputs:
        - response: Informative response
        - needs_human_escalation: True if cannot answer

    Tools:
        - search_faq: Search FAQs
        - get_office_info: Get office information
    """

    def __init__(self) -> None:
        """Initialize General Inquiry Agent."""
        super().__init__(
            name="general_inquiry_agent",
            description="Answers general questions and FAQs",
            system_prompt=GENERAL_INQUIRY_SYSTEM_PROMPT,
            tools=[search_faq, get_office_info],
        )

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Process general inquiry.

        Args:
            state: Current graph state.

        Returns:
            State updates with response.
        """
        user_input = state.get("current_input", "")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "human",
                    """CONSULTA:
{input}

Proporciona una respuesta clara y concisa.
Si no tienes información suficiente, indica que se transferirá a un agente.

Usa las herramientas disponibles para buscar en FAQs u obtener información de oficinas.""",
                ),
            ]
        )

        chain = prompt | self.llm_with_tools
        result = chain.invoke({"input": user_input})

        response_text = self._extract_content(result)

        return {
            "response": response_text,
            "needs_human_escalation": False,
        }
