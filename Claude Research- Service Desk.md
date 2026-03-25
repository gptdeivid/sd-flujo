# Building multi-agent systems with LangGraph, Google ADK, and Claude Code

**LangGraph and Google ADK represent two fundamentally different philosophies for building multi-agent systems in Python — graph-based state machines versus hierarchical agent composition — and both reached production maturity in 2025.** LangGraph (v1.1.0) models agent workflows as directed graphs with explicit state, edges, and conditional routing, while Google ADK (v1.27+) treats agents as composable building blocks with built-in sequential, parallel, and loop orchestrators. Claude Code (v2.1) serves as a powerful scaffolding tool for both, especially when configured with framework-specific CLAUDE.md files and MCP documentation servers. This guide covers the architecture, code patterns, and practical workflows for each.

---

## LangGraph turns agent workflows into programmable state machines

LangGraph, built by LangChain Inc., is a **graph-based orchestration framework** where nodes represent computation units (LLM calls, tool execution, custom logic) and edges define control flow. Unlike simple DAGs, it supports **cyclical workflows** — critical for agent-like behaviors where an LLM reasons, acts, observes, and loops. As of March 2026, LangGraph is at **v1.1.0** (GA since October 2025), and LangChain itself is at v1.0.3.

The core abstraction is the `StateGraph`. You define a typed state schema (typically a `TypedDict`), add nodes as Python functions that read and write to that state, and connect them with normal or conditional edges. The graph must be compiled before execution.

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: str

def agent_node(state: AgentState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"continue": "tools", "end": END})
graph.add_edge("tools", "agent")
app = graph.compile()
```

**LangChain 1.0 introduced `create_agent`** as the recommended high-level API, replacing `create_react_agent` from `langgraph.prebuilt`. For simple tool-calling agents, this single function handles the entire agent loop:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[check_weather, search_web],
    system_prompt="You are a helpful research assistant.",
)
result = agent.invoke({"messages": [{"role": "user", "content": "What's the weather in SF?"}]})
```

Drop down to raw `StateGraph` only when you need custom control flow, branching, or multi-agent orchestration.

### Five orchestration patterns for multi-agent LangGraph systems

**Pattern 1 — Supervisor via tool wrapping (recommended).** The current best practice wraps sub-agents as tools the supervisor can call. This gives full control over context engineering — each sub-agent receives only the information it needs:

```python
from langchain.agents import create_agent
from langchain.tools import tool

# Specialized sub-agents
calendar_agent = create_agent(model="openai:gpt-4o", tools=[create_event], system_prompt="You schedule events.")
email_agent = create_agent(model="openai:gpt-4o", tools=[send_email], system_prompt="You manage email.")

# Wrap as tools
@tool
def schedule_event(request: str) -> str:
    """Schedule calendar events using natural language."""
    result = calendar_agent.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].text

@tool
def manage_email(request: str) -> str:
    """Send and manage emails using natural language."""
    result = email_agent.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].text

# Supervisor orchestrates
supervisor = create_agent(
    model="openai:gpt-4o",
    tools=[schedule_event, manage_email],
    system_prompt="You coordinate calendar and email tasks.",
)
```

**Pattern 2 — Agent handoffs with `Command`.** Agents transfer control to each other using `Command` objects that specify the target node and state updates. The `langgraph-swarm` library provides a clean API for this:

```python
from langgraph_swarm import create_handoff_tool, create_swarm

alice = create_agent(
    ChatOpenAI(model="gpt-4o"),
    tools=[add, create_handoff_tool(agent_name="Bob", description="Transfer to Bob")],
    system_prompt="You are Alice, an addition expert.", name="Alice",
)
bob = create_agent(
    ChatOpenAI(model="gpt-4o"),
    tools=[create_handoff_tool(agent_name="Alice", description="Transfer to Alice")],
    system_prompt="You are Bob.", name="Bob",
)
workflow = create_swarm([alice, bob], default_active_agent="Alice")
app = workflow.compile(checkpointer=InMemorySaver())
```

