"""Problem Classifier Agent (STUB) - Classifies by XLS categories.

FUTURE PHASE: This agent will classify problems based on an XLS category matrix.
"""

from typing import Any

from src.agents.base_agent import BaseServiceDeskAgent
from src.state.base_state import ServiceDeskState


class ProblemClassifierAgent(BaseServiceDeskAgent):
    """Problem Classifier Agent (Stub).

    FUTURE - Will classify problems based on XLS category matrix.

    Inputs:
        - current_input: Problem description
        - bank_info: Bank identification (if applicable)
        - classification: Router's initial classification

    Outputs:
        - problem_classification: Detailed ProblemClassification

    Tools:
        - load_category_matrix: Load XLS category definitions
        - match_category: Find matching category based on keywords
        - get_priority_rules: Get priority assignment rules
    """

    def __init__(self) -> None:
        """Initialize Problem Classifier Agent stub."""
        super().__init__(
            name="problem_classifier_agent",
            description="[STUB] Classifies problems based on XLS category matrix",
            system_prompt="Eres un agente que clasifica problemas según una matriz de categorías.",
            tools=None,
        )

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """STUB: Returns simulated classification.

        Args:
            state: Current graph state.

        Returns:
            Simulated problem classification.
        """
        classification = state.get("classification", "unknown")
        sub_classification = state.get("sub_classification", "")
        user_input = state.get("current_input", "").lower()

        # Simple keyword-based priority for stub
        priority = "medium"
        if any(kw in user_input for kw in ["urgente", "crítico", "caído", "no funciona"]):
            priority = "high"
        elif any(kw in user_input for kw in ["cuando pueda", "no urgente", "consulta"]):
            priority = "low"

        # Extract potential keywords
        matched_keywords = []
        keyword_map = {
            "vpn": ["vpn", "conexión remota"],
            "email": ["correo", "email", "outlook"],
            "password": ["contraseña", "password", "acceso"],
            "hardware": ["laptop", "computadora", "monitor", "teclado"],
            "software": ["aplicación", "programa", "error", "instalar"],
        }

        for category, keywords in keyword_map.items():
            if any(kw in user_input for kw in keywords):
                matched_keywords.extend(keywords)

        return {
            "problem_classification": {
                "category": classification,
                "subcategory": sub_classification or "general",
                "priority": priority,
                "confidence_score": 0.5,
                "matched_keywords": list(set(matched_keywords))[:5],
            },
            "errors": ["ProblemClassifierAgent es un stub - implementación pendiente"],
        }
