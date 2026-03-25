# Analisis y plan de solucion

## 1. Archivos revisados

- `Claude Research- Service Desk.md`: compara LangGraph vs Google ADK y propone un ejemplo de service desk multiagente con clasificador, agente de billing, agente tecnico y supervisor.
- `GDR- ServiceDeskLangchain.md`: define una arquitectura mas rigurosa de produccion con LangGraph, Gemini, tipado fuerte, OOP, tracing, despliegue en Google Cloud y restricciones de scaffolding.
- `PPXL Deep resaearch - Serv.md`: baja el problema a un patron de multi-prompt con LangChain + Gemini y una ruta incremental de implementacion.
- `PPXL LABS - Service desk.md`: refuerza el enfoque de router multi-prompt con prompts especializados y una guia base para Claude Code.

## 2. Perfil inferido

### Perfil tecnico

- Investigas antes de construir y comparas alternativas antes de comprometer stack.
- Piensas en producto y arquitectura al mismo tiempo; no solo en prompts.
- Prefieres soluciones con disciplina de ingenieria: tipado, testing, trazabilidad y despliegue claro.
- Tienes afinidad por el ecosistema Google (`Gemini`, `google-genai`, Vertex/Cloud Run) pero no quieres quedar atado a una abstraccion pobre.
- Quieres usar el agente de codigo como colaborador de arquitectura, no solo como generador de archivos.

### Preferencias de trabajo observables

- Quieres plan antes de codigo.
- Valoras comparativos entre frameworks y criterios de eleccion.
- Te interesa un sistema de service desk que pueda crecer a produccion, no un demo aislado.
- El folder sugiere que estas afinando la forma correcta de construir un router multiagente para soporte/mesa de servicio.

## 3. Requerimientos inferidos de la solucion

### Funcionales

- Recibir solicitudes de usuarios tipo service desk.
- Clasificar o enrutar cada solicitud por intencion o dominio.
- Delegar a agentes especializados en vez de responder con un prompt unico.
- Soportar al menos estos dominios iniciales:
  - clasificacion/triage
  - soporte tecnico
  - billing o temas administrativos
  - fallback/general
- Consolidar la respuesta final para el usuario cuando intervengan varios agentes.
- Preparar el sistema para integracion posterior con herramientas reales: tickets, KB, estado de sistemas, facturas, reembolsos, etc.

### No funcionales

- Orquestacion determinista y observable.
- Estado tipado y validado.
- Separacion clara entre router, agentes, herramientas, estado y capa de transporte.
- Base preparada para pruebas automatizadas.
- Trazabilidad desde el inicio.
- Compatibilidad con despliegue futuro en Google Cloud.
- Evitar dependencias legacy del ecosistema Google.

### Restricciones tecnicas deducidas

- Python como lenguaje principal.
- `LangGraph` como mejor candidato para la orquestacion principal.
- `langchain-google-genai` / `google-genai` como integracion recomendada con Gemini.
- Uso de patrones multi-agent o multi-prompt, pero evitando un `AgentExecutor` lineal como nucleo.
- Enfoque incremental: primero un router funcional y luego herramientas, memoria, RAG y despliegue.

## 4. Lectura critica de las investigaciones

### Lo consistente entre documentos

- El problema correcto no es "hacer un chatbot", sino construir un sistema de ruteo con especialistas.
- `LangGraph` aparece repetidamente como la mejor opcion si importa control, branching, estado y trazabilidad.
- `Google ADK` se ve como alternativa o complemento, no como la opcion principal para este caso.
- El stack objetivo converge en Gemini + LangChain/LangGraph + Google Cloud.
- La solucion debe empezar simple pero con una arquitectura que no obligue a rehacer todo despues.

### Lo que aun no esta definido

- Cuales son exactamente los tipos de ticket prioritarios del negocio.
- Si el service desk operara solo como asistente conversacional o tambien ejecutara acciones reales.
- Que sistema ITSM sera la fuente de verdad: ServiceNow, Jira, Freshservice, Zendesk u otro.
- Que base documental existira para RAG.
- Cuales SLAs, politicas de escalamiento y reglas de aprobacion deben modelarse.
- Si la primera entrega sera interna, operativa o customer-facing.

## 5. Direccion recomendada

### Decision de arquitectura

Recomiendo una arquitectura en 3 capas:

1. `Capa de entrada`: API o interfaz conversacional.
2. `Capa de orquestacion`: `LangGraph` con estado tipado, router, agentes especializados y sintetizador.
3. `Capa de capacidades`: conectores a KB, tickets, estado de servicios, catalogo y billing.

### Razon de la decision

- `LangGraph` da control explicito para triage, handoffs, retries, aprobaciones y observabilidad.
- El caso service desk tiende a requerir reglas, auditoria y rutas de excepcion; eso castiga a las arquitecturas demasiado implicitas.
- El multi-prompt simple sirve como MVP, pero la version con grafo escala mejor cuando aparezcan herramientas reales y memoria.