**Pattern 3 — Sequential prompt chaining.** Simple pipelines where each step's output feeds the next, built as a linear graph with no conditional edges.

**Pattern 4 — Hierarchical teams.** Multi-level supervisors where each sub-team is itself a compiled LangGraph, added as a node in a parent supervisor graph.

**Pattern 5 — ReAct tool-calling loop.** The classic reason-act-observe cycle, built from `StateGraph` with a conditional edge that checks whether the LLM returned tool calls or a final answer.

### LangGraph best practices for 2025-2026

**State management** deserves particular attention. Use `MessagesState` for simple agents and subclass it to add custom fields. The `Annotated[list, add_messages]` type handles message deduplication and ordering automatically. Keep state minimal and typed — don't dump transient values.

**Human-in-the-loop** requires a checkpointer. The preferred approach uses the `interrupt()` function inside a node, which pauses execution and surfaces data to the user. Resume with `Command(resume=value)`. A checkpointer (`InMemorySaver` for development, Postgres for production) is **mandatory** for interrupts to work.

**Streaming** supports four modes: `messages` for token-level output, `updates` for state deltas after each node, `values` for full snapshots, and `custom` for tailored payloads. LangGraph 1.1 added type-safe `StreamPart` objects.

**Middleware**, new in LangChain 1.0, provides composable hooks for context management. `SummarizationMiddleware` manages context windows by summarizing old messages. `HumanInTheLoopMiddleware` adds approval workflows. Custom middleware via `wrap_model_call` intercepts model requests and responses.

---

## Google ADK makes multi-agent composition feel like function composition

Google's Agent Development Kit, announced at **Cloud NEXT 2025** and declared production-ready at **I/O 2025**, takes a fundamentally different approach. Where LangGraph gives you a graph to wire up, ADK gives you **composable agent types** that snap together like building blocks. The current Python version is **v1.27.2** on PyPI, with roughly bi-weekly releases.

ADK's core unit is the `Agent` (alias for `LlmAgent`) — defined by a name, model, instruction, description, tools, and sub-agents. Three built-in **workflow agents** handle deterministic orchestration without any LLM calls:

- **`SequentialAgent`** executes sub-agents in order, sharing session state
- **`ParallelAgent`** executes sub-agents concurrently
- **`LoopAgent`** iterates sub-agents until `max_iterations` or an escalation signal

```python
# Install: pip install google-adk

from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """Retrieves weather for a city."""
    return {"status": "success", "report": f"Sunny, 25°C in {city}"}

root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    description="Provides weather information.",
    instruction="You are a helpful weather agent. Use tools to get data.",
    tools=[get_weather],
)
```

**State communication between agents** uses a shared `session.state` dictionary. The `output_key` parameter on an `LlmAgent` automatically saves its response to a named state key. Other agents read it using `{key_name}` template syntax in their instructions — a clean, declarative pattern for data flow:

```python
from google.adk.agents import SequentialAgent, LlmAgent

writer = LlmAgent(
    name="Writer", model="gemini-2.5-flash",
    instruction="Write Python code for the user's request.",
    output_key="generated_code"
)
reviewer = LlmAgent(
    name="Reviewer", model="gemini-2.5-flash",
    instruction="Review this code: {generated_code}. Provide feedback.",
    output_key="review_comments"
)
refactorer = LlmAgent(
    name="Refactorer", model="gemini-2.5-flash",
    instruction="Refactor {generated_code} based on {review_comments}.",
    output_key="final_code"
)
root_agent = SequentialAgent(
    name="CodePipeline", sub_agents=[writer, reviewer, refactorer]
)
```

### Dynamic delegation and parallel research patterns

For **LLM-driven routing**, a coordinator agent with `sub_agents` automatically gains access to `transfer_to_agent()` calls. The framework intercepts these, finds the target agent, and switches execution — no explicit graph wiring needed:

