# Decision Log - Service Desk Multi-Agent System

Este documento registra las decisiones arquitectónicas y técnicas clave tomadas durante el desarrollo del sistema, incluyendo el razonamiento detrás de cada una.

---

## Índice de Decisiones

| ID | Decisión | Fecha | Status |
|----|----------|-------|--------|
| ADR-001 | LangGraph sobre alternativas | 2024 | Aceptada |
| ADR-002 | Gemini como LLM principal | 2024 | Aceptada |
| ADR-003 | TypedDict vs Pydantic para State | 2024 | Aceptada |
| ADR-004 | Estructura de agentes con herencia | 2024 | Aceptada |
| ADR-005 | Mock tools para MVP | 2024 | Aceptada |
| ADR-006 | FastAPI sobre alternatives | 2024 | Aceptada |
| ADR-007 | Cloud Run para deployment | 2024 | Aceptada |
| ADR-008 | Stub agents para futuras fases | 2024 | Aceptada |

---

## ADR-001: LangGraph como Framework de Orquestación

### Contexto
Necesitábamos un framework para orquestar múltiples agentes de IA que pudieran colaborar en la resolución de tickets de service desk.

### Opciones Consideradas

| Opción | Pros | Contras |
|--------|------|---------|
| **LangGraph** | Grafos determinísticos, trazabilidad, integración LangChain | Curva de aprendizaje |
| LangChain Agents | Simple, documentado | Menos control sobre flujo |
| AutoGen | Multi-agent nativo | Más complejo, menos control |
| CrewAI | Alto nivel, fácil | Menos flexible, abstracción excesiva |
| Custom (sin framework) | Control total | Reinventar la rueda |

### Decisión
**LangGraph** por las siguientes razones:

1. **Grafos determinísticos**: Podemos definir exactamente qué agente procesa qué y cuándo
2. **State management**: TypedDict con reducers para estado compartido
3. **Trazabilidad**: `agent_trace` nos permite ver exactamente qué pasó
4. **Conditional edges**: Routing flexible basado en clasificación
5. **Integración nativa**: Funciona perfectamente con LangChain y Gemini
6. **Producción-ready**: Usado en producción por Anthropic, LangChain Inc.

### Consecuencias
- Positivas: Control granular, debugging fácil, flujos predecibles
- Negativas: Más código boilerplate que alternativas de alto nivel

---

## ADR-002: Google Gemini como LLM Principal

### Contexto
El sistema requiere un LLM capaz de clasificación, generación de respuestas, y uso de tools.

### Opciones Consideradas

| Opción | Pros | Contras |
|--------|------|---------|
| **Gemini 2.0 Flash** | Rápido, económico, Vertex AI nativo | Más nuevo |
| GPT-4 | Probado, documentado | Costo, no nativo en GCP |
| Claude | Excelente razonamiento | No nativo en GCP |
| Llama 3 | Open source | Requiere hosting propio |
| Gemini Pro | Más capaz | Más lento y costoso |

### Decisión
**Gemini 2.0 Flash** via Vertex AI:

1. **Costo-efectivo**: Más barato que GPT-4 para casos de uso similares
2. **Velocidad**: Flash es optimizado para latencia baja
3. **Integración GCP**: Vertex AI nativo, mismo ecosistema que Cloud Run
4. **Structured output**: Soporte excelente para Pydantic schemas
5. **Tool calling**: Función nativa bien implementada

### Configuración Específica

```python
# Nota importante: Gemini 3.0+ requiere temperature=1.0
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=1.0,  # Requerido
    google_api_key=settings.google_api_key
)
```

### Consecuencias
- Positivas: Bajo costo, baja latencia, integración nativa
- Negativas: Documentación menos extensa que OpenAI

---

## ADR-003: TypedDict vs Pydantic para State

### Contexto
LangGraph requiere una definición de estado. Debíamos elegir entre TypedDict y Pydantic BaseModel.

### Opciones Consideradas

| Opción | Pros | Contras |
|--------|------|---------|
| **TypedDict** | Recomendado por LangGraph, reducers nativos | Menos validación runtime |
| Pydantic BaseModel | Validación, serialización | Overhead, reducers manuales |