## 6. Plan maestro

### Plan A - Descubrimiento y definicion

Objetivo: cerrar vacios funcionales antes de construir.

Entregables:
- mapa de intents iniciales
- catalogo de agentes
- inventario de herramientas externas
- criterios de exito por flujo
- decisiones de despliegue del MVP

Tareas:
- definir top 10-20 solicitudes del service desk
- agruparlas por dominio e impacto
- decidir que acciones solo responden y cuales ejecutan
- priorizar integraciones reales vs mocks
- acordar metricas: precision de routing, tiempo de respuesta, tasa de resolucion, necesidad de handoff humano

### Plan B - MVP funcional

Objetivo: validar que el router y los especialistas resuelven mejor que un prompt unico.

Alcance recomendado:
- un router principal
- 3 agentes iniciales: `triage`, `tecnico`, `billing/admin`
- un agente `general` de fallback
- un sintetizador final
- herramientas simuladas o stub para no bloquear avance
- tracing y pruebas de rutas criticas

Criterio de salida:
- el sistema enruta correctamente un conjunto base de casos
- cada agente responde dentro de su dominio sin contaminar contexto
- existe evidencia de trazas y pruebas minimas

### Plan C - Productizacion

Objetivo: llevar el MVP a una base operable.

Alcance recomendado:
- integrar ITSM real
- integrar knowledge base o RAG
- persistencia de estado
- aprobaciones humanas para acciones sensibles
- politicas de errores, retries y timeouts
- observabilidad, costos y seguridad

Criterio de salida:
- flujos auditables
- sesiones persistentes
- conectores reales protegidos por permisos
- telemetria lista para diagnostico y mejora continua

## 7. Plan tecnico por modulos

### Modulo 1 - Dominio y estado

- definir entidades: solicitud, clasificacion, contexto, accion, resultado, escalamiento
- definir estado del grafo con contratos estrictos
- separar estado conversacional de estado operacional

### Modulo 2 - Router

- clasificacion estructurada por intent y severidad
- soporte para uno o varios destinos segun el caso
- reglas de fallback y baja confianza

### Modulo 3 - Agentes especializados

- `triage`: entiende, normaliza y prioriza
- `tecnico`: diagnostico, troubleshooting, sugerencias y apertura de ticket
- `billing/admin`: consultas administrativas y procesos autorizados
- `general`: contencion y derivacion cuando no haya match suficiente

### Modulo 4 - Herramientas

- consulta de estado de servicios
- creacion/actualizacion de tickets
- consulta de KB
- consulta de cuentas, facturas o catalogo
- registro de auditoria

### Modulo 5 - Sintesis y salida

- consolidar respuestas multiagente
- explicar siguiente paso al usuario
- incluir estado del caso, accion ejecutada y ruta de escalamiento si aplica

### Modulo 6 - Calidad operativa

- pruebas de routing
- pruebas de herramientas
- tracing
- manejo de errores
- limites de costo y latencia

## 8. Roadmap por fases

### Fase 0

- definir requerimientos reales del service desk
- cerrar alcance del MVP
- elegir sistema externo prioritario

### Fase 1

- construir el flujo base de router + 3 especialistas + fallback
- trabajar con herramientas stub
- validar conversaciones y rutas

### Fase 2

- integrar primer sistema real (idealmente tickets o KB)
- incorporar memoria/persistencia minima
- agregar evaluaciones del router

### Fase 3

- agregar RAG, aprobaciones humanas y politicas de escalamiento
- endurecer seguridad, despliegue y observabilidad

## 9. Riesgos principales

- empezar por demasiadas integraciones reales y frenar el aprendizaje del flujo.
- sobrecargar al router con taxonomias vagas.
- mezclar logica de negocio con prompts sin contratos de datos.
- depender de un solo prompt monolitico disfrazado de multiagente.
- no definir desde el inicio cuando debe escalar a humano.

## 10. Recomendaciones concretas para la siguiente etapa

- Construir primero el modelo de dominio del service desk, no los prompts finales.
- Diseñar el router como clasificacion estructurada, no como texto libre.
- Empezar con herramientas stub y datasets de casos reales anonimizados.
- Medir desde el MVP precision de routing y tasa de fallback.
- Reservar `ADK` para una fase posterior o para casos muy especificos; no como nucleo inicial.

## 11. Supuestos explicitos

Estos planes se basan en lo que aparece en tus investigaciones. No encontre aun en el folder:

- requerimientos de negocio detallados
- lista real de intents o tickets historicos
- definicion del sistema fuente de tickets
- flujos de aprobacion
- restricciones regulatorias o de seguridad especificas

Por eso el plan esta orientado a una arquitectura correcta y a un MVP validable, pero todavia no a una implementacion cerrada de producto.