```python
billing = LlmAgent(name="Billing", model="gemini-2.0-flash",
    description="Handles billing and payment issues.",
    instruction="You handle billing questions precisely.")

support = LlmAgent(name="Support", model="gemini-2.0-flash",
    description="Handles technical support requests.",
    instruction="You troubleshoot technical issues.")

coordinator = LlmAgent(
    name="HelpDesk", model="gemini-2.0-flash",
    instruction="Route: billing/payment → Billing, technical → Support.",
    sub_agents=[billing, support]
)
```

For **parallel fan-out with synthesis**, combine `ParallelAgent` and `SequentialAgent`:

```python
from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent

energy_researcher = LlmAgent(name="EnergyResearch", model="gemini-2.5-flash",
    instruction="Research renewable energy advancements.", output_key="energy_result")
ev_researcher = LlmAgent(name="EVResearch", model="gemini-2.5-flash",
    instruction="Research electric vehicle trends.", output_key="ev_result")

parallel_step = ParallelAgent(name="Research", sub_agents=[energy_researcher, ev_researcher])
synthesizer = LlmAgent(name="Synthesizer", model="gemini-2.5-flash",
    instruction="Combine {energy_result} and {ev_result} into a unified report.")

root_agent = SequentialAgent(name="Pipeline", sub_agents=[parallel_step, synthesizer])
```

**Running agents programmatically** uses the `Runner` and `InMemorySessionService`:

```python
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def main():
    session_service = InMemorySessionService()
    runner = Runner(app_name="my_app", agent=root_agent, session_service=session_service)
    session = await session_service.create_session(app_name="my_app", user_id="user-1")
    
    message = types.Content(role="user", parts=[types.Part(text="What's the weather in London?")])
    async for event in runner.run_async(user_id="user-1", session_id=session.id, new_message=message):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"[{event.author}]: {part.text}")

asyncio.run(main())
```

ADK also provides **callbacks at every level** — `before_agent_callback`, `after_model_callback`, `before_tool_callback`, etc. — plus a **Plugins system** for global interceptors registered on the Runner. The `adk web` command launches a built-in development UI at localhost:8000 for testing agents interactively.

---

## LangGraph versus Google ADK: choosing the right framework

The two frameworks optimize for different developer experiences and deployment targets. Here's where each excels:

| Dimension | LangGraph | Google ADK |
|-----------|-----------|------------|
| **Mental model** | Explicit directed graph with state | Hierarchical agent composition |
| **Control granularity** | Fine-grained (every edge, condition, state update) | Coarse-grained (agent types handle orchestration) |
| **Multi-agent primitives** | Manual via StateGraph, Command, swarm library | Built-in Sequential, Parallel, Loop, Transfer |
| **Model ecosystem** | 100+ model integrations via LangChain | Gemini-optimized, others via LiteLLM |
| **State management** | Typed state schemas with reducers | Session state dict with output_key templates |
| **Deployment** | Self-hosted, LangSmith for observability | Vertex AI Agent Engine, Cloud Run, GKE |
| **Dev tooling** | LangSmith traces, LangGraph Studio | Built-in `adk web` UI, OpenTelemetry |
| **Maturity** | 3+ years, massive ecosystem | ~1 year, rapidly evolving (v1.27+) |
| **Learning curve** | Steeper (graph concepts, state reducers) | Gentler (Python classes, declarative composition) |
| **Best for** | Complex custom workflows, maximum flexibility | Google Cloud teams, structured multi-agent pipelines |

**LangGraph wins on flexibility.** If you need custom control flow, complex branching, human-in-the-loop with checkpointing, or deep integration with non-Google models and tools, LangGraph's graph-based approach gives you surgical control over every decision point. The middleware system and streaming modes are more mature.

**ADK wins on ergonomics for structured pipelines.** If your multi-agent system naturally decomposes into sequential, parallel, or iterative stages — which most do — ADK's workflow agents express this with far less boilerplate. The `output_key` + template syntax for inter-agent communication is particularly elegant. ADK is also the clear choice for teams already invested in Google Cloud and Gemini.

Both frameworks are **model-agnostic** in practice. LangGraph works with any LangChain-supported model. ADK works with Gemini natively and supports Claude, GPT-4o, and others via LiteLLM. Both support the **A2A (Agent-to-Agent) protocol** for cross-framework interoperability.

