"""Tests for state definitions."""

from src.state.base_state import ServiceDeskState, create_initial_state
from src.state.enums import EscalationReason, TicketCategory, TicketPriority


class TestServiceDeskState:
    """Tests for ServiceDeskState TypedDict."""

    def test_create_initial_state(self):
        """Should create initial state with correct defaults."""
        state = create_initial_state(
            user_input="Test input",
            session_id="test-123",
        )

        assert state["current_input"] == "Test input"
        assert state["session_id"] == "test-123"
        assert state["classification"] == "unknown"
        assert state["response"] == ""
        assert state["needs_human_escalation"] is False
        assert state["agent_trace"] == []
        assert state["errors"] == []

    def test_state_has_all_mvp_fields(self):
        """Should have all required MVP fields."""
        state = create_initial_state("test", "session-1")

        mvp_fields = [
            "messages",
            "current_input",
            "classification",
            "sub_classification",
            "response",
            "next_agent",
            "needs_human_escalation",
            "escalation_reason",
            "agent_trace",
            "errors",
            "session_id",
            "timestamp",
        ]

        for field in mvp_fields:
            assert field in state, f"Missing field: {field}"

    def test_state_has_stub_fields(self):
        """Should have stub fields for future phases."""
        state = create_initial_state("test", "session-1")

        stub_fields = [
            "email_components",
            "caller_info",
            "bank_info",
            "problem_classification",
            "ticket_info",
        ]

        for field in stub_fields:
            assert field in state, f"Missing stub field: {field}"


class TestEnums:
    """Tests for state enums."""

    def test_ticket_priority_values(self):
        """Should have correct priority values."""
        assert TicketPriority.LOW.value == "low"
        assert TicketPriority.MEDIUM.value == "medium"
        assert TicketPriority.HIGH.value == "high"
        assert TicketPriority.CRITICAL.value == "critical"

    def test_ticket_category_values(self):
        """Should have correct category values."""
        assert TicketCategory.IT_SUPPORT.value == "it_support"
        assert TicketCategory.BILLING.value == "billing"
        assert TicketCategory.GENERAL_INQUIRY.value == "general_inquiry"
        assert TicketCategory.ESCALATION.value == "escalation"

    def test_escalation_reason_values(self):
        """Should have correct escalation reason values."""
        assert EscalationReason.COMPLEX_ISSUE.value == "complex_issue"
        assert EscalationReason.CUSTOMER_REQUEST.value == "customer_request"
        assert EscalationReason.LOW_CONFIDENCE.value == "low_confidence"
