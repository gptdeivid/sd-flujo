# Próximos Pasos y Roadmap

Este documento detalla las fases de desarrollo recomendadas después del MVP, priorizadas por valor de negocio e impacto técnico.

---

## Estado Actual (MVP Completado)

### Lo que tenemos:
- Router inteligente con clasificación por Gemini
- 4 agentes especializados funcionales (IT, Billing, General, Escalation)
- Tools mock para demostración
- API REST con FastAPI
- Dockerfile para Cloud Run
- Tests unitarios e integración
- Documentación completa

### Lo que falta:
- Integraciones reales (Gmail, Jira, sistemas internos)
- Persistencia de sesiones
- Autenticación
- Monitoring en producción

---

## Roadmap de Fases

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ROADMAP DE DESARROLLO                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  COMPLETADO                                                             │
│  ═══════════                                                            │
│  [✓] Fase 0: MVP Core                                                   │
│      └── Router + 4 Agentes + API + Docker                             │
│                                                                         │
│  CORTO PLAZO (1-2 meses)                                               │
│  ══════════════════════                                                 │
│  [ ] Fase 1: Producción Básica                                         │
│      ├── Deployment Cloud Run                                          │
│      ├── Secrets Management                                            │
│      ├── Logging & Monitoring básico                                   │
│      └── Health checks mejorados                                       │
│                                                                         │
│  [ ] Fase 2: Persistencia y Sesiones                                   │
│      ├── Redis/Firestore para sesiones                                 │
│      ├── Historial de conversaciones                                   │
│      └── LangGraph Checkpointing                                       │
│                                                                         │
│  MEDIANO PLAZO (3-4 meses)                                             │
│  ═════════════════════════                                              │
│  [ ] Fase 3: Integración Gmail                                         │
│      ├── Gmail API para lectura de emails                              │
│      ├── EmailParserAgent funcional                                    │
│      └── Procesamiento automático de inbox                             │
│                                                                         │
│  [ ] Fase 4: Integración Jira                                          │
│      ├── Crear tickets automáticamente                                 │
│      ├── Actualizar tickets existentes                                 │
│      └── Consultar estado de tickets                                   │
│                                                                         │
│  LARGO PLAZO (5-6 meses)                                               │
│  ════════════════════════                                               │
│  [ ] Fase 5: Validación de Callers (XLS)                               │
│      ├── CallerValidatorAgent funcional                                │
│      ├── Matriz de autorizaciones                                      │
│      └── Verificación de permisos                                      │
│                                                                         │
│  [ ] Fase 6: Clasificación por Categorías (XLS)                        │
│      ├── ProblemClassifierAgent funcional                              │
│      ├── Taxonomía de problemas                                        │
│      └── SLAs por categoría                                            │
│                                                                         │
│  FUTURO                                                                 │
│  ══════                                                                 │
│  [ ] Fase 7: Respuestas Automáticas                                    │
│  [ ] Fase 8: Dashboard Analytics                                       │
│  [ ] Fase 9: Multitenancy                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Fase 1: Producción Básica

### Objetivo
Llevar el MVP a un estado deployable en producción con mínima infraestructura.

### Tareas

#### 1.1 Deployment Cloud Run

```bash
# Configurar proyecto GCP
gcloud config set project YOUR_PROJECT_ID

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Build y push imagen
gcloud builds submit --tag gcr.io/YOUR_PROJECT/servicedesk-agent

# Deploy
gcloud run deploy servicedesk-agent \
  --image gcr.io/YOUR_PROJECT/servicedesk-agent \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=YOUR_PROJECT" \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=true"
```

#### 1.2 Secrets Management

```python
# src/config/settings.py - Actualizar para Cloud Run
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    """Fetch secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")
```

#### 1.3 Logging Estructurado

```python
# src/config/logging.py
import logging
import json
from datetime import datetime

class CloudRunFormatter(logging.Formatter):
    """JSON formatter for Cloud Run logs."""

    def format(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat(),
            "component": record.name,
        }
        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id
        if hasattr(record, 'classification'):
            log_entry["classification"] = record.classification
        return json.dumps(log_entry)
```

