"""Base Agent - Abstract base class for all Service Desk agents."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI

from src.llm.gemini_client import get_gemini_client
from src.state.base_state import ServiceDeskState


class BaseServiceDeskAgent(ABC):
    """Abstract base class for Service Desk agents.

    All specialized agents must inherit from this class and implement
    the `process` method.

    Attributes:
        name: Unique agent identifier.
        description: Agent capabilities description.
        system_prompt: System prompt for this agent.
        tools: List of tools available to the agent.
        llm: LLM client instance.
    """

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        tools: Optional[list[BaseTool]] = None,
        llm: Optional[ChatGoogleGenerativeAI] = None,
    ) -> None:
        """Initialize the agent.

        Args:
            name: Unique agent name.
            description: Description of agent capabilities.
            system_prompt: System prompt for this agent.
            tools: Optional list of tools for the agent.
            llm: Optional LLM client (defaults to Gemini).
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.llm = llm or get_gemini_client()

        # Bind tools to LLM if any exist
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

    @abstractmethod
    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Process current state and return updates.

        Args:
            state: Current graph state.

        Returns:
            Dictionary with partial state updates.
        """
        pass

    def __call__(self, state: ServiceDeskState) -> dict[str, Any]:
        """Allow using agent as callable for LangGraph.

        Wraps the process method with error handling and tracing.

        Args:
            state: Current graph state.

        Returns:
            Dictionary with state updates including agent trace.
        """
        # Add agent to trace
        trace_update: dict[str, Any] = {"agent_trace": [self.name]}

        try:
            result = self.process(state)
            return {**trace_update, **result}
        except Exception as e:
            # Return error state with escalation
            return {
                **trace_update,
                "errors": [f"{self.name}: {str(e)}"],
                "needs_human_escalation": True,
                "escalation_reason": f"Error en {self.name}: {str(e)}",
            }

    def _extract_content(self, response: Any) -> str:
        """Extract text content from LLM response.

        Args:
            response: LLM response object.

        Returns:
            Extracted text content.
        """
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)
