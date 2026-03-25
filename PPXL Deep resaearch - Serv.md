# Multi‑Prompt LangChain Agent with Google Gemini and Claude Code Guide

## Overview

This report describes how to build a multi‑prompt, multi‑agent system in Python using LangChain and Google’s Gemini models via the `langchain-google-genai` integration (which wraps the official Google Generative AI SDK).[^1][^2][^3][^4]
The system routes user queries to specialized agents, each with its own system prompt and tools, and includes a final markdown guide tailored for implementing the solution in Claude Code.

## Stack and prerequisites

- **Language & runtime**: Python 3.10+ (required by recent `langchain-google-genai` releases).[^2]
- **Core libraries**:
  - `langchain` / `langchain-core` for prompts, tools, and multi‑agent patterns.[^5]
  - `langchain-google-genai` to connect LangChain to Gemini models using the consolidated `google-genai` SDK and support both Gemini Developer API and Vertex AI endpoints.[^3][^4][^1][^2]
  - Optionally the underlying Gemini API/SDK from Google AI (`google-genai`) if you also want to work directly at SDK level.[^6]
- **Cloud & auth**:
  - A Gemini API key from Google AI Studio or a configured Vertex AI project; authentication is handled via `GOOGLE_API_KEY` or standard Google Cloud creds.[^4][^1][^2][^6]

### Installation

```bash
pip install -U \
  langchain \
  langchain-core \
  langchain-community \
  langchain-google-genai

# If you also want the raw Gemini SDK (optional in this pattern)
pip install -U google-genai
```

Set your Gemini key (Developer API case):

```bash
export GOOGLE_API_KEY="your-gemini-key"
```

The `langchain-google-genai` package exposes `ChatGoogleGenerativeAI`, which is the main LangChain chat model interface for Gemini (supports Developer API and Vertex AI).[^1][^2][^3][^4]

## Concept: multi‑prompt, multi‑agent with routing

LangChain’s multi‑agent utilities define patterns such as **subagents**, **handoffs**, **skills**, and **router‑based systems**.[^5]
For a “multi‑prompt agent”, the usual design is a set of specialized agents, each with its own system prompt and tools, plus a router that classifies the user query and forwards it to the right agent (or several, then merges results).[^7][^5]

Typical components:

- **Base LLM**: a Gemini model instantiated via `ChatGoogleGenerativeAI`.
- **Specialized agents**:
  - Each agent = prompt template (system + human), tools, plus an executor.
  - Examples: `CodeAgent`, `DataAgent`, `CloudAgent`, `GeneralChatAgent`.
- **Router**:
  - A classifier (another LLM call) that reads the user message and chooses which agent(s) should run.[^7][^5]
- **Orchestrator / graph**:
  - Optionally implemented with LangGraph to represent router + agents as nodes in a workflow; but a simple Python router function works fine for a first version.[^5]

## Integrating Gemini with LangChain

### Initializing the Gemini chat model

The recommended LangChain interface is `ChatGoogleGenerativeAI`, exposed by `langchain-google-genai`.[^2][^3][^4][^1]

```python
from langchain_google_genai import ChatGoogleGenerativeAI

base_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-pro-exp-02-05",  # or gemini-1.5-pro, gemini-2.5-pro, etc.
    temperature=0.2,
)
```

This uses the consolidated Google Generative AI SDK under the hood and works with either the Gemini Developer API or the Vertex AI Gemini endpoint, depending on configuration.[^3][^4]

### Attaching tools (optional)

Gemini models support bound tools (function calling, Google Search, Google Maps, etc.) via LangChain’s tool binding.[^4]

Example: simple Python tool bound to the model through LangChain’s `@tool` decorator:

```python
from langchain.tools import tool

@tool("get_weather", return_direct=False)
def get_weather(location: str) -> str:
    """Get the current weather in a given location (demo stub)."""
    return f"Weather for {location}: sunny and 25C (demo)."

llm_with_weather = base_llm.bind_tools([get_weather])
```

The same pattern can be applied inside each specialized agent, giving different tools to different prompts.[^4][^5]

## Designing the multi‑prompt agents

### 1. Define system prompts per agent

Each agent gets a focused system prompt describing its role and what queries it should handle.

Examples:

- **CodeAgent**: “You are a senior Python and cloud engineer. You handle coding, APIs, microservices, infrastructure as code, and debugging.”
- **DataAgent**: “You are a data analyst. You write SQL, analyze data, and explain metrics.”
- **CloudAgent**: “You are a Google Cloud and AWS architect. You design cloud topologies and cost‑efficient deployments.”
- **GeneralChatAgent**: fallback for everything else.