### Decisión
**TypedDict con Annotated reducers**:

```python
class ServiceDeskState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    agent_trace: Annotated[list[str], append_to_list]
```

### Razonamiento
1. **Patrón oficial**: LangGraph recomienda TypedDict
2. **Reducers nativos**: `Annotated` permite acumulación automática
3. **total=False**: Campos opcionales sin defaults
4. **Performance**: Menos overhead que Pydantic para estado interno

### Consecuencias
- Positivas: Código idiomático, reducers funcionan perfectamente
- Negativas: Validación de tipos solo en tiempo de desarrollo

---

## ADR-004: Estructura de Agentes con Herencia

### Contexto
Necesitábamos una forma consistente de implementar múltiples agentes con comportamiento compartido.

### Opciones Consideradas

| Opción | Pros | Contras |
|--------|------|---------|
| **Clase base abstracta** | Contrato claro, reutilización | Más código |
| Funciones independientes | Simple | Duplicación, inconsistencia |
| Composición | Flexible | Más complejo |
| Protocolo/Interface | Type-safe | Menos código compartido |

### Decisión
**Clase base abstracta `BaseServiceDeskAgent`**:

```python
class BaseServiceDeskAgent(ABC):
    def __init__(self):
        self.gemini_client = GeminiClient()

    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @abstractmethod
    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        pass

    def _update_trace(self, state: ServiceDeskState) -> list[str]:
        return [self.agent_name]
```

### Razonamiento
1. **Contrato explícito**: Todos los agentes implementan lo mismo
2. **Código compartido**: `_update_trace`, `_handle_error` en base
3. **Extensibilidad**: Fácil agregar nuevos agentes
4. **Testing**: Mock de agente base para tests unitarios

### Consecuencias
- Positivas: Consistencia, mantenibilidad, testing fácil
- Negativas: Boilerplate inicial

---

## ADR-005: Mock Tools para MVP

### Contexto
El MVP necesita demostrar funcionalidad sin integraciones reales (APIs de monitoreo, sistemas de facturación, etc.).

### Decisión
**Tools con respuestas simuladas** que mantienen la interfaz correcta:

```python
@tool
def check_system_status(system_name: str) -> str:
    """Check the status of a company system.

    Args:
        system_name: Name of the system to check (e.g., 'vpn', 'email', 'erp')

    Returns:
        Current status of the system
    """
    statuses = {
        "vpn": "VPN is operational. Current load: 45%",
        "email": "Email servers running normally",
        "erp": "ERP system maintenance scheduled for tonight",
    }
    return statuses.get(system_name.lower(), f"System '{system_name}' status: Unknown")
```

### Razonamiento
1. **Desarrollo aislado**: No dependemos de sistemas externos
2. **Testing confiable**: Respuestas predecibles
3. **Interfaz correcta**: Docstrings que el LLM puede usar
4. **Migración fácil**: Solo cambiar implementación, no interfaz

### Estrategia de Migración

```python
# Actual (mock)
def check_system_status(system_name: str) -> str:
    return mock_statuses.get(system_name)

# Futuro (real)
def check_system_status(system_name: str) -> str:
    return monitoring_api.get_status(system_name)
```

### Consecuencias
- Positivas: MVP funcional rápido, tests predecibles
- Negativas: No prueba integración real

---

## ADR-006: FastAPI para API REST

### Contexto
Necesitamos exponer el sistema como API REST para integración con otros sistemas.

### Opciones Consideradas

| Opción | Pros | Contras |
|--------|------|---------|
| **FastAPI** | Async, Pydantic, OpenAPI automático | - |
| Flask | Simple, conocido | Sync, menos moderno |
| Django REST | Completo | Overkill para este caso |
| gRPC | Performance | Menos universal |

### Decisión
**FastAPI** sin dudas:

1. **Async nativo**: LLM calls son I/O bound
2. **Pydantic integrado**: Ya lo usamos para schemas
3. **OpenAPI automático**: Documentación gratis
4. **Cloud Run compatible**: Perfecto con uvicorn

