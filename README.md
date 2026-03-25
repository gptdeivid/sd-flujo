# Service Desk Flujo

Repositorio de investigacion, planeacion e implementacion de un service desk multiagente construido con `LangGraph`, `FastAPI` y `Gemini`.

La idea central del proyecto es correcta: no resolver soporte con un solo prompt, sino con un flujo determinista que clasifica solicitudes, delega a especialistas y deja una ruta clara para escalar a integraciones reales.

## Que hay en este repo

- `servicedesk-agent/`: MVP funcional del agente de service desk.
- `servicedesk-agent/docs-by-claude-code/`: arquitectura, decision log, guia de implementacion y roadmap generados durante el trabajo con Claude Code.
- `codex/`: analisis y planes de construccion hechos en esta sesion.
- `Claude Research- Service Desk.md`, `GDR- ServiceDeskLangchain.md`, `PPXL Deep resaearch - Serv.md`, `PPXL LABS - Service desk.md`: investigaciones base que justifican stack, patrones y direccion tecnica.

## Lectura del proyecto

Este repo ya no esta en etapa de idea. Tiene dos capas claras:

1. `Investigacion`: compara `LangGraph`, `LangChain`, `Google ADK`, `Gemini`, Cloud Run y patrones multi-agent.
2. `Implementacion`: un MVP en `servicedesk-agent/` con router, agentes especializados, API y tests.

La conclusion comun entre los documentos es consistente:

- `LangGraph` es la mejor base para este caso porque el problema requiere routing, estado, branching, trazabilidad y escalamiento.
- `Gemini` entra como motor LLM via `langchain-google-genai`.
- El sistema debe empezar con tools mock y contratos de estado bien definidos, y luego conectar Gmail, Jira, KB, matrices XLS y persistencia.

## Estado actual del MVP

El proyecto implementado en `servicedesk-agent/` ya cubre el esqueleto principal:

- router con clasificacion estructurada
- agentes `it_support`, `billing`, `general_inquiry` y `escalation`
- grafo principal en `LangGraph`
- API REST en `FastAPI`
- tools mock para pruebas y demo
- tests unitarios e integracion basica
- `Dockerfile` y orientacion a `Cloud Run`

Tambien deja preparado el terreno para fases posteriores:

- parsing de email
- validacion de caller
- identificacion bancaria
- clasificacion por taxonomia
- integracion de tickets reales
- persistencia de sesiones

## Arquitectura real hoy

Flujo principal:

```text
User input
  -> FastAPI
  -> input_processor
  -> router
  -> specialized agent
  -> response_formatter
  -> escalation_handler (si aplica)
  -> response JSON
```

Categorias principales de routing:

- `it_support`
- `billing`
- `general_inquiry`
- `escalation`
- `unknown`

Decisiones de diseno visibles en el codigo:

- estado central en `TypedDict`
- reducers para listas y mensajes
- edge routing explicito
- agentes encapsulados por clase
- tools simuladas para no bloquear el MVP por dependencias externas

## Lo que esta bien resuelto

- La separacion de responsabilidades es buena: `state`, `agents`, `graph`, `api`, `llm`, `tools`, `config`.
- El MVP esta pensado para evolucionar, no para rehacerse.
- El roadmap esta ya insinuado en los stubs del estado y de los agentes.
- Hay disciplina tecnica: `pyproject.toml`, tests, settings, Docker y `CLAUDE.md`.

## Lo que todavia esta incompleto

- Las tools son mock; no hay integracion real con ITSM, Gmail, KB ni sistemas internos.
- No hay persistencia real de sesiones o tickets.
- No hay autenticacion.
- El endpoint de status es placeholder.
- Hay drift documental menor: `servicedesk-agent/CLAUDE.md` habla de Gemini 3 Flash, pero `servicedesk-agent/src/config/settings.py` hoy arranca con `gemini-2.0-flash`.

Ese ultimo punto no rompe el proyecto, pero conviene alinear documentacion y configuracion antes de endurecerlo.

## Estructura recomendada de lectura

Si alguien nuevo entra al repo, el orden correcto es:

1. este `README.md`
2. `servicedesk-agent/CLAUDE.md`
3. `servicedesk-agent/docs-by-claude-code/ARCHITECTURE.md`
4. `servicedesk-agent/docs-by-claude-code/DECISION_LOG.md`
5. `servicedesk-agent/docs-by-claude-code/NEXT_STEPS.md`
6. `servicedesk-agent/src/graph/service_desk_graph.py`
7. `servicedesk-agent/src/state/base_state.py`

## Como correr el MVP

```bash
cd servicedesk-agent
uv sync
copy .env.example .env
uv run uvicorn src.api.main:app --reload
```

Variables de entorno esperadas:

```bash
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_GENAI_USE_VERTEXAI=true
VERTEXAI_LOCATION=us-central1

# alternativa para desarrollo local
GOOGLE_API_KEY=your-api-key
```

Pruebas:

```bash
cd servicedesk-agent
uv run pytest
```

Script local:

```bash
cd servicedesk-agent
uv run python scripts/run_local.py
```

Request de ejemplo:

```bash
curl -X POST http://localhost:8000/api/v1/tickets ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"No puedo conectarme a la VPN\"}"
```

## Como usar Claude Code bien en este repo

