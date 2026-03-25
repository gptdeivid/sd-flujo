# Building a Multi‑Prompt Agent with LangChain, Google Gemini (GenAI SDK), and Claude Code

## Overview

A multi‑prompt agent in LangChain is a routing chain that dynamically selects one of several specialized prompts (and downstream chains) based on the user’s input, typically implemented with `MultiPromptChain` on top of a router LLM. This pattern lets a single entrypoint automatically pick an appropriate “persona” or task‑specific prompt (for example, Python expert, cloud architect, math solver) without you manually deciding which prompt to call.

This report explains how to build such a router using LangChain’s `MultiPromptChain` plus Google’s Gemini models via the `langchain_google_genai` integration (which uses the Gemini API/GenAI SDK), and ends with a concrete Markdown guide you can paste into Claude Code to scaffold the project.

## Key components and architecture

A practical multi‑prompt agent with LangChain and Gemini typically involves three core elements.

1. **LLM backend**: a Gemini chat model accessed via LangChain’s `ChatGoogleGenerativeAI`, configured either directly against the Gemini API or via Vertex AI, using a `GOOGLE_API_KEY`/`GEMINI_API_KEY` plus optional project settings.
2. **Destination chains**: a dictionary of `LLMChain` (or more complex chains) keyed by name, each with its own `PromptTemplate` representing a specialized prompt.
3. **Router + MultiPromptChain**: a router chain that examines the user input and selects one destination; `MultiPromptChain.from_prompts` is a convenience constructor that wires the router, destination chains, and default chain from a simple `prompt_infos` list.

At runtime, the agent receives a user query, runs the router LLM over a meta‑prompt describing each available destination, then forwards the query to the chosen destination chain and returns its output.

## Setting up the Google GenAI SDK and Gemini

Google’s official GenAI SDK for Python is exposed via the `google-genai` package, which provides a `genai.Client` capable of calling Gemini models such as `gemini-3-flash-preview` and related variants. The quickstart demonstrates installing the SDK and using the `GEMINI_API_KEY` environment variable so the client can authenticate without hardcoding secrets.

```bash
pip install -U google-genai
export GEMINI_API_KEY="your-api-key"
```

Once configured, a minimal raw SDK usage example looks like this (outside LangChain):

```python
from google import genai

client = genai.Client()
resp = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain how AI works in a few words",
)
print(resp.text)
```

LangChain’s `langchain_google_genai` integration uses the same Gemini API surface and environment variables, so the same API key configuration works when instantiating `ChatGoogleGenerativeAI` in your chains.

## Wiring Gemini into LangChain via `ChatGoogleGenerativeAI`

The `langchain_google_genai` package exposes `ChatGoogleGenerativeAI` as the primary chat model wrapper for Gemini inside LangChain. The class supports both direct Gemini API usage and Vertex AI mode, controlled via environment variables or explicit constructor parameters.

The basic setup is:

```bash
pip install -U langchain langchain-google-genai
export GOOGLE_API_KEY="your-gemini-or-vertex-api-key"
# For Vertex AI usage (optional):
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
```

Then in Python:

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-pro-preview",  # or any current Gemini chat model
    temperature=0.2,
)
```

The same wrapper can be pointed at Vertex AI explicitly (for example, to run Gemini models managed in Vertex AI) by passing `vertexai=True` or using the environment variable `GOOGLE_GENAI_USE_VERTEXAI` as shown in the reference docs.

## Designing the multi‑prompt routing schema

LangChain’s `MultiPromptChain` expects a list of `prompt_infos`, where each element defines a name, description, and prompt template for one destination chain. The router uses the descriptions to decide which prompt is the best match for a given user query.

A typical `prompt_infos` list for an AI engineer might look like this:

```python
prompt_infos = [
    {
        "name": "python_expert",
        "description": "Questions about Python code, debugging, or OOP design.",
        "prompt_template": (
            "You are a senior Python engineer. "
            "Explain and fix code with clear, concise examples.\n"
            "User question: {input}"
        ),
    },
    {
        "name": "cloud_architect",
        "description": "Cloud architecture, GCP/AWS/Azure services, networking, infra.",
        "prompt_template": (
            "You are a cloud solutions architect. "
            "Design pragmatic, cost‑aware cloud solutions.\n"
            "User question: {input}"
        ),
    },
    {
        "name": "math_solver",
        "description": "Math, algorithms, and complexity analysis questions.",
        "prompt_template": (
            "You are a math and algorithms tutor. "
            "Derive the answer step by step.\n"
            "Problem: {input}"
        ),
    },
]
```

Each `prompt_template` is a normal LangChain `PromptTemplate` that takes an `input` variable, and the router will pass the original user message as that `input` value.

## Implementing `MultiPromptChain` with Gemini

LangChain’s router utilities include `MultiPromptChain`, which can be initialized from the `prompt_infos` list using the `from_prompts` classmethod. This helper builds the underlying router chain, the destination `LLMChain` objects, and a default `ConversationChain` used when no specific route is selected.[^1]

A minimal yet realistic implementation with Gemini looks like this:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.router import MultiPromptChain

# 1. Instantiate the Gemini LLM via LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-pro-preview",  # or another Gemini chat model
    temperature=0.2,
)

# 2. Define prompt_infos as shown in the previous section
prompt_infos = [...]

# 3. Build the router + destination chains
chain = MultiPromptChain.from_prompts(
    llm=llm,
    prompt_infos=prompt_infos,
    verbose=True,
)

# 4. Invoke the multi‑prompt agent
result = chain.invoke({"input": "Design a cost‑effective GCP architecture for an event‑driven ETL."})
print(result["text"])  # or result depending on your LangChain version
```