### Consecuencias
- Positivas: API moderna, documentada, eficiente
- Negativas: Ninguna significativa

---

## ADR-007: Google Cloud Run para Deployment

### Contexto
Necesitamos una plataforma de deployment que escale automáticamente y sea costo-efectiva.

### Opciones Consideradas

| Opción | Pros | Contras |
|--------|------|---------|
| **Cloud Run** | Serverless, auto-scale, integración Vertex AI | Cold starts |
| GKE | Control total | Overhead operacional |
| Cloud Functions | Simple | Límites de timeout |
| Compute Engine | Control | Gestión manual |
| App Engine | PaaS | Menos flexible |

### Decisión
**Cloud Run**:

```yaml
# Beneficios clave:
- Scale to zero (costo)
- Auto-scaling (tráfico variable)
- Mismo proyecto que Vertex AI
- Container-based (portable)
- Health checks nativos
```

### Configuración

```dockerfile
# Multi-stage build para imagen optimizada
FROM python:3.12-slim AS runtime
USER appuser  # Non-root
ENV PORT=8080
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Consecuencias
- Positivas: Costo eficiente, escalable, integrado
- Negativas: Cold starts (mitigable con min-instances)

---

## ADR-008: Stub Agents para Futuras Fases

### Contexto
Sabemos que el sistema necesitará agentes adicionales (Gmail, Jira, validación XLS), pero no son parte del MVP.

### Decisión
**Crear agentes stub** con interfaz completa pero implementación vacía:

```python
# src/agents/stubs/email_parser_agent.py
class EmailParserAgent(BaseServiceDeskAgent):
    """Agent for parsing incoming emails.

    Future integration: Gmail API
    """

    @property
    def agent_name(self) -> str:
        return "email_parser"

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        # Stub implementation
        return {
            "errors": ["EmailParserAgent not yet implemented"],
            "agent_trace": [self.agent_name],
        }
```

### Razonamiento
1. **Arquitectura definida**: Sabemos cómo encajarán
2. **Contratos claros**: Interfaces ya definidas
3. **Planificación**: Documenta futuras capacidades
4. **Testing**: Podemos escribir tests que fallarán hasta implementar

### Agentes Stub Creados
- `EmailParserAgent`: Parseo de emails (Gmail API)
- `CallerValidatorAgent`: Validación vs matriz XLS
- `BankIdentifierAgent`: Identificación de bancos
- `ProblemClassifierAgent`: Clasificación por categorías XLS

### Consecuencias
- Positivas: Roadmap claro, arquitectura extensible
- Negativas: Código "muerto" temporal

---

## Decisiones Pendientes

### P-001: Persistencia de Sesiones
- **Contexto**: Actualmente no hay persistencia entre requests
- **Opciones**: Redis, Firestore, PostgreSQL
- **Cuando decidir**: Al implementar memoria de conversación

### P-002: Mecanismo de Streaming
- **Contexto**: Respuestas actualmente son síncronas
- **Opciones**: SSE, WebSockets, HTTP streaming
- **Cuando decidir**: Al requerir respuestas en tiempo real

### P-003: Autenticación y Autorización
- **Contexto**: MVP no tiene auth
- **Opciones**: JWT, OAuth2, API Keys, IAM
- **Cuando decidir**: Antes de producción

### P-004: Estrategia de Logging y Monitoring
- **Contexto**: Logging básico actual
- **Opciones**: Cloud Logging, Datadog, custom
- **Cuando decidir**: Pre-producción

---

## Lecciones Aprendidas

### 1. Temperature en Gemini
```python
# Gemini 3.0+ requiere temperature=1.0
# Esto fue un descubrimiento durante desarrollo
```

### 2. Reducers en LangGraph
```python
# Los reducers son fundamentales para estado acumulativo
# Sin ellos, cada nodo sobrescribiría el estado anterior
```

### 3. Structured Output vs JSON Mode
```python
# Structured output con Pydantic es más confiable
# que pedir JSON y parsearlo manualmente
```

### 4. Tools Docstrings
```python
# El LLM usa los docstrings para decidir qué tool usar
# Docstrings pobres = decisiones pobres del LLM
```
