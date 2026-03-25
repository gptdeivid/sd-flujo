# Coding plan - Service Desk multiagente

## Objetivo

Implementar un MVP de service desk multiagente con arquitectura preparada para evolucionar a produccion, manteniendo control estricto de estado, routing, herramientas e integraciones.

## Principios de implementacion

- `LangGraph` como orquestador principal.
- `langchain-google-genai` como integracion con Gemini.
- Estado tipado desde el inicio.
- Modulos pequenos y responsabilidades separadas.
- Herramientas stub primero; integraciones reales despues.
- Trazabilidad y testing desde la primera version ejecutable.

## Fase 1 - Scaffolding del proyecto

### Objetivo

Crear la base del repositorio sin logica de negocio compleja.

### Tareas

- definir estructura de carpetas
- crear configuracion de entorno
- definir archivo de dependencias
- preparar entrypoint de desarrollo
- preparar configuracion de tests y tipado

### Entregables

- arbol base del proyecto
- configuracion de entorno local
- suite minima de pruebas ejecutable
- convenciones de desarrollo documentadas

## Fase 2 - Modelo de dominio y estado

### Objetivo

Establecer contratos de datos antes de construir nodos y prompts.

### Tareas

- definir entidades del dominio service desk
- definir taxonomia inicial de intents
- definir estado del grafo
- definir esquemas de clasificacion y salida
- separar estado conversacional de estado operacional

### Entregables

- modulo de tipos y estado
- contratos de entrada/salida por nodo
- ejemplos de payloads validos

## Fase 3 - Router y control de flujo

### Objetivo

Construir el flujo principal de enrutamiento.

### Tareas

- implementar nodo router con salida estructurada
- definir politica de confianza y fallback
- mapear intents a agentes
- agregar nodo supervisor o coordinador
- agregar sintetizador final

### Entregables

- grafo base compilable
- routing determinista para casos principales
- manejo explicito de casos ambiguos

## Fase 4 - Agentes especializados

### Objetivo

Agregar especialistas con contexto acotado.

### Agentes iniciales

- `triage`
- `tecnico`
- `billing_admin`
- `general_fallback`

### Tareas

- definir prompt y contrato de cada agente
- implementar nodos de agente
- limitar contexto por agente
- normalizar salidas para sintesis posterior

### Entregables

- agentes especializados funcionando con stubs
- respuestas consistentes por dominio

## Fase 5 - Herramientas y adaptadores

### Objetivo

Dar capacidades operativas sin acoplar la logica del grafo a sistemas externos.

### Tareas

- crear interfaces de herramientas
- implementar stubs de ticketing
- implementar stubs de knowledge base
- implementar stubs de estado de servicios
- agregar capa de adaptadores para futuras integraciones reales

### Entregables

- toolkit base por dominio
- interfaces listas para conectar sistemas reales

## Fase 6 - API o interfaz de uso

### Objetivo

Exponer el MVP de forma util para prueba operativa.

### Tareas

- definir contrato de entrada del usuario
- exponer endpoint o CLI de prueba
- serializar respuesta final y metadatos
- incluir trazas y errores legibles

### Entregables

- interfaz minima para probar conversaciones
- formato estable de request/response

## Fase 7 - Testing y evaluacion

### Objetivo

Validar routing, estabilidad y comportamiento basico.

### Tareas

- pruebas unitarias del router
- pruebas de nodos especializados
- pruebas del grafo end to end
- dataset base de tickets anonimizados o sinteticos
- medicion de precision de routing y tasa de fallback

### Entregables

- suite de pruebas del MVP
- baseline de calidad del routing

## Fase 8 - Observabilidad y endurecimiento

### Objetivo

Preparar la base para operacion real.

### Tareas

- integrar tracing
- registrar decisiones de routing
- agregar timeouts y manejo de errores
- controlar costo y latencia por llamada
- preparar configuracion de despliegue

### Entregables

- observabilidad minima operativa
- lineamientos de despliegue inicial

## Estructura sugerida del codigo

```text
src/
  app/
  domain/
  graph/
  agents/
  tools/
  integrations/
  schemas/
  config/
  api/
  observability/
tests/
```

## Orden recomendado de implementacion

1. scaffolding
2. dominio y estado
3. router
4. agentes
5. herramientas stub
6. interfaz de prueba
7. tests
8. observabilidad
9. integraciones reales

## Definition of done del MVP

- enruta correctamente los casos principales
- tiene al menos 3 especialistas y 1 fallback
- usa estado tipado
- corre con herramientas stub
- expone una interfaz de prueba
- tiene pruebas base de routing y flujo
- deja lista la arquitectura para conectar ITSM y KB reales
