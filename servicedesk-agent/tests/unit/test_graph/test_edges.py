"""Tests for graph edge functions."""

from src.graph.edges import check_escalation_needed, route_by_classification


class TestRouteByClassification:
    """Tests for route_by_classification edge function."""

    def test_routes_it_support(self, sample_state):
        """Should route to it_support when classified as such."""
        sample_state["classification"] = "it_support"
        result = route_by_classification(sample_state)
        assert result == "it_support"

    def test_routes_billing(self, sample_state):
        """Should route to billing when classified as such."""
        sample_state["classification"] = "billing"
        result = route_by_classification(sample_state)
        assert result == "billing"

    def test_routes_general_inquiry(self, sample_state):
        """Should route to general_inquiry when classified as such."""
        sample_state["classification"] = "general_inquiry"
        result = route_by_classification(sample_state)
        assert result == "general_inquiry"

    def test_routes_escalation(self, sample_state):
        """Should route to escalation when classified as such."""
        sample_state["classification"] = "escalation"
        result = route_by_classification(sample_state)
        assert result == "escalation"

    def test_routes_unknown_for_invalid(self, sample_state):
        """Should route to unknown for invalid classification."""
        sample_state["classification"] = "invalid_category"
        result = route_by_classification(sample_state)
        assert result == "unknown"

    def test_uses_next_agent_when_set(self, sample_state):
        """Should use next_agent if explicitly set."""
        sample_state["classification"] = "billing"
        sample_state["next_agent"] = "escalation"
        result = route_by_classification(sample_state)
        assert result == "escalation"


class TestCheckEscalationNeeded:
    """Tests for check_escalation_needed edge function."""

    def test_returns_complete_when_no_escalation(self, sample_state):
        """Should return complete when no escalation needed."""
        sample_state["needs_human_escalation"] = False
        result = check_escalation_needed(sample_state)
        assert result == "complete"

    def test_returns_needs_escalation_when_flagged(self, sample_state):
        """Should return needs_escalation when flagged."""
        sample_state["needs_human_escalation"] = True
        result = check_escalation_needed(sample_state)
        assert result == "needs_escalation"

    def test_defaults_to_complete_when_not_set(self, sample_state):
        """Should default to complete when flag not set."""
        if "needs_human_escalation" in sample_state:
            del sample_state["needs_human_escalation"]
        result = check_escalation_needed(sample_state)
        assert result == "complete"
