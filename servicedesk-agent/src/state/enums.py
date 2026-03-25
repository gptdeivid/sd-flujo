"""Enumerations for the Service Desk system."""

from enum import Enum


class TicketPriority(str, Enum):
    """Ticket priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(str, Enum):
    """Main ticket categories."""

    IT_SUPPORT = "it_support"
    BILLING = "billing"
    GENERAL_INQUIRY = "general_inquiry"
    ESCALATION = "escalation"
    UNKNOWN = "unknown"


class ITSubcategory(str, Enum):
    """IT support subcategories."""

    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    ACCESS = "access"
    OTHER = "other"


class BillingSubcategory(str, Enum):
    """Billing subcategories."""

    INVOICE = "invoice"
    PAYMENT = "payment"
    REFUND = "refund"
    PRICING = "pricing"
    OTHER = "other"


class EscalationReason(str, Enum):
    """Reasons for escalating to human agent."""

    COMPLEX_ISSUE = "complex_issue"
    CUSTOMER_REQUEST = "customer_request"
    POLICY_VIOLATION = "policy_violation"
    URGENT_MATTER = "urgent_matter"
    UNRESOLVED = "unresolved"
    SENSITIVE_DATA = "sensitive_data"
    LOW_CONFIDENCE = "low_confidence"


class AgentStatus(str, Enum):
    """Agent execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
