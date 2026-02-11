# 04 — Tools and Tool Wrappers

BioDSA has a three-layer tool architecture. This guide explains each layer and how to create new tools.

---

## Layer 1: Low-Level API Tools (`biodsa/tools/`)

Pure Python functions that call external biomedical APIs. These have **no LangChain dependency** and can be used standalone or inside the Docker sandbox.

### Directory Structure

```
biodsa/tools/
├── biothings/          # BioThings API (genes, diseases, drugs, variants)
├── chembl/             # ChEMBL database (compounds, drugs, targets)
├── clinical_trials/    # ClinicalTrials.gov
├── compound/           # Unified compound search
├── diseases/           # Unified disease search
├── drugs/              # Unified drug search
├── ensembl/            # Ensembl genome database
├── gene_ontology/      # Gene Ontology
├── gene_set/           # Gene set analysis (enrichment, pathways, etc.)
├── genes/              # Unified gene search
├── hpo/                # Human Phenotype Ontology
├── kegg/               # KEGG pathway database
├── ncbi/               # NCBI databases
├── openfda/            # FDA Open Data
├── opengenes/          # OpenGenes database
├── opentargets/        # Open Targets Platform
├── pathway/            # Unified pathway search
├── proteinatlas/       # Human Protein Atlas
├── pubchem/            # PubChem database
├── pubmed/             # PubMed / PubTator
├── reactome/           # Reactome pathway database
├── risk_calculators/   # Clinical risk calculators (AgentMD)
├── targets/            # Unified target search
├── umls/               # Unified Medical Language System
└── uniprot/            # UniProt protein database
```

### Pattern: Client + Domain Tools

Most tool modules follow a `client.py` + domain-specific tool files pattern:

```python
# biodsa/tools/opentargets/client.py
class OpenTargetsClient:
    BASE_URL = "https://api.platform.opentargets.org/api/v4/graphql"

    def query(self, graphql_query: str, variables: dict = None) -> dict:
        """Execute a GraphQL query against Open Targets."""
        ...

# biodsa/tools/opentargets/target_tools.py
from .client import OpenTargetsClient

def search_targets(query: str, limit: int = 10) -> list:
    """Search for drug targets by name or keyword."""
    client = OpenTargetsClient()
    ...
```

### Creating a New Low-Level Tool

1. Create a directory: `biodsa/tools/my_api/`
2. Add `__init__.py`, `client.py`, and domain-specific tool files.
3. Write pure functions that return serializable data (dicts, lists, strings).
4. Add a `README.md` documenting the API and available functions.
5. **No LangChain imports** in this layer.

```python
# biodsa/tools/my_api/client.py
import requests

class MyAPIClient:
    BASE_URL = "https://api.example.com/v1"

    def query(self, endpoint: str, params: dict = None) -> dict:
        response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

# biodsa/tools/my_api/search.py
from .client import MyAPIClient

def search_items(query: str, limit: int = 10) -> list:
    client = MyAPIClient()
    result = client.query("search", {"q": query, "limit": limit})
    return result.get("items", [])
```

---

## Layer 2: LangChain Tool Wrappers (`biodsa/tool_wrappers/`)

These wrap the low-level tools as LangChain `BaseTool` subclasses so they can be bound to LLMs via `llm.bind_tools()`.

### Directory Structure

```
biodsa/tool_wrappers/
├── biothings/
├── clinical_trials/
├── code_exec_tool.py     # Code execution (sandbox or local)
├── diseases/
├── drugs/
├── gene_set/
├── genes/
├── pubmed/               # PubMed + PubTator wrappers
├── umls/
├── utils.py              # Python REPL helpers
└── websearch/
```

### Pattern: BaseTool + Pydantic Input Schema

Every tool wrapper follows this pattern:

```python
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class MyToolInput(BaseModel):
    """Input schema — becomes the tool's argument spec for the LLM."""
    query: str = Field(description="Search query")
    limit: int = Field(default=10, description="Max results to return")


class MySearchTool(BaseTool):
    """LangChain tool wrapper."""
    name: str = "my_search"
    description: str = """Search for items using MyAPI.
    Use this when you need to find information about X.
    Returns a formatted list of results."""
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, query: str, limit: int = 10) -> str:
        """Execute the tool and return a formatted string."""
        from biodsa.tools.my_api.search import search_items
        results = search_items(query, limit=limit)
        if not results:
            return f"No results found for '{query}'."
        # Format as readable text for the LLM
        output = f"# Search Results for '{query}'\n\n"
        for i, item in enumerate(results, 1):
            output += f"{i}. **{item['name']}**: {item['description']}\n"
        return output
```

### Key Rules for Tool Wrappers

1. **`name`** — Short, snake_case identifier. This is what the LLM sees.
2. **`description`** — Detailed description of when and how to use the tool. The LLM reads this to decide whether to call the tool.
3. **`args_schema`** — Pydantic model defining the tool's input parameters. Field descriptions guide the LLM.
4. **`_run()`** — Must return a **string**. Format it as readable markdown for the LLM to consume.
5. **Error handling** — Catch exceptions in `_run()` and return error strings rather than raising.

### The CodeExecutionTool (Special Case)

