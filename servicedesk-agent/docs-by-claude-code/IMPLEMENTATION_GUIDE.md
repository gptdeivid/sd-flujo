# Guía de Implementación - Service Desk Multi-Agent System

Este documento detalla cómo se construyó el sistema paso a paso, sirviendo como referencia para entender el código y como guía para futuros desarrollos similares.

---

## Fase 1: Setup del Proyecto

### 1.1 Estructura Inicial

```bash
mkdir servicedesk-agent
cd servicedesk-agent

# Crear estructura de carpetas
mkdir -p src/{config,state,agents/stubs,tools/stubs,graph,llm,api/routes}
mkdir -p tests/{unit,integration}
mkdir -p scripts
```

### 1.2 Configuración de Dependencias (pyproject.toml)

```toml
[project]
name = "servicedesk-agent"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "langchain>=0.3",
    "langgraph>=0.2",
    "langchain-google-genai>=2.0",
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "ruff>=0.5",
]
```

**Por qué estas versiones:**
- `langchain>=0.3`: Última versión estable con mejor integración
- `langgraph>=0.2`: StateGraph con reducers mejorados
- `langchain-google-genai>=2.0`: Soporte Gemini 2.0

### 1.3 Variables de Entorno

```bash
# .env.example
GOOGLE_API_KEY=your-api-key-here
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_GENAI_USE_VERTEXAI=false
VERTEXAI_LOCATION=us-central1
LOG_LEVEL=INFO
```

---

## Fase 2: Definición del Estado

### 2.1 Base State (src/state/base_state.py)

El estado es el corazón del sistema. Cada campo fue cuidadosamente diseñado:

```python
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from datetime import datetime
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


def append_to_list(current: list, new: list) -> list:
    """Reducer that appends new items to existing list."""
    if current is None:
        current = []
    if new is None:
        return current
    return current + new


class ServiceDeskState(TypedDict, total=False):
    """Central state for Service Desk workflow.

    Uses TypedDict with total=False for optional fields.
    Annotated types specify reducers for accumulation.
    """

    # === CONVERSACIÓN ===
    messages: Annotated[list[BaseMessage], add_messages]
    """Historial de mensajes. add_messages acumula automáticamente."""

    current_input: str
    """Input actual del usuario (sin procesar)."""

    # === CLASIFICACIÓN ===
    classification: Literal[
        "it_support", "billing", "general_inquiry", "escalation", "unknown"
    ]
    """Categoría asignada por el router."""

    sub_classification: Optional[str]
    """Sub-categoría específica (ej: 'vpn_issues', 'password_reset')."""

    confidence_score: float
    """Confianza de la clasificación (0.0 a 1.0)."""

    # === RESPUESTA ===
    response: str
    """Respuesta final para el usuario."""

    # === ROUTING ===
    next_agent: Optional[str]
    """Próximo agente a ejecutar (override de clasificación)."""

    # === ESCALAMIENTO ===
    needs_human_escalation: bool
    """Flag para derivar a humano."""

    escalation_reason: Optional[str]
    """Razón del escalamiento."""

    # === TRAZABILIDAD ===
    agent_trace: Annotated[list[str], append_to_list]
    """Lista de agentes que procesaron este request."""

    errors: Annotated[list[str], append_to_list]
    """Errores capturados durante procesamiento."""

    # === METADATA ===
    session_id: str
    """ID de sesión para tracking."""

    timestamp: datetime
    """Timestamp de procesamiento."""
```

**Puntos clave:**
1. `total=False`: Permite campos opcionales sin defaults
2. `Annotated` con reducers: Acumulación automática de listas
3. `Literal` para clasificaciones: Type-safe en tiempo de desarrollo

### 2.2 Enums (src/state/enums.py)

```python
from enum import Enum


class TicketCategory(str, Enum):
    """Main ticket categories."""
    IT_SUPPORT = "it_support"
    BILLING = "billing"
    GENERAL_INQUIRY = "general_inquiry"
    ESCALATION = "escalation"
    UNKNOWN = "unknown"


class TicketPriority(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(str, Enum):
    """Available agent types."""
    ROUTER = "router"
    IT_SUPPORT = "it_support"
    BILLING = "billing"
    GENERAL_INQUIRY = "general_inquiry"
    ESCALATION = "escalation"
```

---

## Fase 3: Cliente LLM

### 3.1 Gemini Client (src/llm/gemini_client.py)

