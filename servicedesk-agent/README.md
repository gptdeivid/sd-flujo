# Service Desk Multi-Agent System

Sistema de Service Desk empresarial basado en múltiples agentes usando LangGraph y Google Gemini.

## Características

- **Router inteligente**: Clasifica automáticamente las solicitudes
- **Agentes especializados**: IT Support, Billing, General Inquiry, Escalation
- **Orquestación con LangGraph**: Flujos de trabajo determinísticos y trazables
- **API REST**: FastAPI para integración con otros sistemas
- **Cloud Ready**: Configurado para Google Cloud Run

## Arquitectura

```
User Request → Input Node → Router Agent
                                 │
                 ┌───────────────┼───────────────┐
                 ↓               ↓               ↓
           IT Support      Billing        General Inquiry
                 │               │               │
                 └───────────────┴───────────────┘
                                 │
                                 ↓
                     Response Formatter → END
```

## Requisitos

- Python 3.12+
- Cuenta de Google Cloud con Vertex AI habilitado
- API key de Gemini o credenciales de Vertex AI

## Instalación

```bash
# Clonar repositorio
cd servicedesk-agent

# Instalar dependencias con uv
uv sync

# O con pip
pip install -e .
```

## Configuración

1. Copia `.env.example` a `.env`
2. Configura tus credenciales:

```bash
# Para Vertex AI (recomendado en producción)
GOOGLE_CLOUD_PROJECT=tu-proyecto
GOOGLE_GENAI_USE_VERTEXAI=true
VERTEXAI_LOCATION=us-central1

# O para API de Gemini directa (desarrollo)
GOOGLE_API_KEY=tu-api-key
```

## Uso

### Servidor local

```bash
uv run uvicorn src.api.main:app --reload
```

### Script interactivo

```bash
uv run python scripts/run_local.py
```

### API

```bash
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d '{"message": "No puedo conectarme a la VPN"}'
```

## Tests

```bash
# Todos los tests
uv run pytest

# Solo unit tests
uv run pytest tests/unit/

# Con coverage
uv run pytest --cov=src
```

## Deployment

### Docker

```bash
docker build -t servicedesk-agent .
docker run -p 8080:8080 --env-file .env servicedesk-agent
```

### Cloud Run

```bash
gcloud run deploy servicedesk-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Estructura del Proyecto

```
servicedesk-agent/
├── src/
│   ├── config/          # Configuración y prompts
│   ├── state/           # TypedDict y enums
│   ├── agents/          # Agentes especializados
│   ├── tools/           # Tools para agentes
│   ├── graph/           # LangGraph orchestration
│   ├── llm/             # Gemini client
│   └── api/             # FastAPI endpoints
├── tests/
└── scripts/
```

## Fases Futuras

- [ ] Integración con Gmail API
- [ ] Integración con Jira
- [ ] Validación de callers (matriz XLS)
- [ ] Clasificación por categorías (XLS)
- [ ] Respuestas automáticas

## Licencia

Privado - Uso interno empresarial