### Entregables
- [ ] Service desplegado en Cloud Run
- [ ] Secrets en Secret Manager
- [ ] Logs estructurados en Cloud Logging
- [ ] Alertas básicas configuradas

### Estimación de Esfuerzo
- Desarrollo: 3-5 días
- Testing/QA: 2 días
- Documentación: 1 día

---

## Fase 2: Persistencia y Sesiones

### Objetivo
Permitir conversaciones con contexto histórico y recuperación de estado.

### Arquitectura Propuesta

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Cloud Run   │────▶│    Redis      │────▶│   Firestore   │
│   (API)       │     │  (Sesiones)   │     │  (Histórico)  │
└───────────────┘     └───────────────┘     └───────────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │ LangGraph         │
                    │ Checkpointer      │
                    └───────────────────┘
```

### Tareas

#### 2.1 Redis para Sesiones Activas

```python
# src/persistence/redis_store.py
import redis
from typing import Optional
import json

class SessionStore:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
        self.session_ttl = 3600  # 1 hora

    def save_state(self, session_id: str, state: dict) -> None:
        """Save session state to Redis."""
        self.client.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps(state, default=str)
        )

    def get_state(self, session_id: str) -> Optional[dict]:
        """Retrieve session state."""
        data = self.client.get(f"session:{session_id}")
        return json.loads(data) if data else None

    def delete_session(self, session_id: str) -> None:
        """Delete session."""
        self.client.delete(f"session:{session_id}")
```

#### 2.2 LangGraph Checkpointing

```python
# src/graph/service_desk_graph.py - Actualizar
from langgraph.checkpoint import MemorySaver
# O para producción:
# from langgraph.checkpoint.redis import RedisSaver

def compile_graph_with_memory():
    """Compile graph with checkpointing."""
    graph = StateGraph(ServiceDeskState)
    # ... add nodes and edges ...

    # Add checkpointer
    memory = MemorySaver()  # O RedisSaver para producción
    return graph.compile(checkpointer=memory)
```

#### 2.3 Historial en Firestore

```python
# src/persistence/firestore_store.py
from google.cloud import firestore
from datetime import datetime

class ConversationHistory:
    def __init__(self):
        self.db = firestore.Client()
        self.collection = "conversations"

    def save_conversation(
        self,
        session_id: str,
        messages: list,
        metadata: dict
    ) -> None:
        """Archive conversation to Firestore."""
        doc_ref = self.db.collection(self.collection).document(session_id)
        doc_ref.set({
            "messages": messages,
            "metadata": metadata,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }, merge=True)

    def get_conversation(self, session_id: str) -> Optional[dict]:
        """Retrieve archived conversation."""
        doc = self.db.collection(self.collection).document(session_id).get()
        return doc.to_dict() if doc.exists else None
```

### Entregables
- [ ] Redis configurado para sesiones
- [ ] Checkpointing de LangGraph funcional
- [ ] Histórico en Firestore
- [ ] Tests de persistencia

---

## Fase 3: Integración Gmail

### Objetivo
Procesar emails entrantes automáticamente y responder o crear tickets.

### Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Gmail Inbox   │────▶│   Pub/Sub       │────▶│   Cloud Run     │
│                 │     │   (Push)        │     │   (Processor)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                               ┌────────┴────────┐
                                               ▼                 ▼
                                        ┌───────────┐     ┌───────────┐
                                        │ Email     │     │ Service   │
                                        │ Parser    │     │ Desk      │
                                        │ Agent     │     │ Graph     │
                                        └───────────┘     └───────────┘
```

### Tareas

#### 3.1 Gmail API Setup

```python
# src/integrations/gmail/client.py
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GmailClient:
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
    ]

    def __init__(self, credentials_path: str):
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=self.SCOPES
        )
        self.service = build('gmail', 'v1', credentials=credentials)

    def get_unread_messages(self, max_results: int = 10) -> list:
        """Fetch unread messages from inbox."""
        results = self.service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=max_results
        ).execute()
        return results.get('messages', [])

    def get_message_details(self, message_id: str) -> dict:
        """Get full message details."""
        return self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

    def send_reply(self, thread_id: str, to: str, subject: str, body: str):
        """Send reply to thread."""
        # Implementation...
```

