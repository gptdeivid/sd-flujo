# Plan de ejecucion por entregables

## Objetivo

Convertir la investigacion actual en una solucion de service desk multiagente con una ruta clara de construccion, validacion y despliegue, sin comenzar aun implementacion.

## Entregable 1 - Definicion funcional

### Resultado esperado

Un documento que deje cerrados:
- tipos de solicitud soportados por el MVP
- acciones permitidas por cada agente
- criterios de escalamiento a humano
- KPIs de exito del MVP

### Preguntas que debe responder

- Cuales son los 5-10 casos de uso de mayor valor.
- Que casos solo informan y que casos ejecutan acciones.
- Que decisiones requieren aprobacion.
- Que integracion real es la primera prioridad.

## Entregable 2 - Diseno de arquitectura

### Resultado esperado

Una especificacion de arquitectura con:
- grafo principal
- estado tipado
- agentes especializados
- contratos de entrada/salida
- lista de herramientas por agente

### Decisiones objetivo

- `LangGraph` como orquestador principal.
- `Gemini` via `langchain-google-genai` como capa LLM.
- separacion estricta entre orquestacion, dominio, herramientas y transporte.

## Entregable 3 - Plan de validacion

### Resultado esperado

Una estrategia de evaluacion antes de tocar produccion:
- dataset de prompts/casos de prueba
- metricas de routing
- metricas de resolucion
- criterios de fallback
- criterios de aceptacion por fase

### Casos minimos a cubrir

- ticket tecnico claro
- ticket administrativo claro
- solicitud ambigua
- solicitud fuera de dominio
- solicitud que requiere escalamiento humano

## Entregable 4 - Plan de integraciones

### Resultado esperado

Un backlog priorizado de conectores:
1. sistema de tickets
2. base de conocimiento
3. estado de servicios
4. datos administrativos o billing

### Regla de priorizacion

Implementar primero la integracion que mas cambie el valor del flujo, no la mas facil tecnicamente.

## Entregable 5 - Plan operativo

### Resultado esperado

Definir desde el inicio:
- observabilidad
- seguridad
- manejo de secretos
- auditoria de acciones
- control de costos y latencia
- estrategia de despliegue

## Secuencia recomendada

1. Cerrar alcance funcional del MVP.
2. Definir taxonomia de intents y reglas de escalamiento.
3. Disenar grafo, estado y contratos.
4. Preparar pruebas de routing con casos reales anonimizados.
5. Solo despues iniciar implementacion.

## Criterios para arrancar codigo

No conviene empezar a codificar hasta que existan estos minimos:
- lista de agentes del MVP cerrada
- integracion prioritaria definida
- dataset base de casos de prueba
- criterio claro de exito del router
- reglas de aprobacion y fallback documentadas
