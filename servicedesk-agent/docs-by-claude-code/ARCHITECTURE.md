# Arquitectura del Sistema Multi-Agent Service Desk

## Visión General

Este documento describe la arquitectura técnica del sistema de Service Desk basado en múltiples agentes inteligentes. El sistema utiliza **LangGraph** para orquestación, **Google Gemini** como LLM, y está diseñado para desplegarse en **Google Cloud Run**.

## Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CAPA DE PRESENTACIÓN                          │
├─────────────────────────────────────────────────────────────────────────┤
│  FastAPI REST API                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │ POST /tickets│  │ GET /health │  │ GET /ready  │                     │
│  └──────┬──────┘  └─────────────┘  └─────────────┘                     │
│         │                                                               │
└─────────┼───────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAPA DE ORQUESTACIÓN                             │
├─────────────────────────────────────────────────────────────────────────┤
│  LangGraph StateGraph                                                   │
│                                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────────────┐   │
│  │  START   │───▶│  Input Node  │───▶│      Router Agent           │   │
│  └──────────┘    └──────────────┘    │  (Clasificación con LLM)    │   │
│                                      └──────────────┬──────────────┘   │
│                                                     │                   │
│                    ┌────────────────┬───────────────┼───────────────┐  │
│                    ▼                ▼               ▼               ▼  │
│            ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌──────┐│
│            │ IT Support │   │  Billing   │   │  General   │   │Escal.││
│            │   Agent    │   │   Agent    │   │  Inquiry   │   │Agent ││
│            └─────┬──────┘   └─────┬──────┘   └─────┬──────┘   └──┬───┘│
│                  │                │                │             │     │
│                  └────────────────┴────────────────┴─────────────┘     │
│                                         │                               │
│                                         ▼                               │
│                              ┌───────────────────┐                      │
│                              │ Response Formatter│                      │
│                              └─────────┬─────────┘                      │
│                                        │                                │
│                          ┌─────────────┴─────────────┐                  │
│                          ▼                           ▼                  │
│                   needs_escalation?           No escalation             │
│                          │                           │                  │
│                          ▼                           ▼                  │
│                  ┌──────────────┐              ┌─────────┐              │
│                  │  Escalation  │              │   END   │              │
│                  │   Handler    │              └─────────┘              │
│                  └──────┬───────┘                                       │
│                         ▼                                               │
│                    ┌─────────┐                                          │
│                    │   END   │                                          │
│                    └─────────┘                                          │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE AGENTES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    BaseServiceDeskAgent                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │ agent_name  │  │ system_prompt│  │ process(state) -> dict │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│           △                                                             │
│           │ extends                                                     │
│  ┌────────┴────────┬─────────────────┬─────────────────┬────────────┐  │
│  │                 │                 │                 │            │  │
│  ▼                 ▼                 ▼                 ▼            ▼  │
│ RouterAgent   ITSupportAgent   BillingAgent   GeneralInquiry  Escalation│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE TOOLS                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  IT Support Tools          Billing Tools           General Tools        │
│  ┌──────────────────┐     ┌──────────────────┐    ┌──────────────────┐ │
│  │check_system_status│     │lookup_invoice    │    │search_faq        │ │
│  │get_troubleshooting│     │check_payment     │    │                  │ │
│  │get_network_status │     │get_billing_info  │    │                  │ │
│  └──────────────────┘     └──────────────────┘    └──────────────────┘ │
│                                                                         │
│  (Actualmente mock - preparados para integraciones reales)              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             CAPA LLM                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    GeminiClient                                  │   │
│  │                                                                  │   │
│  │  Model: gemini-2.0-flash                                        │   │
│  │  Provider: Google Vertex AI / Gemini API                        │   │
│  │  Temperature: 1.0 (requerido por Gemini 3.0+)                   │   │
│  │                                                                  │   │
│  │  Métodos:                                                        │   │
│  │  - get_model() -> ChatGoogleGenerativeAI                        │   │
│  │  - create_agent_with_tools(tools) -> AgentExecutor              │   │
│  │  - invoke_with_structured_output(schema) -> BaseModel           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. ServiceDeskState (Estado Centralizado)

El corazón del sistema es un `TypedDict` que mantiene todo el estado de la conversación:

```python
class ServiceDeskState(TypedDict, total=False):
    # Campos activos MVP
    messages: Annotated[list[BaseMessage], add_messages]
    current_input: str
    classification: Literal["it_support", "billing", "general_inquiry", "escalation", "unknown"]
    sub_classification: Optional[str]
    confidence_score: float
    response: str
    next_agent: Optional[str]
    needs_human_escalation: bool
    escalation_reason: Optional[str]
    agent_trace: Annotated[list[str], append_to_list]
    errors: Annotated[list[str], append_to_list]
    session_id: str
    timestamp: datetime

    # Campos stub (futuras fases)
    email_components: Optional[EmailComponents]
    caller_info: Optional[CallerInfo]
    bank_info: Optional[BankInfo]
    problem_classification: Optional[ProblemClassification]
```

**Características clave:**
- `Annotated` con reducers para acumulación automática
- `add_messages` para historial de conversación
- `append_to_list` para trazas y errores
- Campos stub preparados para futuras integraciones

