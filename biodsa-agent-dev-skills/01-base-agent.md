# 01 — The BaseAgent Class

> **Source**: `biodsa/agents/base_agent.py`

All agents in BioDSA inherit from `BaseAgent`. This guide covers what the base class provides and what subclasses are expected to implement.

---

## Constructor Signature

```python
class BaseAgent():

    system_prompt: str = None
    registered_datasets: List[str] = []
    sandbox: ExecutionSandboxWrapper = None
    workdir: str = None

    def __init__(
        self,
        api_type: Literal["azure"],       # Also accepts "openai", "anthropic", "google"
        api_key: str,
        model_name: str = None,            # e.g. "gpt-4o", "gpt-5", "claude-sonnet-4-20250514"
        endpoint: str = None,              # Required for Azure
        max_completion_tokens: int = 5000,
        container_id: str = None,          # Docker container ID (optional)
        model_kwargs: Dict[str, Any] = None,
        llm_timeout: Optional[float] = None,
        **kwargs
    ):
```

### What `__init__` Does

1. **Sandbox** — Tries to initialize a `ExecutionSandboxWrapper` Docker sandbox. Falls back to a local `workdir/` if Docker is unavailable.
2. **LLM** — Calls `_get_model()` to create the LangChain chat model (`AzureChatOpenAI`, `ChatOpenAI`, `ChatAnthropic`, or `ChatGoogleGenerativeAI`).
3. **State** — Stores `api_type`, `api_key`, `model_name`, `endpoint`, `model_kwargs`, `llm_timeout` as instance attributes.

### Important Instance Attributes

| Attribute              | Type                         | Description |
| ---------------------- | ---------------------------- | ----------- |
| `self.llm`             | `BaseLanguageModel`          | The initialized LLM instance |
| `self.sandbox`         | `ExecutionSandboxWrapper`    | Docker sandbox (or `None`) |
| `self.workdir`         | `str`                        | Working directory path |
| `self.registered_datasets` | `List[str]`             | Paths of datasets uploaded to sandbox |
| `self.model_name`      | `str`                        | Model name string |
| `self.api_type`        | `str`                        | API provider |
| `self.llm_timeout`     | `Optional[float]`            | Timeout in seconds per LLM call |

---

## Key Methods Provided by BaseAgent

### `_get_model(api, api_key, model_name, endpoint, **kwargs) -> BaseLanguageModel`

Factory method that returns the appropriate LangChain chat model. Supports:
- `"openai"` → `ChatOpenAI`
- `"azure"` → `AzureChatOpenAI`
- `"anthropic"` → `ChatAnthropic`
- `"google"` → `ChatGoogleGenerativeAI`

### `_call_model(model_name, messages, tools, model_kwargs, ...) -> BaseMessage`

Convenience method to call a specific model with tools. Handles:
- Tool binding via `llm.bind_tools(tools)`
- Retry with exponential backoff via `run_with_retry()`
- Timeout support

### `_format_messages(messages) -> List[Dict[str, str]]`

Converts LangChain `BaseMessage` objects into simple `{"role": ..., "content": ...}` dicts. Handles tool calls, list-type content blocks, etc.

### `_format_code_execution_results(code_execution_results) -> List[Dict[str, str]]`

Serializes `CodeExecutionResult` objects to dicts.

### `generate(**kwargs) -> Dict[str, Any]`

Base implementation that invokes `self.agent_graph.invoke(inputs)`. Expects `input_query` in kwargs.
Most agents override this method.

### `register_workspace(workspace_dir, install_biodsa_tools=True)`

Uploads CSV files from a local directory into the Docker sandbox. Also installs `biodsa.tools` into the sandbox so agent-generated code can `from biodsa.tools import ...`.

### `clear_workspace()`

Stops the sandbox and cleans up resources.

### `go(input_query) -> Dict[str, Any]`

The main entry point for running the agent. Raises `NotImplementedError` in the base class — **every agent must implement this**.

---

## What Subclasses Must Implement

| Method | Required? | Purpose |
| ------ | --------- | ------- |
| `__init__` | Yes | Call `super().__init__(...)`, set `name`, build `self.agent_graph` |
| `_create_agent_graph()` | Yes (by convention) | Build and return the compiled LangGraph `StateGraph` |
| `go(input_query)` | Yes | Main entry point; returns `ExecutionResults` |
| `generate(...)` | Recommended | Streaming execution; called by `go()` |
| `_get_tools()` | Recommended | Return a list/dict of tools for the agent |
| `_build_system_prompt()` | Optional | Dynamically build the system prompt |

---

## The `run_with_retry` Helper

Defined at module level in `base_agent.py`:

```python
def run_with_retry(
    func: Callable,
    max_retries: int = 5,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    timeout: Optional[float] = None,
    arg=None,
    **kwargs
):
```

All LLM calls should go through this function. It provides:
- Exponential backoff with jitter (via `tenacity`)
- Optional timeout per call (via `ThreadPoolExecutor`)
- Automatic retry on any exception

**Usage**:
```python
response = run_with_retry(llm_with_tools.invoke, arg=messages, timeout=self.llm_timeout)
```

---

## Subclass `__init__` Pattern

Every agent follows this pattern:

```python
class MyAgent(BaseAgent):
    name = "my_agent"

    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str,
        container_id: str = None,
        # ... agent-specific params ...
        **kwargs
    ):
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
        )
        # agent-specific initialization
        self.agent_graph = self._create_agent_graph()
```

**Key points**:
- Always call `super().__init__(...)` first
- Set the `name` class attribute (used as the compiled graph name)
- Build `self.agent_graph` at the end of `__init__`
- Add any agent-specific parameters (e.g., `max_rounds`, `top_k_retrieval`)