#### 3.2 Email Parser Agent

```python
# src/agents/stubs/email_parser_agent.py - Implementar
from typing import Any
from pydantic import BaseModel, Field

class EmailComponents(BaseModel):
    """Structured email parsing output."""
    sender_email: str
    sender_name: Optional[str]
    subject: str
    body_text: str
    intent: str
    urgency: Literal["low", "medium", "high", "critical"]
    requires_response: bool

class EmailParserAgent(BaseServiceDeskAgent):
    """Parse incoming emails and extract structured data."""

    def process(self, state: ServiceDeskState) -> dict[str, Any]:
        raw_email = state.get("raw_email", {})

        prompt = f"""Analyze this email and extract key information:

From: {raw_email.get('from')}
Subject: {raw_email.get('subject')}
Body: {raw_email.get('body')}

Extract:
1. Sender information
2. Main intent/request
3. Urgency level
4. Whether it requires a response
"""

        result = self.gemini_client.invoke_with_structured_output(
            prompt=prompt,
            output_schema=EmailComponents,
        )

        return {
            "email_components": result.model_dump(),
            "current_input": result.body_text,  # Para el router
            "agent_trace": [self.agent_name],
        }
```

#### 3.3 Pub/Sub Handler

```python
# src/api/routes/pubsub.py
from fastapi import APIRouter, Request
import base64
import json

router = APIRouter(tags=["pubsub"])

@router.post("/gmail/push")
async def handle_gmail_push(request: Request):
    """Handle Gmail push notification from Pub/Sub."""
    envelope = await request.json()
    message = envelope.get("message", {})

    if message:
        data = base64.b64decode(message.get("data", "")).decode("utf-8")
        notification = json.loads(data)

        # Process new email
        history_id = notification.get("historyId")
        await process_new_emails(history_id)

    return {"status": "ok"}
```

### Entregables
- [ ] Gmail API integrada
- [ ] EmailParserAgent funcional
- [ ] Pub/Sub configurado
- [ ] Respuestas automáticas
- [ ] Tests de integración

---

## Fase 4: Integración Jira

### Objetivo
Crear y gestionar tickets de Jira automáticamente.

### Tareas

#### 4.1 Jira Client

```python
# src/integrations/jira/client.py
from jira import JIRA

class JiraClient:
    def __init__(self):
        self.client = JIRA(
            server=settings.jira_server,
            basic_auth=(settings.jira_email, settings.jira_api_token)
        )

    def create_ticket(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
    ) -> str:
        """Create a new Jira ticket."""
        issue = self.client.create_issue(
            project=project_key,
            summary=summary,
            description=description,
            issuetype={"name": issue_type},
            priority={"name": priority},
        )
        return issue.key

    def add_comment(self, issue_key: str, comment: str) -> None:
        """Add comment to existing ticket."""
        self.client.add_comment(issue_key, comment)

    def update_status(self, issue_key: str, status: str) -> None:
        """Transition ticket to new status."""
        transitions = self.client.transitions(issue_key)
        for t in transitions:
            if t['name'].lower() == status.lower():
                self.client.transition_issue(issue_key, t['id'])
                break
```

#### 4.2 Jira Tools

```python
# src/tools/jira_tools.py
from langchain_core.tools import tool
from src.integrations.jira.client import JiraClient

jira_client = JiraClient()

@tool
def create_jira_ticket(
    summary: str,
    description: str,
    priority: str = "Medium"
) -> str:
    """Create a new Jira ticket for this request.

    Use when the issue cannot be resolved automatically
    and needs to be tracked in Jira.

    Args:
        summary: Brief title for the ticket
        description: Detailed description of the issue
        priority: Priority level (Low, Medium, High, Critical)

    Returns:
        Jira ticket key (e.g., SD-123)
    """
    ticket_key = jira_client.create_ticket(
        project_key="SD",
        summary=summary,
        description=description,
        priority=priority,
    )
    return f"Ticket created: {ticket_key}"


@tool
def get_ticket_status(ticket_key: str) -> str:
    """Get current status of a Jira ticket.

    Args:
        ticket_key: The Jira ticket key (e.g., SD-123)

    Returns:
        Current status and details of the ticket
    """
    issue = jira_client.client.issue(ticket_key)
    return f"Ticket {ticket_key}: {issue.fields.status.name} - {issue.fields.summary}"
```

