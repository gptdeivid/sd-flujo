"""Router Agent - Classifies incoming requests."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agents.base_agent import BaseServiceDeskAgent
from src.config.constants import CONFIDENCE_THRESHOLD
from src.config.prompts import ROUTER_SYSTEM_PROMPT
from src.llm.gemini_client import get_gemini_client_for_classification
from src.state.base_state import ServiceDeskState


class ClassificationOutput(BaseModel):
    """Schema for router structured output."""

    classification: str = Field(
        description="Request type: it_support, billing, general_inquiry, or escalation"
    )
    sub_classification: str = Field(
        default="",
        description="More specific subcategory if applicable",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Classification confidence level (0.0-1.0)",
    )
    reasoning: str = Field(
        description="Brief explanation of why this classification was chosen",
    )


class RouterAgent(BaseServiceDeskAgent):
    """Agent that classifies incoming requests.

    Inputs:
        - state.current_input: User request text
        - state.messages: Conversation history (context)

    Outputs:
        - classification: Main category (it_support, billing, etc.)
        - sub_classification: Detailed subcategory
        - next_agent: Name of next agent to execute
        - confidence_score: Classification confidence

    Tools:
        - None (pure LLM classification)
    """

    def __init__(self) -> None:
        """Initialize Router Agent."""
        super().__init__(
            name="router_agent",
            description="Classifies incoming Service Desk requests",
            system_prompt=ROUTER_SYSTEM_PROMPT,
            tools=None,
            llm=get_gemini_client_for_classification(),
        )

        # Configure LLM with structured output
        self.classifier = self.llm.with_structured_output(ClassificationOutput)

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Classify incoming request.

        Args:
            state: Current graph state.

        Returns:
            State updates with classification results.
        """
        user_input = state.get("current_input", "")

        if not user_input:
            return {
                "classification": "unknown",
                "next_agent": "unknown_handler",
                "confidence_score": 0.0,
                "errors": ["No se recibió input del usuario"],
            }

        # Build classification prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "human",
                    """Clasifica la siguiente solicitud del usuario:

SOLICITUD:
{input}

Determina:
1. La categoría principal (it_support, billing, general_inquiry, escalation)
2. Una subcategoría si aplica
3. Tu nivel de confianza (0.0-1.0)
4. Breve razonamiento""",
                ),
            ]
        )

        chain = prompt | self.classifier

        result: ClassificationOutput = chain.invoke({"input": user_input})

        # Determine if low confidence requires escalation
        needs_escalation = result.confidence < CONFIDENCE_THRESHOLD

        # Map classification to next agent
        next_agent = result.classification
        if needs_escalation:
            next_agent = "escalation"

        escalation_reason = None
        if needs_escalation:
            escalation_reason = f"Baja confianza en clasificación: {result.confidence:.2f}"

        return {
            "classification": result.classification,
            "sub_classification": result.sub_classification or None,
            "next_agent": next_agent,
            "confidence_score": result.confidence,
            "needs_human_escalation": needs_escalation,
            "escalation_reason": escalation_reason,
        }