`biodsa/tool_wrappers/code_exec_tool.py` is the most commonly used tool:

```python
class CodeExecutionTool(BaseTool):
    name: str = "code_execution"
    description: str = "Execute code to answer the user's question..."
    sandbox: ExecutionSandboxWrapper = None  # Passed at construction

    def __init__(self, sandbox=None, max_output_tokens=4096):
        super().__init__()
        self.sandbox = sandbox
        self.max_output_tokens = max_output_tokens

    def _run(self, code: str) -> str:
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory_mb = \
                self.sandbox.execute(language="python", code=code)
            # ... format result ...
        else:
            output = run_python_repl(code)  # local fallback
            # ... format result ...
```

Tools that need the sandbox receive it in their constructor, typically via:
```python
tools = [CodeExecutionTool(sandbox=self.sandbox)]
```

---

## Layer 3: Agent-Specific Tools (`biodsa/agents/<name>/tools.py`)

Domain-specific tools that only make sense for a particular agent. These are defined alongside the agent and follow the same `BaseTool` pattern.

### Example: AgentMD Tools

```python
# biodsa/agents/agentmd/tools.py

class CalculatorSearchTool(BaseTool):
    name: str = "search_calculators"
    description: str = "Search for relevant clinical calculators..."
    args_schema: Type[BaseModel] = CalculatorSearchInput

    def _run(self, query, category=None, top_k=5) -> str:
        from biodsa.tools.risk_calculators import RiskCalcRetriever
        retriever = RiskCalcRetriever()
        results = retriever.retrieve(query, top_k=top_k)
        # ... format ...

def get_agentmd_tools() -> List[BaseTool]:
    """Convenience function to get all tools for this agent."""
    return [
        CalculatorSearchTool(),
        CalculatorDetailsTool(),
        RunCalculatorTool(),
        ExecuteCodeTool(),
        ListCalculatorsTool(),
    ]
```

### Pattern: `get_<agent>_tools()` Helper

Every agent's `tools.py` should export a convenience function:

```python
def get_my_agent_tools() -> List[BaseTool]:
    """Get all tools for MyAgent."""
    return [MySearchTool(), MyAnalysisTool(), ...]
```

This is used in the agent:
```python
def _get_tools(self):
    from biodsa.agents.my_agent.tools import get_my_agent_tools
    return get_my_agent_tools()
```

---

## Wiring Tools into Agents

### In a ReAct Agent Node

```python
def _agent_node(self, state, config):
    tools = list(self._get_tools().values())
    llm = self._get_model(...)
    llm_with_tools = llm.bind_tools(tools)
    response = run_with_retry(llm_with_tools.invoke, arg=messages)
    return {"messages": [response]}
```

### In a Tool Node

```python
def _tool_node(self, state, config):
    last_message = state.messages[-1]
    tool_dict = self._get_tools()  # {name: tool_instance}

    tool_results = []
    for tool_call in last_message.tool_calls:
        tool = tool_dict[tool_call["name"]]
        try:
            output = tool._run(**tool_call["args"])
        except Exception as e:
            output = f"Error: {str(e)}"
        tool_results.append(ToolMessage(
            content=output,
            name=tool_call["name"],
            tool_call_id=tool_call["id"],
        ))
    return {"messages": tool_results}
```

---

## Reusing Existing Tools

Before creating new tools, check if existing ones cover your needs:

| Need | Existing Tool Location |
| ---- | ---------------------- |
| Run Python code | `biodsa/tool_wrappers/code_exec_tool.py` |
| Search PubMed | `biodsa/tool_wrappers/pubmed/` |
| Search clinical trials | `biodsa/tools/clinical_trials/` |
| Gene information | `biodsa/tool_wrappers/genes/`, `biodsa/tools/genes/` |
| Drug information | `biodsa/tool_wrappers/drugs/`, `biodsa/tools/drugs/` |
| Disease information | `biodsa/tool_wrappers/diseases/`, `biodsa/tools/diseases/` |
| Gene set analysis | `biodsa/tool_wrappers/gene_set/`, `biodsa/tools/gene_set/` |
| UMLS concepts | `biodsa/tool_wrappers/umls/` |
| Web search | `biodsa/tool_wrappers/websearch/` |
| Risk calculators | `biodsa/tools/risk_calculators/` |
| Pathway analysis | `biodsa/tools/pathway/`, `biodsa/tools/reactome/` |
| Protein data | `biodsa/tools/uniprot/`, `biodsa/tools/proteinatlas/` |

---

## Checklist for Adding a New Tool

1. Decide the layer:
   - **Low-level** (`biodsa/tools/`) if it's a general API client others might reuse
   - **Wrapper** (`biodsa/tool_wrappers/`) if it wraps a low-level tool for LangChain
   - **Agent-specific** (`biodsa/agents/<name>/tools.py`) if it's only for one agent
2. Write the Pydantic input schema with descriptive `Field(description=...)`.
3. Write a clear `description` for the tool — this is what the LLM reads.
4. Implement `_run()` returning a formatted string.
5. Handle errors gracefully (return error strings, don't raise).
6. Add to `get_<agent>_tools()` or the appropriate `__init__.py`.
