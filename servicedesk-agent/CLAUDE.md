# Service Desk Multi-Agent System

Sistema de Service Desk empresarial interno basado en LangGraph y Gemini 3 Flash.

## Comandos

- `uv sync`: Instalar dependencias
- `uv run pytest`: Ejecutar tests
- `uv run pytest -m integration`: Solo tests de integración
- `uv run ruff check src/`: Linting
- `uv run mypy src/`: Type checking
- `uv run uvicorn src.api.main:app --reload`: Servidor local

## Arquitectura

### Stack
- Python 3.12+
- LangGraph 0.2+ para orquestación
- langchain-google-genai 2.0+ (SDK consolidado google-genai)
- Gemini 3 Flash via Vertex AI
- FastAPI para API REST
- Cloud Run para deployment

### Patrón de Diseño
- **Supervisor con sub-agentes como tools**: Patrón recomendado por LangGraph 2026
- **StateGraph con TypedDict**: Para state management explícito
- **Clases para nodos**: Encapsulación OOP de lógica de agentes
- **Separación de concerns**: API / Nodes / State / Graph en módulos separados

### Estructura de Estado
El estado principal `ServiceDeskState` (TypedDict) incluye:
- `messages`: Historial con reducer add_messages
- `classification`: Tipo de solicitud (it_support, billing, etc.)
- `response`: Respuesta generada
- `needs_human_escalation`: Flag de escalamiento
- Campos stub para futuras integraciones (email_components, caller_info, etc.)

## Convenciones

### Código
- Type hints obligatorios en todas las funciones
- Docstrings Google-style para clases y funciones públicas
- Archivos max 300 líneas
- Tests para toda lógica de negocio

### State Management
- NUNCA mutar el estado directamente
- Retornar diccionarios parciales con updates
- Usar reducers explícitos para listas

### LLM Integration
- Usar ChatGoogleGenerativeAI de langchain-google-genai
- Temperature 1.0 para Gemini 3.0+ (requerido)
- Structured outputs con Pydantic para clasificación

### Agentes
- Heredar de BaseServiceDeskAgent
- Implementar método `process(state) -> dict`
- Tools con @tool decorator y docstrings completos

## Prohibiciones

- NO usar google-ai-generativelanguage (deprecated)
- NO usar ChatVertexAI (migrado a ChatGoogleGenerativeAI)
- NO hardcodear API keys
- NO crear archivos mayores a 300 líneas
- NO commitear sin pasar tests y type checks

## Integraciones Futuras (Stubs)

Los siguientes agentes están definidos como stubs:
- EmailParserAgent: Integración Gmail
- CallerValidatorAgent: Matriz de callers en XLS
- BankIdentifierAgent: Identificación por firmas/dominio
- ProblemClassifierAgent: Categorías de XLS

## Testing

- pytest para unit tests
- pytest-asyncio para tests async
- pytest markers: `@pytest.mark.integration`, `@pytest.mark.slow`
- Coverage mínimo: 80%

## Deployment

- Target: Google Cloud Run
- Region: us-central1
- Service Account: servicedesk-agent@PROJECT.iam.gserviceaccount.com
- Roles: aiplatform.user, logging.logWriter

## Flujo del Grafo

```
START → Input Node → Router Agent
                          │
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
    IT Support      Billing        General Inquiry
          │               │               │
          └───────────────┴───────────────┘
                          │
                          ↓
              Response Formatter
                          │
              ┌───────────┴───────────┐
              ↓                       ↓
      needs_human? YES        needs_human? NO
              ↓                       ↓
      Escalation Handler            END
              ↓
             END
```
