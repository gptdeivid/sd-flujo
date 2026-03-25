"""Application constants."""

# Classification confidence threshold for escalation
CONFIDENCE_THRESHOLD = 0.6

# Maximum message history to keep in state
MAX_MESSAGE_HISTORY = 20

# API version
API_VERSION = "v1"

# Default session timeout in seconds
SESSION_TIMEOUT = 3600  # 1 hour

# Agent names for tracing
AGENT_NAMES = {
    "router": "router_agent",
    "it_support": "it_support_agent",
    "billing": "billing_agent",
    "general_inquiry": "general_inquiry_agent",
    "escalation": "escalation_agent",
    "email_parser": "email_parser_agent",
    "caller_validator": "caller_validator_agent",
    "bank_identifier": "bank_identifier_agent",
    "problem_classifier": "problem_classifier_agent",
}

# Valid classification categories
VALID_CLASSIFICATIONS = {
    "it_support",
    "billing",
    "general_inquiry",
    "escalation",
    "unknown",
}