```python
from typing import Any, Optional, Type
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from src.config.settings import settings


class GeminiClient:
    """Wrapper for Google Gemini LLM interactions."""

    def __init__(self):
        self._model: Optional[ChatGoogleGenerativeAI] = None

    def get_model(self) -> ChatGoogleGenerativeAI:
        """Get or create the Gemini model instance.

        Uses lazy initialization for efficiency.
        """
        if self._model is None:
            self._model = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                temperature=1.0,  # Required for Gemini 3.0+
                google_api_key=settings.google_api_key,
            )
        return self._model

    def create_agent_with_tools(
        self,
        tools: list[BaseTool],
        system_prompt: str,
    ) -> AgentExecutor:
        """Create an agent executor with specified tools.

        Args:
            tools: List of tools available to the agent
            system_prompt: System prompt for agent behavior

        Returns:
            AgentExecutor ready to process requests
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(
            llm=self.get_model(),
            tools=tools,
            prompt=prompt,
        )

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=settings.debug,
            handle_parsing_errors=True,
        )

    def invoke_with_structured_output(
        self,
        prompt: str,
        output_schema: Type[BaseModel],
    ) -> BaseModel:
        """Invoke LLM with structured output.

        Args:
            prompt: The prompt to send
            output_schema: Pydantic model for output structure

        Returns:
            Parsed response as Pydantic model
        """
        model_with_structure = self.get_model().with_structured_output(
            output_schema
        )
        return model_with_structure.invoke(prompt)
```

**Decisiones de implementación:**

1. **Lazy initialization**: El modelo no se crea hasta que se necesita
2. **with_structured_output**: Usa función nativa de LangChain para outputs Pydantic
3. **temperature=1.0**: Requerido por Gemini 3.0+

---

## Fase 4: Agentes

### 4.1 Base Agent (src/agents/base_agent.py)

```python
from abc import ABC, abstractmethod
from typing import Any

from src.state.base_state import ServiceDeskState
from src.llm.gemini_client import GeminiClient


class BaseServiceDeskAgent(ABC):
    """Abstract base class for all Service Desk agents.

    Provides common functionality and enforces consistent interface.
    """

    def __init__(self):
        self.gemini_client = GeminiClient()

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique identifier for this agent."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining agent behavior."""
        pass

    @abstractmethod
    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Process the current state and return updates.

        Args:
            state: Current workflow state

        Returns:
            Dictionary of state updates (partial state)
        """
        pass

    def _update_trace(self, state: ServiceDeskState) -> list[str]:
        """Add this agent to the trace.

        Returns a list (not appending) because the reducer handles accumulation.
        """
        return [self.agent_name]

    def _handle_error(self, error: Exception) -> dict[str, Any]:
        """Handle errors uniformly across agents."""
        return {
            "errors": [f"{self.agent_name}: {str(error)}"],
            "agent_trace": [self.agent_name],
        }
```

### 4.2 Router Agent (src/agents/router_agent.py)

El Router es el más crítico - determina todo el flujo:

```python
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

from src.agents.base_agent import BaseServiceDeskAgent
from src.state.base_state import ServiceDeskState
from src.config.prompts import ROUTER_SYSTEM_PROMPT


class ClassificationOutput(BaseModel):
    """Structured output for ticket classification."""

    classification: Literal[
        "it_support", "billing", "general_inquiry", "escalation"
    ] = Field(description="The primary category for this request")

    sub_classification: Optional[str] = Field(
        default=None,
        description="More specific sub-category if applicable"
    )

    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this classification (0.0 to 1.0)"
    )

    reasoning: str = Field(
        description="Brief explanation of classification decision"
    )


class RouterAgent(BaseServiceDeskAgent):
    """Agent responsible for classifying incoming requests."""

    @property
    def agent_name(self) -> str:
        return "router"

    @property
    def system_prompt(self) -> str:
        return ROUTER_SYSTEM_PROMPT

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Classify the user's request.

        Uses structured output for reliable classification.
        """
        try:
            user_input = state.get("current_input", "")

            if not user_input:
                return {
                    "classification": "unknown",
                    "confidence_score": 0.0,
                    "errors": ["No input provided"],
                    "agent_trace": self._update_trace(state),
                }

            # Build classification prompt
            prompt = f"""{self.system_prompt}

User Request: {user_input}

Classify this request and provide your reasoning."""

            # Get structured classification
            result = self.gemini_client.invoke_with_structured_output(
                prompt=prompt,
                output_schema=ClassificationOutput,
            )

            return {
                "classification": result.classification,
                "sub_classification": result.sub_classification,
                "confidence_score": result.confidence_score,
                "agent_trace": self._update_trace(state),
            }

        except Exception as e:
            return {
                **self._handle_error(e),
                "classification": "unknown",
                "confidence_score": 0.0,
            }
```