---

## Claude Code accelerates scaffolding for both frameworks

Claude Code (v2.1, powered by Claude Sonnet 4.5) is Anthropic's agentic coding tool that operates in your terminal, understands entire codebases, edits files, and runs commands. It's the most effective tool available for scaffolding multi-agent projects when configured correctly.

**Installation and setup:**

```bash
# macOS/Linux
curl -fsSL https://claude.ai/install.sh | sh

# Windows
winget install Anthropic.ClaudeCode

# Start a session
cd your-project && claude
```

**The highest-leverage configuration is the CLAUDE.md file** — a markdown file at your project root that gives Claude persistent context about your project's architecture, conventions, and commands. LangChain's own research found that **Claude + CLAUDE.md outperformed Claude + MCP documentation alone**, and the combined approach produced the best results:

```markdown
# Multi-Agent System

Python 3.12, uv for packages, LangGraph for orchestration.

## Commands
- `uv sync`: Install deps
- `uv run pytest`: Tests
- `uv run ruff check .`: Lint

## Architecture
- Use StateGraph with TypedDict state schemas
- Supervisor pattern: wrap sub-agents as tools
- create_react_agent for tool-calling agents
- Always add checkpointer for human-in-the-loop

## Pitfalls
- Don't use input() for HITL; use interrupt()
- Always validate structured output from LLM calls
```

**Add framework documentation via MCP servers** for deep reference access:

```bash
# LangGraph docs
claude mcp add langchain-docs --transport stdio -- \
  uvx --from mcpdoc mcpdoc \
  --urls "LangGraph:https://langchain-ai.github.io/langgraph/llms.txt" \
  --transport stdio

# Google ADK docs
claude mcp add adk-docs --transport stdio -- \
  uvx --from mcpdoc mcpdoc \
  --urls "AgentDevelopmentKit:https://google.github.io/adk-docs/llms.txt" \
  --transport stdio
```

**Effective scaffolding prompts provide architecture context first, then technical specifics:**

```
> Create a multi-agent customer support system using LangGraph with:
> - A classifier agent that categorizes incoming tickets (billing, technical, general)
> - A billing agent with tools for looking up invoices and processing refunds
> - A technical agent with tools for checking system status and creating tickets
> - A supervisor that routes based on classification
>
> Use Python 3.12 with uv. Set up proper TypedDict state schemas.
> Include LangSmith tracing. Write tests with pytest.
```

For Google ADK projects, a similar prompt structure works:

```
> Using google-adk, create a research pipeline with:
> - A ParallelAgent that runs 3 researcher agents simultaneously
> - Each researcher uses google_search tool for a different topic
> - A SequentialAgent wrapper that feeds parallel results into a synthesizer
> - Set up .env for GOOGLE_API_KEY, proper project structure with __init__.py
```

**The iterative workflow matters as much as the initial prompt.** Use `/init` to generate an initial CLAUDE.md, then refine it manually. Use `/plan` mode to have Claude propose architecture before coding. Use `Esc` to course-correct mid-generation, and `/compact` at ~50% context usage to keep the conversation productive. Claude Code's **subagent capability** delegates investigation tasks to separate instances, preserving main context for implementation work.

---

## Conclusion

The multi-agent landscape in 2026 has consolidated around two dominant patterns: **graph-based orchestration** (LangGraph) and **hierarchical composition** (Google ADK). LangGraph's `StateGraph` with the tool-wrapping supervisor pattern offers maximum control for complex, branching workflows. ADK's `SequentialAgent`/`ParallelAgent`/`LoopAgent` trio provides a more declarative approach that maps cleanly to common pipeline architectures. The critical insight is that **both frameworks now recommend wrapping sub-agents as callable tools** rather than building monolithic agent graphs — this preserves context isolation and makes systems easier to test and debug. Claude Code, configured with a curated CLAUDE.md and framework-specific MCP documentation servers, can scaffold either system in minutes, turning architectural decisions into working code with proper project structure, typed state schemas, and test scaffolding from the start.