Example usage in older documentation and community snippets shows `MultiPromptChain.from_prompts(OpenAI(), prompt_infos, verbose=True)`; the same pattern applies when substituting `ChatGoogleGenerativeAI` as the LLM backend. For more control, a manual setup can construct an `LLMRouterChain` with a `RouterOutputParser` and `MULTI_PROMPT_ROUTER_TEMPLATE`, but the factory method is usually sufficient for multi‑prompt agents.[^1]

## Extending the agent with tools and memory

Once the basic router is in place, each destination chain can itself be an agent that uses tools (e.g., Google Search, vector stores) instead of a simple `LLMChain`. For example, the `cloud_architect` destination could be a tool‑using agent wired to GCP billing APIs or documentation search, while `python_expert` could be an agent with a code‑execution tool.[^2]

Because `MultiPromptChain` only cares that each destination is a runnable chain, you can replace the simple `LLMChain` instances with `AgentExecutor` instances built using LangChain’s agent tooling. The router then becomes the top‑level controller that chooses which sub‑agent should handle the user’s request.[^2]

## Markdown guide for Claude Code

The following is a concise Markdown implementation guide tailored for a Claude Code environment. It assumes familiarity with Python, virtual environments, and Git.

```markdown
# Multi‑Prompt Agent with LangChain and Google Gemini (Claude Code Guide)

## 1. Create project and environment

1. In Claude Code, create a new Python project folder, for example `langchain-multiprompt-gemini`.
2. Initialize a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   ```

## 2. Install dependencies

```bash
pip install -U "langchain>=0.2" langchain-google-genai google-genai python-dotenv
```

## 3. Configure Gemini / Google GenAI

1. Get a Gemini API key from Google AI Studio or configure Vertex AI as needed.
2. In the project root, create a `.env` file:
   ```env
   GOOGLE_API_KEY=your-gemini-or-vertex-api-key
   # Optional for Vertex AI
   GOOGLE_GENAI_USE_VERTEXAI=true
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   ```
3. Ensure Claude Code loads environment variables from `.env` (or export them manually in the terminal).

## 4. Implement the multi‑prompt agent

Create `multiprompt_agent.py` with:

```python
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.router import MultiPromptChain

# 1. Gemini LLM via LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-pro-preview",  # adjust to current stable model
    temperature=0.2,
)

# 2. Prompt definitions
prompt_infos = [
    {
        "name": "python_expert",
        "description": "Python, debugging, OOP design questions.",
        "prompt_template": (
            "You are a senior Python engineer. "
            "Explain and fix code with concise examples.\\n"
            "User question: {input}"
        ),
    },
    {
        "name": "cloud_architect",
        "description": "Cloud architecture and GCP/AWS/Azure questions.",
        "prompt_template": (
            "You are a pragmatic cloud architect. "
            "Propose cost‑effective, production‑ready designs.\\n"
            "User question: {input}"
        ),
    },
    {
        "name": "math_solver",
        "description": "Math, algorithms, and complexity questions.",
        "prompt_template": (
            "You are a math and algorithms tutor. "
            "Derive the answer step by step.\\n"
            "Problem: {input}"
        ),
    },
]

# 3. Router chain
chain = MultiPromptChain.from_prompts(
    llm=llm,
    prompt_infos=prompt_infos,
    verbose=True,
)

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if not user_input.strip():
            continue
        if user_input.lower() in {"exit", "quit"}:
            break
        result = chain.invoke({"input": user_input})
        # Depending on LangChain version, key may be "text" or "output"
        print("Agent:", result.get("text") or result)
```

## 5. Run and iterate

1. In Claude Code’s terminal, run:
   ```bash
   python multiprompt_agent.py
   ```
2. Ask questions that hit different domains (Python, cloud, math) and verify that the router selects the right prompt based on behavior.
3. Refine `prompt_infos` descriptions and templates, or swap a destination out for a more complex agent (e.g., tool‑using cloud architect) as your needs grow.
```

This guide gives a complete, copy‑pasteable starting point for building a Gemini‑backed multi‑prompt agent in LangChain inside a Claude Code workflow.

---

## References

1. [awesome_ai_agents/README.md at main · jim-schwoebel ...](https://github.com/jim-schwoebel/awesome_ai_agents/blob/main/README.md) - This repository is a comprehensive hub for resources related to AI agents, providing a curated colle...

2. [Building AI Agents in Pure Python - Beginner Course](https://www.youtube.com/watch?v=bZzyPscbtI8) - In this video I'm going to show you how to build effective AI agents or rather AI systems as I would...