### 4.3 IT Support Agent (src/agents/it_support_agent.py)

Ejemplo de agente con tools:

```python
from typing import Any

from src.agents.base_agent import BaseServiceDeskAgent
from src.state.base_state import ServiceDeskState
from src.config.prompts import IT_SUPPORT_SYSTEM_PROMPT
from src.tools.it_tools import (
    check_system_status,
    get_troubleshooting_guide,
    get_network_status,
)


class ITSupportAgent(BaseServiceDeskAgent):
    """Agent specialized in IT support issues."""

    @property
    def agent_name(self) -> str:
        return "it_support"

    @property
    def system_prompt(self) -> str:
        return IT_SUPPORT_SYSTEM_PROMPT

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        """Process IT support request using available tools."""
        try:
            user_input = state.get("current_input", "")

            # Create agent with IT-specific tools
            agent_executor = self.gemini_client.create_agent_with_tools(
                tools=[
                    check_system_status,
                    get_troubleshooting_guide,
                    get_network_status,
                ],
                system_prompt=self.system_prompt,
            )

            # Execute agent
            result = agent_executor.invoke({"input": user_input})

            return {
                "response": result.get("output", ""),
                "agent_trace": self._update_trace(state),
            }

        except Exception as e:
            return self._handle_error(e)
```

---

## Fase 5: Tools

### 5.1 IT Tools (src/tools/it_tools.py)

```python
from langchain_core.tools import tool


@tool
def check_system_status(system_name: str) -> str:
    """Check the current status of a company system.

    Use this tool when the user asks about system availability,
    outages, or wants to know if a system is working.

    Args:
        system_name: Name of the system to check.
                    Common values: 'vpn', 'email', 'erp', 'intranet', 'wifi'

    Returns:
        Current status information for the requested system
    """
    statuses = {
        "vpn": "VPN service is operational. Current load: 45%. "
               "All regions connected.",
        "email": "Email servers running normally. "
                "No delays in message delivery.",
        "erp": "ERP system is online. "
              "Scheduled maintenance tonight 2:00-4:00 AM.",
        "intranet": "Intranet is accessible. "
                   "Recent updates deployed successfully.",
        "wifi": "Corporate WiFi operational on all floors. "
               "Guest network available.",
    }

    system_lower = system_name.lower()
    if system_lower in statuses:
        return statuses[system_lower]
    return f"System '{system_name}' not found in monitoring. " \
           f"Available systems: {', '.join(statuses.keys())}"


@tool
def get_troubleshooting_guide(issue_type: str) -> str:
    """Get step-by-step troubleshooting guide for common IT issues.

    Use this tool when the user has a technical problem and needs
    guidance on how to resolve it themselves.

    Args:
        issue_type: Type of issue. Common values: 'vpn_connection',
                   'password_reset', 'slow_computer', 'printer',
                   'software_install'

    Returns:
        Step-by-step troubleshooting instructions
    """
    guides = {
        "vpn_connection": """
VPN Connection Troubleshooting:
1. Verify internet connection is working
2. Restart the VPN client application
3. Check if credentials are correct
4. Try disconnecting and reconnecting
5. If issue persists, restart your computer
6. Contact IT if still not working after restart
""",
        "password_reset": """
Password Reset Guide:
1. Go to password.company.com
2. Click "Forgot Password"
3. Enter your email address
4. Check your email for reset link
5. Create new password (min 12 chars, 1 number, 1 symbol)
6. Log in with new password
""",
        "slow_computer": """
Slow Computer Troubleshooting:
1. Restart your computer
2. Close unnecessary applications
3. Check available disk space (need >10% free)
4. Run disk cleanup utility
5. Check for pending Windows updates
6. If issue persists, submit ticket for IT review
""",
    }

    issue_lower = issue_type.lower().replace(" ", "_")
    if issue_lower in guides:
        return guides[issue_lower]
    return f"No guide found for '{issue_type}'. " \
           f"Available guides: {', '.join(guides.keys())}"


@tool
def get_network_status(location: str = "all") -> str:
    """Get network status for office locations.

    Use this tool when user asks about network connectivity,
    internet speed, or office network status.

    Args:
        location: Office location or 'all' for summary.
                 Values: 'headquarters', 'branch_north', 'branch_south', 'all'

    Returns:
        Network status information
    """
    statuses = {
        "headquarters": "HQ Network: Online | Speed: 1Gbps | Latency: 5ms",
        "branch_north": "North Branch: Online | Speed: 500Mbps | Latency: 12ms",
        "branch_south": "South Branch: Online | Speed: 500Mbps | Latency: 15ms",
    }

    if location.lower() == "all":
        return "\n".join([f"- {v}" for v in statuses.values()])

    loc_lower = location.lower().replace(" ", "_")
    if loc_lower in statuses:
        return statuses[loc_lower]
    return f"Location '{location}' not found. " \
           f"Available: {', '.join(statuses.keys())}"
```