### 2. Router Agent (Clasificador Inteligente)

El RouterAgent es el punto de entrada crítico que determina qué agente especializado debe manejar cada solicitud:

```python
class ClassificationOutput(BaseModel):
    classification: Literal["it_support", "billing", "general_inquiry", "escalation"]
    sub_classification: Optional[str]
    confidence_score: float
    reasoning: str
```

**Proceso de clasificación:**
1. Recibe el input del usuario
2. Usa structured output de Gemini para clasificar
3. Retorna clasificación con score de confianza
4. El grafo rutea al agente correspondiente

### 3. Agentes Especializados

Cada agente hereda de `BaseServiceDeskAgent` y tiene:
- **System prompt** específico para su dominio
- **Tools** relevantes para su función
- **Lógica de procesamiento** personalizada

| Agente | Dominio | Tools Disponibles |
|--------|---------|-------------------|
| ITSupportAgent | Problemas técnicos | check_system_status, get_troubleshooting_guide, get_network_status |
| BillingAgent | Facturación | lookup_invoice, check_payment_status, get_billing_info |
| GeneralInquiryAgent | FAQs generales | search_faq |
| EscalationAgent | Derivación humana | Ninguno (prepara handoff) |

### 4. LangGraph StateGraph

El grafo define el flujo de ejecución:

```python
graph = StateGraph(ServiceDeskState)

# Nodos
graph.add_node("input", input_node)
graph.add_node("router", router_node)
graph.add_node("it_support", it_support_node)
graph.add_node("billing", billing_node)
graph.add_node("general_inquiry", general_inquiry_node)
graph.add_node("escalation", escalation_node)
graph.add_node("format_response", format_response_node)

# Edges
graph.add_edge(START, "input")
graph.add_edge("input", "router")
graph.add_conditional_edges("router", route_by_classification, {...})
graph.add_conditional_edges("format_response", check_escalation_needed, {...})
```

## Patrones de Diseño Utilizados

### 1. Reducer Pattern (LangGraph)

Los reducers permiten acumular valores en lugar de sobrescribirlos:

```python
from langgraph.graph import add_messages

def append_to_list(current: list, new: list) -> list:
    return current + new

# Uso en state
messages: Annotated[list[BaseMessage], add_messages]
agent_trace: Annotated[list[str], append_to_list]
```

### 2. Factory Pattern (Agentes)

`AgentFactory` centraliza la creación de instancias:

```python
class AgentFactory:
    _instances: dict[str, BaseServiceDeskAgent] = {}

    @classmethod
    def get_agent(cls, agent_type: str) -> BaseServiceDeskAgent:
        if agent_type not in cls._instances:
            cls._instances[agent_type] = cls._create_agent(agent_type)
        return cls._instances[agent_type]
```

### 3. Strategy Pattern (Tools)

Los tools son intercambiables y pueden reemplazarse de mock a implementaciones reales:

```python
# Mock (MVP)
@tool
def check_system_status(system_name: str) -> str:
    """Check status of a system."""
    return f"System {system_name} is operational."

# Real (Futuro)
@tool
def check_system_status(system_name: str) -> str:
    """Check status via monitoring API."""
    return monitoring_client.get_status(system_name)
```

## Flujo de Datos

```
1. Request HTTP POST /api/v1/tickets
   │
   ▼
2. FastAPI valida TicketRequest (Pydantic)
   │
   ▼
3. invoke_service_desk(message, session_id)
   │
   ▼
4. StateGraph.invoke() inicia ejecución
   │
   ▼
5. input_node: Prepara estado inicial
   │
   ▼
6. router_node: Clasifica con LLM
   │
   ▼
7. Conditional edge: Rutea a agente especializado
   │
   ▼
8. Agent node: Procesa con tools si necesario
   │
   ▼
9. format_response_node: Formatea respuesta final
   │
   ▼
10. check_escalation_needed: Verifica si escalar
    │
    ├── Si escalation: escalation_handler_node
    │
    ▼
11. END: Retorna estado final
    │
    ▼
12. FastAPI retorna TicketResponse JSON
```

## Consideraciones de Seguridad

1. **Non-root container**: El Dockerfile usa un usuario `appuser`
2. **Validación de inputs**: Pydantic valida todos los requests
3. **Secrets management**: Variables de entorno para credenciales
4. **No hardcoded credentials**: Uso de `.env` y Cloud Run secrets

## Escalabilidad

- **Stateless**: Cada request es independiente
- **Cloud Run**: Auto-scaling basado en requests
- **Session ID**: Preparado para persistencia de sesiones (futuro)
- **Lazy loading**: Agentes se instancian solo cuando se necesitan

## Métricas y Observabilidad

Campos en el state para tracking:
- `agent_trace`: Lista de agentes que procesaron el request
- `confidence_score`: Confianza de la clasificación
- `timestamp`: Hora de procesamiento
- `errors`: Errores capturados durante ejecución

## Próximos Pasos Arquitectónicos

1. **Persistencia de sesiones**: Redis/Firestore para historial
2. **Checkpointing**: LangGraph checkpointer para recuperación
3. **Streaming**: Respuestas en tiempo real con SSE
4. **Multitenancy**: Separación por organización
5. **Rate limiting**: Control de requests por usuario