Multi‑prompt here means each agent has its own `system` message and possibly its own “task template” for user messages.

### 2. Implement agents as LangChain chains

With LangChain, each agent is typically a chain composed of:

- `ChatPromptTemplate` (system + human)
- The Gemini chat model instance
- Optional tooling (via `bind_tools`) and memory.

Pseudo‑implementation:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence

code_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a senior Python and cloud engineer. Answer with code and brief explanations."),
    ("human", "{input}"),
])

code_agent = RunnableSequence(code_prompt | base_llm)

cloud_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a GCP/AWS architect. Design infra and explain tradeoffs."),
    ("human", "{input}"),
])

cloud_agent = RunnableSequence(cloud_prompt | base_llm)

# Add more agents as needed
```

Here `RunnableSequence` is a common LCEL building block, but any LangChain chain/agent executor that takes `{"input": str}` and returns an `AIMessage` (or string) will work.[^5]

## Building the router

### Router concept

LangChain’s router pattern classifies incoming requests and chooses the appropriate specialized agent(s).[^7][^5]
The classification itself is typically done with another LLM call, again using Gemini.

### Simple classifier prompt

Define a classifier prompt that takes the user query and outputs one of a small set of labels, for example: `code`, `cloud`, `data`, or `general`.

```python
from langchain_core.prompts import PromptTemplate

router_prompt = PromptTemplate.from_template(
    """You are a router.
You receive a user query and must decide which expert agent should answer.
Available agents:
- code: coding questions, debugging, APIs, infra as code
- cloud: cloud design, architecture, GCP/AWS/Azure
- data: analytics, SQL, dashboards, KPIs
- general: anything else

Return only one word: code | cloud | data | general.

Query: {input}
Choice:"""
)

router_chain = router_prompt | base_llm
```

For production, the router would often use structured outputs (e.g., Pydantic schema) or LangGraph’s router utilities, but the above is enough to get started.[^5]

### Python router function

Combine the classifier and agents into a single callable that:

1. Calls the router chain.
2. Chooses the selected agent.
3. Forwards the original user query to that agent.

```python
from typing import Dict

agents: Dict[str, RunnableSequence] = {
    "code": code_agent,
    "cloud": cloud_agent,
    # "data": data_agent,
    # "general": general_agent,
}

async def route_and_invoke(user_input: str) -> str:
    # 1) Ask router which agent to use
    classification = await router_chain.ainvoke({"input": user_input})
    label = classification.content.strip().lower()

    if label not in agents:
        label = "code"  # simple fallback

    agent = agents[label]

    # 2) Invoke the selected agent
    response = await agent.ainvoke({"input": user_input})

    # 3) Normalize to text
    return getattr(response, "content", str(response))
```

This is an explicit implementation of the router pattern described in the LangChain multi‑agent docs: a classifier routes to one of multiple specialized agents based on the input.[^7][^5]

## Extending with tools and stateful workflows

### Tools per agent

Using `bind_tools`, each agent can expose different tools to Gemini (e.g., a CloudAgent with Google Maps / Search, a DataAgent with SQL access, etc.).[^4][^5]
For example, to give the CloudAgent access to a stub `estimate_cost` tool:

```python
from langchain.tools import tool

@tool("estimate_cost")
def estimate_cost(description: str) -> str:
    """Estimate relative cloud cost for a given architecture description (demo)."""
    return "Approximate monthly cost: low-medium (demo)."

cloud_llm = base_llm.bind_tools([estimate_cost])

cloud_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a GCP/AWS architect. When useful, call tools to estimate cost."),
    ("human", "{input}"),
])

cloud_agent = RunnableSequence(cloud_prompt | cloud_llm)
```

If Gemini returns tool calls (function calling), a tool‑execution loop similar to the example in the ChatGoogleGenerativeAI docs can be used to execute the tools and feed their results back to the model.[^4]

### LangGraph for richer multi‑agent workflows

For more complex behaviour (handoffs, skills, custom workflows), LangChain recommends using LangGraph to represent agents and routers as nodes in a stateful graph.[^5]
Patterns include:

- **Subagents**: a main agent that decides when to call each subagent.
- **Handoffs**: switching agents based on state changes.
- **Router graphs**: explicit router nodes which send inputs to specific agent nodes.

The core ideas remain the same: each agent still has its own prompt and tools; the graph controls how and when they execute.[^5]

## Cloud considerations (Google Cloud)

- **Running the app**: a typical deployment target is Cloud Run (containerized FastAPI / Flask app) with LangChain and `langchain-google-genai` installed.[^8]
- **Vector storage / RAG**: Google Cloud Next examples show combining LangChain with Cloud SQL + `pgvector` and Vertex AI endpoints for generative applications; the same pattern can be extended to this multi‑agent system.[^8]
- **Auth**: on GCP, prefer service accounts and Application Default Credentials instead of manually exporting `GOOGLE_API_KEY` when using Vertex AI endpoints.[^6][^3][^4]

## Markdown guide for implementing in Claude Code

The following is a self‑contained markdown guide that can be pasted directly into Claude Code as instructions to scaffold the project.

```markdown
# Claude Code Build Guide: Multi‑Prompt LangChain + Gemini Agent