**Por qué docstrings detallados:**
El LLM usa los docstrings para decidir qué tool usar. Docstrings pobres = decisiones pobres.

---

## Fase 6: Grafo LangGraph

### 6.1 Nodos (src/graph/nodes.py)

```python
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage

from src.state.base_state import ServiceDeskState
from src.agents.router_agent import RouterAgent
from src.agents.it_support_agent import ITSupportAgent
from src.agents.billing_agent import BillingAgent
from src.agents.general_inquiry_agent import GeneralInquiryAgent
from src.agents.escalation_agent import EscalationAgent


# Lazy initialization of agents
_agents: dict[str, Any] = {}


def _get_agent(agent_type: str):
    """Get or create agent instance (lazy loading)."""
    if agent_type not in _agents:
        agent_classes = {
            "router": RouterAgent,
            "it_support": ITSupportAgent,
            "billing": BillingAgent,
            "general_inquiry": GeneralInquiryAgent,
            "escalation": EscalationAgent,
        }
        _agents[agent_type] = agent_classes[agent_type]()
    return _agents[agent_type]


def input_node(state: ServiceDeskState) -> dict[str, Any]:
    """Initialize state with user input.

    This is the entry point that prepares the state.
    """
    return {
        "messages": [HumanMessage(content=state.get("current_input", ""))],
        "timestamp": datetime.now(),
        "needs_human_escalation": False,
    }


def router_node(state: ServiceDeskState) -> dict[str, Any]:
    """Route request to appropriate agent."""
    agent = _get_agent("router")
    return agent.process(state)


def it_support_node(state: ServiceDeskState) -> dict[str, Any]:
    """Process IT support requests."""
    agent = _get_agent("it_support")
    return agent.process(state)


def billing_node(state: ServiceDeskState) -> dict[str, Any]:
    """Process billing requests."""
    agent = _get_agent("billing")
    return agent.process(state)


def general_inquiry_node(state: ServiceDeskState) -> dict[str, Any]:
    """Process general inquiries."""
    agent = _get_agent("general_inquiry")
    return agent.process(state)


def escalation_node(state: ServiceDeskState) -> dict[str, Any]:
    """Process escalation requests."""
    agent = _get_agent("escalation")
    return agent.process(state)


def format_response_node(state: ServiceDeskState) -> dict[str, Any]:
    """Format final response for user."""
    response = state.get("response", "")

    if not response:
        response = "Lo siento, no pude procesar tu solicitud. " \
                  "Por favor intenta de nuevo o contacta a soporte."

    return {
        "response": response,
        "agent_trace": ["format_response"],
    }


def escalation_handler_node(state: ServiceDeskState) -> dict[str, Any]:
    """Handle cases that need human escalation."""
    current_response = state.get("response", "")
    escalation_notice = (
        "\n\n---\n"
        "Este caso ha sido marcado para revisión humana. "
        "Un agente de soporte se pondrá en contacto contigo pronto."
    )

    return {
        "response": current_response + escalation_notice,
        "agent_trace": ["escalation_handler"],
    }
```

### 6.2 Edges (src/graph/edges.py)

```python
from typing import Literal

from src.state.base_state import ServiceDeskState


def route_by_classification(
    state: ServiceDeskState,
) -> Literal["it_support", "billing", "general_inquiry", "escalation", "unknown"]:
    """Determine next node based on classification.

    Checks next_agent first (for explicit routing),
    then falls back to classification.
    """
    # Check for explicit next agent
    next_agent = state.get("next_agent")
    if next_agent:
        return next_agent

    # Use classification
    classification = state.get("classification", "unknown")

    valid_routes = {"it_support", "billing", "general_inquiry", "escalation"}
    if classification in valid_routes:
        return classification

    return "unknown"


def check_escalation_needed(
    state: ServiceDeskState,
) -> Literal["needs_escalation", "complete"]:
    """Check if case needs human escalation."""
    if state.get("needs_human_escalation", False):
        return "needs_escalation"
    return "complete"
```

### 6.3 Grafo Principal (src/graph/service_desk_graph.py)