La documentacion oficial de Claude Code encaja bastante bien con este proyecto. Lo importante no es solo "usar Claude", sino estructurar el repo para que Claude no improvise de mas.

### 1. `CLAUDE.md` es parte del producto, no decoracion

Claude Code carga `CLAUDE.md` al inicio de cada sesion para aplicar instrucciones persistentes del proyecto. La recomendacion oficial es mantener esos archivos concretos, bien estructurados y preferentemente por debajo de 200 lineas; si crecen, dividirlos con imports o `.claude/rules/`.

Aplicacion directa aqui:

- mantener `servicedesk-agent/CLAUDE.md` como contrato vivo de arquitectura
- mover reglas grandes a `.claude/rules/` cuando el proyecto crezca
- usar imports para traer contexto estable, por ejemplo `@README.md` o guias internas

### 2. `/init` debe usarse para refinar, no para empezar de cero cada vez

La doc oficial dice que `/init` genera o mejora `CLAUDE.md`, y en el flujo nuevo incluso puede proponer `CLAUDE.md`, hooks y skills. En este repo ya existe `CLAUDE.md`, asi que el uso correcto seria pedirle mejoras puntuales y no regenerar el proyecto a ciegas.

### 3. Plan Mode es especialmente util aqui

Este repo tiene routing, estado y decisiones de arquitectura; no conviene editarlo a golpes. Claude Code recomienda usar Plan Mode para cambios complejos antes de tocar codigo. Para este proyecto, eso aplica sobre todo a:

- cambios en el grafo
- cambios en el estado central
- integraciones reales
- persistencia
- seguridad y permisos

### 4. `.claude/settings.json` deberia endurecer el repo

La documentacion oficial permite configurar permisos, `additionalDirectories` y modo por defecto. Este repo deberia usar eso para negar acceso accidental a secretos y endurecer el flujo de trabajo.

Minimo recomendado cuando se agregue `.claude/settings.json`:

- negar lectura de `.env`
- negar lectura de carpetas de secretos
- permitir solo los directorios necesarios
- definir un modo de permisos consistente para el equipo

### 5. Hooks son buena siguiente capa

Claude Code soporta hooks en `~/.claude/settings.json`, `.claude/settings.json` y `.claude/settings.local.json`. Para este repo tienen mucho sentido en eventos como `PreToolUse`, `PostToolUse` y `Stop`.

Usos recomendados aqui:

- correr lint o tests despues de cambios relevantes
- bloquear operaciones peligrosas sobre secretos
- registrar cambios en configuracion
- validar que no se lean archivos sensibles

### 6. MCP compartido debe vivir en `.mcp.json`

La doc oficial indica que los MCP project-scoped se guardan en `.mcp.json` y estan pensados para compartirse por control de versiones. Para este repo eso es util cuando el equipo quiera conectar docs, KB o sistemas internos de forma estable.

Buenos candidatos futuros:

- doc servers internos
- knowledge base corporativa
- Jira o ITSM
- catalogos operativos

### 7. Skills especificos tendrian mucho valor

Claude Code ya no separa tanto comandos custom y skills: ambos pueden vivir en `.claude/skills/` con `SKILL.md`. Este repo se beneficiaria de skills como:

- `review-graph`: revisar cambios en `state` + `graph`
- `service-desk-test`: correr suite minima y resumir fallos
- `ticket-taxonomy`: mantener taxonomias y ejemplos de clasificacion
- `cloud-run-release`: checklist de release

## Roadmap tecnico realista

Orden pragmatica para seguir:

1. alinear docs y configuracion actual
2. endurecer `CLAUDE.md`
3. agregar `.claude/settings.json`
4. agregar hooks basicos
5. conectar persistencia de sesiones
6. integrar primer sistema real, idealmente tickets o knowledge base
7. agregar evaluacion de routing con casos anonimizados

## Documentos clave del repo

- `servicedesk-agent/README.md`: README operativo del subproyecto
- `servicedesk-agent/CLAUDE.md`: contrato de trabajo para Claude Code
- `servicedesk-agent/docs-by-claude-code/ARCHITECTURE.md`: arquitectura tecnica
- `servicedesk-agent/docs-by-claude-code/DECISION_LOG.md`: decisiones arquitectonicas
- `servicedesk-agent/docs-by-claude-code/IMPLEMENTATION_GUIDE.md`: guia detallada de implementacion
- `servicedesk-agent/docs-by-claude-code/NEXT_STEPS.md`: roadmap posterior al MVP
- `codex/PLAN-analisis-servicedesk.md`: lectura sintetica del problema
- `codex/PLAN-coding-servicedesk.md`: plan tecnico de codificacion

## Referencias oficiales de Claude Code que guian este repo

- Memory / `CLAUDE.md`: https://code.claude.com/docs/en/memory
- Settings: https://code.claude.com/docs/en/settings
- Hooks: https://code.claude.com/docs/en/hooks
- MCP: https://code.claude.com/docs/en/mcp
- Skills y slash-driven workflows: https://code.claude.com/docs/en/slash-commands

En resumen: este repo ya tiene una direccion tecnica valida. Lo mas importante ahora no es cambiar de stack, sino terminar de convertir el MVP en una base operable y hacer que `CLAUDE.md`, settings, hooks y MCP trabajen a favor del proyecto en vez de quedarse como piezas sueltas.