## 1. Goal

Create a Python project that exposes a multi‑prompt, multi‑agent system using LangChain and Google Gemini via `langchain-google-genai`. A router LLM chooses which specialized agent (code, cloud, etc.) should answer a user query.

## 2. Project setup

1. Create a new Python project (3.10+).
2. Add a virtual environment and install dependencies:

   ```bash
   pip install -U \
     langchain \
     langchain-core \
     langchain-community \
     langchain-google-genai
   ```

3. Configure environment variables:

   ```bash
   export GOOGLE_API_KEY="your-gemini-key"  # or configure Vertex AI creds
   ```

## 3. Base LLM initialization

Create `llm.py`:

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-pro-exp-02-05",  # adjust as needed
    temperature=0.2,
)
```

## 4. Define prompts and agents

Create `agents.py`:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from .llm import llm

code_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a senior Python and cloud engineer. Answer with code and brief explanations."),
    ("human", "{input}"),
])

cloud_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a GCP/AWS architect. Design infra and explain tradeoffs."),
    ("human", "{input}"),
])

code_agent = RunnableSequence(code_prompt | llm)
cloud_agent = RunnableSequence(cloud_prompt | llm)

agents = {
    "code": code_agent,
    "cloud": cloud_agent,
}
```

## 5. Build the router

Create `router.py`:

```python
from langchain_core.prompts import PromptTemplate
from .llm import llm
from .agents import agents

router_prompt = PromptTemplate.from_template(
    """You are a router.
You receive a user query and must decide which expert agent should answer.
Available agents:
- code: coding, debugging, APIs, infra as code
- cloud: cloud design, architecture, GCP/AWS/Azure

Return only one word: code | cloud.

Query: {input}
Choice:"""
)

router_chain = router_prompt | llm

async def route_and_invoke(user_input: str) -> str:
    classification = await router_chain.ainvoke({"input": user_input})
    label = classification.content.strip().lower()

    if label not in agents:
        label = "code"

    agent = agents[label]
    response = await agent.ainvoke({"input": user_input})
    return getattr(response, "content", str(response))
```

## 6. Simple CLI entrypoint

Create `main.py`:

```python
import asyncio
from router import route_and_invoke

async def main() -> None:
    while True:
        query = input("User> ")
        if not query or query.lower() in {"exit", "quit"}:
            break
        answer = await route_and_invoke(query)
        print("Agent>", answer)

if __name__ == "__main__":
    asyncio.run(main())
```

## 7. Next steps

- Add more agents (data, general, etc.) by defining new prompts and registering them in `agents`.
- Add tools (e.g., `@tool` functions) and bind them to specific agents.
- Wrap the router function in a FastAPI endpoint and deploy to Cloud Run.
```

---

## References

1. [langchain-google-genai - PyPI](https://pypi.org/project/langchain-google-genai/) - An integration package connecting Google's genai package and LangChain

2. [langchain-google-genai - Python Simple Repository Browser](https://simple-repository.app.cern.ch/project/langchain-google-genai)

3. [Google (GenAI) | LangChain Reference](https://reference.langchain.com/python/integrations/langchain_google_genai/) - Unified reference documentation for LangChain and LangGraph Python packages.

4. [ChatGoogleGenerativeAI integration - Docs by LangChain](https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai) - Integrate with the ChatGoogleGenerativeAI chat model using LangChain Python.

5. [Multi-agent - Docs by LangChain](https://docs.langchain.com/oss/python/langchain/multi-agent) - Tool calls update a state variable that triggers routing or configuration changes, switching agents ...

6. [Gemini API libraries - Google AI for Developers](https://ai.google.dev/gemini-api/docs/libraries) - Download and get started with the Gemini API Libraries + SDKs

7. [Router - Docs by LangChain](https://docs.langchain.com/oss/python/langchain/multi-agent/router) - The router classifies the query and directs it to the appropriate agent(s). Use Command for single-a...

8. [Building generative AI apps on Google Cloud with LangChain](https://www.youtube.com/watch?v=l7tNx52bnsc) - LangChain is the most popular open-source framework for building LLM-based apps. Google Cloud is the...