### Entregables
- [ ] Cliente Jira funcional
- [ ] Tools para agentes
- [ ] Creación automática de tickets
- [ ] Actualización de estado
- [ ] Tests

---

## Fase 5: Validación de Callers (XLS)

### Objetivo
Validar que quien hace la solicitud está autorizado según una matriz Excel.

### Tareas

```python
# src/integrations/excel/caller_validator.py
import pandas as pd

class CallerValidator:
    def __init__(self, matrix_path: str):
        self.matrix = pd.read_excel(matrix_path)
        self._index_by_email()

    def _index_by_email(self):
        self.email_index = self.matrix.set_index('email').to_dict('index')

    def validate_caller(self, email: str, action: str) -> dict:
        """Validate if caller is authorized for action."""
        caller = self.email_index.get(email.lower())

        if not caller:
            return {
                "authorized": False,
                "reason": "Caller not found in authorization matrix"
            }

        if action in caller.get("allowed_actions", []):
            return {
                "authorized": True,
                "caller_name": caller.get("name"),
                "department": caller.get("department"),
            }

        return {
            "authorized": False,
            "reason": f"Action '{action}' not authorized for this caller"
        }
```

---

## Fase 6: Clasificación por Categorías (XLS)

### Objetivo
Clasificar problemas según taxonomía definida en Excel con SLAs asociados.

```python
# src/integrations/excel/problem_classifier.py
import pandas as pd
from typing import Optional

class ProblemTaxonomy:
    def __init__(self, categories_path: str):
        self.categories = pd.read_excel(categories_path)

    def get_category_info(self, category_code: str) -> Optional[dict]:
        """Get category details including SLA."""
        row = self.categories[
            self.categories['code'] == category_code
        ].to_dict('records')

        if row:
            return {
                "code": row[0]['code'],
                "name": row[0]['name'],
                "description": row[0]['description'],
                "sla_hours": row[0]['sla_hours'],
                "escalation_path": row[0]['escalation_path'],
            }
        return None

    def match_category(self, description: str) -> str:
        """Match description to category using keywords."""
        # Implementar matching con keywords o embeddings
        pass
```

---

## Recomendaciones de Priorización

### Alta Prioridad (Hacer Primero)
1. **Fase 1**: Sin esto no hay producción
2. **Fase 2**: Sesiones son críticas para UX
3. **Fase 3**: Gmail es el canal principal de entrada

### Media Prioridad
4. **Fase 4**: Jira mejora trazabilidad
5. **Fase 5**: Validación mejora seguridad

### Baja Prioridad (Puede Esperar)
6. **Fase 6**: Categorización es nice-to-have

---

## Métricas de Éxito

### Por Fase

| Fase | Métrica | Target |
|------|---------|--------|
| 1 | Uptime | 99.5% |
| 2 | Session recovery rate | 95% |
| 3 | Email processing time | < 30s |
| 4 | Ticket creation accuracy | 90% |
| 5 | False rejection rate | < 5% |
| 6 | Classification accuracy | 85% |

### Globales

- **Tiempo de respuesta promedio**: < 10 segundos
- **Tasa de resolución automática**: > 60%
- **Satisfacción de usuario**: > 4.0/5.0
- **Escalamientos innecesarios**: < 15%

---

## Recursos Necesarios

### Infraestructura
- Cloud Run (ya configurado)
- Redis (Memorystore)
- Firestore
- Secret Manager
- Pub/Sub (para Gmail)

### APIs
- Vertex AI (ya configurado)
- Gmail API
- Jira Cloud API

### Humanos
- 1 Backend developer
- 0.5 DevOps engineer
- 0.5 QA engineer

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Gmail API rate limits | Alto | Implementar backoff exponencial |
| Costos de Vertex AI | Medio | Monitoring de uso, cacheo |
| Latencia LLM | Medio | Streaming, timeout handling |
| Datos sensibles en logs | Alto | Redacción automática |
| Cold starts Cloud Run | Bajo | Min instances en prod |
