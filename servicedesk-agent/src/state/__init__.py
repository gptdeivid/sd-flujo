"""State definitions module."""

from src.state.base_state import ServiceDeskState
from src.state.enums import TicketCategory, TicketPriority, EscalationReason

__all__ = ["ServiceDeskState", "TicketCategory", "TicketPriority", "EscalationReason"]