```python
from langgraph.graph import StateGraph, START, END

from src.state.base_state import ServiceDeskState
from src.graph.nodes import (
    input_node,
    router_node,
    it_support_node,
    billing_node,
    general_inquiry_node,
    escalation_node,
    format_response_node,
    escalation_handler_node,
)
from src.graph.edges import route_by_classification, check_escalation_needed


def compile_graph() -> StateGraph:
    """Compile the Service Desk workflow graph.

    Returns a compiled graph ready for invocation.
    """
    # Create graph with state schema
    graph = StateGraph(ServiceDeskState)

    # Add all nodes
    graph.add_node("input", input_node)
    graph.add_node("router", router_node)
    graph.add_node("it_support", it_support_node)
    graph.add_node("billing", billing_node)
    graph.add_node("general_inquiry", general_inquiry_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("format_response", format_response_node)
    graph.add_node("escalation_handler", escalation_handler_node)

    # Entry point
    graph.add_edge(START, "input")
    graph.add_edge("input", "router")

    # Conditional routing from router
    graph.add_conditional_edges(
        "router",
        route_by_classification,
        {
            "it_support": "it_support",
            "billing": "billing",
            "general_inquiry": "general_inquiry",
            "escalation": "escalation",
            "unknown": "general_inquiry",  # Fallback
        },
    )

    # All agents go to format_response
    graph.add_edge("it_support", "format_response")
    graph.add_edge("billing", "format_response")
    graph.add_edge("general_inquiry", "format_response")
    graph.add_edge("escalation", "format_response")

    # Check for escalation after formatting
    graph.add_conditional_edges(
        "format_response",
        check_escalation_needed,
        {
            "needs_escalation": "escalation_handler",
            "complete": END,
        },
    )

    # Escalation handler ends the flow
    graph.add_edge("escalation_handler", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def get_graph():
    """Get the compiled graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = compile_graph()
    return _compiled_graph


def invoke_service_desk(
    message: str,
    session_id: str,
) -> dict:
    """Invoke the Service Desk workflow.

    Args:
        message: User's message/request
        session_id: Session identifier for tracking

    Returns:
        Final state dictionary with response
    """
    graph = get_graph()

    initial_state = {
        "current_input": message,
        "session_id": session_id,
    }

    result = graph.invoke(initial_state)
    return result
```

---

## Fase 7: API FastAPI

### 7.1 Main App (src/api/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.tickets import router as tickets_router
from src.api.routes.health import router as health_router
from src.config.settings import settings

app = FastAPI(
    title="Service Desk Multi-Agent API",
    description="API for Service Desk powered by multiple AI agents",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(tickets_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Service Desk Multi-Agent",
        "version": "0.1.0",
        "status": "running",
    }
```

### 7.2 Tickets Router (src/api/routes/tickets.py)

```python
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.graph.service_desk_graph import invoke_service_desk

router = APIRouter(tags=["tickets"])


class TicketRequest(BaseModel):
    """Request model for creating a ticket."""
    message: str = Field(..., min_length=1, description="User's request message")
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for tracking"
    )


class TicketResponse(BaseModel):
    """Response model for ticket processing."""
    session_id: str
    classification: str
    sub_classification: Optional[str] = None
    confidence_score: float
    response: str
    needs_human_escalation: bool
    agent_trace: list[str]


@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(request: TicketRequest):
    """Process a new ticket request.

    The request is classified and routed to the appropriate
    specialized agent for handling.
    """
    try:
        session_id = request.session_id or str(uuid4())

        result = invoke_service_desk(
            message=request.message,
            session_id=session_id,
        )

        return TicketResponse(
            session_id=session_id,
            classification=result.get("classification", "unknown"),
            sub_classification=result.get("sub_classification"),
            confidence_score=result.get("confidence_score", 0.0),
            response=result.get("response", ""),
            needs_human_escalation=result.get("needs_human_escalation", False),
            agent_trace=result.get("agent_trace", []),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )
```

---

## Verificación Final

### Tests Ejecutables

```bash
# Instalar dependencias
uv sync

# Correr tests unitarios
uv run pytest tests/unit/ -v

# Correr tests de integración (requiere LLM)
uv run pytest tests/integration/ -v -m integration

# Coverage
uv run pytest --cov=src --cov-report=html
```

### Test Manual

```bash
# Iniciar servidor
uv run uvicorn src.api.main:app --reload

# Test request
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d '{"message": "No puedo conectarme a la VPN"}'
```

### Resultado Esperado

```json
{
  "session_id": "abc123",
  "classification": "it_support",
  "sub_classification": "vpn_issues",
  "confidence_score": 0.95,
  "response": "Para resolver problemas de VPN...",
  "needs_human_escalation": false,
  "agent_trace": ["router", "it_support", "format_response"]
}
```
