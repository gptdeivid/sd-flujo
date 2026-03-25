"""Ticket processing endpoints."""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.graph.service_desk_graph import invoke_service_desk

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tickets"])


class TicketRequest(BaseModel):
    """Request model for ticket creation."""

    message: str = Field(..., min_length=1, description="User message or request")
    session_id: Optional[str] = Field(
        default=None, description="Session ID for conversation tracking"
    )


class TicketResponse(BaseModel):
    """Response model for ticket processing."""

    session_id: str
    classification: str
    sub_classification: Optional[str]
    response: str
    needs_human_escalation: bool
    escalation_reason: Optional[str]
    confidence_score: float
    agent_trace: list[str]
    errors: list[str]


@router.post("/tickets", response_model=TicketResponse)
async def process_ticket(request: TicketRequest):
    """Process a Service Desk ticket.

    Receives a user message, routes it through the multi-agent system,
    and returns the response.
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(f"Processing ticket for session {session_id}")
    logger.debug(f"Message: {request.message[:100]}...")

    try:
        # Invoke the Service Desk graph
        result = invoke_service_desk(
            user_input=request.message,
            session_id=session_id,
        )

        return TicketResponse(
            session_id=session_id,
            classification=result.get("classification", "unknown"),
            sub_classification=result.get("sub_classification"),
            response=result.get("response", ""),
            needs_human_escalation=result.get("needs_human_escalation", False),
            escalation_reason=result.get("escalation_reason"),
            confidence_score=result.get("confidence_score", 0.0),
            agent_trace=result.get("agent_trace", []),
            errors=result.get("errors", []),
        )

    except Exception as e:
        logger.error(f"Error processing ticket: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}",
        )


@router.get("/tickets/{session_id}/status")
async def get_ticket_status(session_id: str):
    """Get status of a ticket by session ID.

    Note: In MVP, this is a placeholder. Full implementation would
    require persistent storage of ticket state.
    """
    return {
        "session_id": session_id,
        "status": "completed",
        "message": "Ticket status tracking requires persistent storage (future phase)",
    }
