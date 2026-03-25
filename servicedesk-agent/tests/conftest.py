"""Pytest fixtures for Service Desk tests."""

from unittest.mock import AsyncMock, Mock

import pytest
from langchain_core.messages import AIMessage


@pytest.fixture
def mock_llm():
    """Mocked LLM for unit tests."""
    mock = Mock()
    mock.invoke = Mock(return_value=AIMessage(content="Test response"))
    mock.ainvoke = AsyncMock(return_value=AIMessage(content="Test response"))
    mock.with_structured_output = Mock(return_value=mock)
    mock.bind_tools = Mock(return_value=mock)
    return mock


@pytest.fixture
def sample_state():
    """Basic test state."""
    return {
        "messages": [],
        "current_input": "Mi computadora no enciende",
        "classification": "unknown",
        "sub_classification": None,
        "response": "",
        "next_agent": None,
        "needs_human_escalation": False,
        "escalation_reason": None,
        "agent_trace": [],
        "errors": [],
        "session_id": "test-session-001",
        "timestamp": "2026-03-25T10:00:00Z",
        "confidence_score": 0.0,
    }


@pytest.fixture
def it_support_state(sample_state):
    """State for IT Support tests."""
    return {
        **sample_state,
        "classification": "it_support",
        "sub_classification": "hardware",
    }


@pytest.fixture
def billing_state(sample_state):
    """State for Billing tests."""
    return {
        **sample_state,
        "current_input": "Necesito copia de mi factura del mes pasado",
        "classification": "billing",
    }


@pytest.fixture
def escalation_state(sample_state):
    """State for Escalation tests."""
    return {
        **sample_state,
        "current_input": "Quiero hablar con un humano",
        "classification": "escalation",
        "needs_human_escalation": True,
    }
