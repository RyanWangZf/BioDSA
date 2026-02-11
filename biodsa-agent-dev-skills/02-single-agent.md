# 02 — Implementing a Single Agent

This guide shows how to subclass `BaseAgent` to build a single-agent workflow. There are three common patterns in the codebase, shown from simplest to most complex.

---

## Pattern A: ReAct Loop (Tool-Calling Agent)

> **Example**: `ReactAgent` (`biodsa/agents/react_agent.py`)

The simplest pattern: an LLM with tools in a loop. The agent calls tools until it decides to stop.

### Graph Shape

```
Entry → agent_node ──(has tool calls?)──→ tool_node ──→ agent_node
                    └─(no tool calls)──→ END
```

### State

Use the built-in `AgentState`:

```python
# biodsa/agents/state.py
class AgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    code_execution_results: List[CodeExecutionResult] = []
```

### Minimal Implementation

```python
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.state import AgentState, CodeExecutionResult
from biodsa.sandbox.execution import ExecutionResults


class MyReActAgent(BaseAgent):
    name = "my_react_agent"

    def __init__(self, model_name, api_type, api_key, endpoint, container_id=None, **kwargs):
        super().__init__(
            model_name=model_name, api_type=api_type,
            api_key=api_key, endpoint=endpoint, container_id=container_id,
        )
        self.agent_graph = self._create_agent_graph()

    # 1. Define tools
    def _get_tools(self):
        from biodsa.tool_wrappers.code_exec_tool import CodeExecutionTool
        tool_list = [CodeExecutionTool(sandbox=self.sandbox)]
        return {tool.name: tool for tool in tool_list}

    # 2. Agent node: call LLM with tools
    def _agent_node(self, state: AgentState, config: RunnableConfig) -> dict:
        messages = [SystemMessage(content="You are a helpful assistant.")] + list(state.messages)
        tools = list(self._get_tools().values())
        llm = self._get_model(api=self.api_type, model_name=self.model_name,
                              api_key=self.api_key, endpoint=self.endpoint)
        llm_with_tools = llm.bind_tools(tools)
        response = run_with_retry(llm_with_tools.invoke, arg=messages)
        return {"messages": [response]}

    # 3. Tool node: execute tool calls
    def _tool_node(self, state: AgentState, config: RunnableConfig) -> dict:
        tool_call = state.messages[-1].tool_calls[0]
        tool = self._get_tools()[tool_call["name"]]
        output = tool._run(**tool_call["args"])
        return {"messages": [ToolMessage(content=output, name=tool_call["name"],
                                         tool_call_id=tool_call["id"])]}

    # 4. Routing function
    def _should_continue(self, state: AgentState):
        last = state.messages[-1]
        if not isinstance(last, AIMessage) or not last.tool_calls:
            return "end"
        return "tool_node"

    # 5. Build the graph
    def _create_agent_graph(self):
        wf = StateGraph(AgentState, input=AgentState, output=AgentState)
        wf.add_node("agent_node", self._agent_node)
        wf.add_node("tool_node", self._tool_node)
        wf.add_conditional_edges("agent_node", self._should_continue,
                                 {"tool_node": "tool_node", "end": END})
        wf.add_edge("tool_node", "agent_node")
        wf.set_entry_point("agent_node")
        return wf.compile(name=self.name)

    # 6. Streaming execution
    def generate(self, input_query, verbose=True):
        all_results = []
        for _, chunk in self.agent_graph.stream(
            {"messages": [("user", input_query)]},
            stream_mode=["values"],
            config={"recursion_limit": 20}
        ):
            if verbose:
                print(chunk['messages'][-1].content[:200])
            all_results.append(chunk)
        return all_results

    # 7. Main entry point
    def go(self, input_query, verbose=True):
        results = self.generate(input_query, verbose=verbose)
        final = results[-1]
        return ExecutionResults(
            sandbox=self.sandbox,
            message_history=self._format_messages(final['messages']),
            code_execution_results=self._format_code_execution_results(
                final.get('code_execution_results', [])),
            final_response=final['messages'][-1].content,
        )
```

---

## Pattern B: Multi-Stage Pipeline (No Graph Loop Per Stage)

> **Example**: `AgentMD` (`biodsa/agents/agentmd/agent.py`)

The agent has distinct stages executed sequentially in `go()`, without necessarily using a LangGraph workflow. Each stage is a method that manages its own LLM conversation loop.

### Graph Shape

```
go()
 ├── _step1_tool_selection()   ← Single LLM call
 └── _step2_tool_computation() ← Manual LLM loop with tool calls
```

### Key Characteristics

- **No `self.agent_graph`** — The `go()` method orchestrates the pipeline directly.
- Each step can use different prompts, tools, and even models.
- The manual loop gives fine-grained control over when to stop.

### Skeleton

```python
class MyPipelineAgent(BaseAgent):
    name = "my_pipeline"

    def __init__(self, model_name, api_type, api_key, endpoint, **kwargs):
        super().__init__(model_name=model_name, api_type=api_type,
                         api_key=api_key, endpoint=endpoint)
        # No self.agent_graph needed

    def _step1_analyze(self, query: str) -> str:
        """Step 1: Analyze the input and extract key information."""
        llm = self._get_model(api=self.api_type, model_name=self.model_name,
                              api_key=self.api_key, endpoint=self.endpoint)
        messages = [{"role": "user", "content": f"Analyze this: {query}"}]
        response = run_with_retry(llm.invoke, arg=messages)
        return response.content

    def _step2_execute(self, analysis: str, query: str) -> tuple:
        """Step 2: Execute based on analysis (with tool loop)."""
        from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
        tools = [...]  # your tools
        llm = self._get_model(...)
        llm_with_tools = llm.bind_tools(tools)

        messages = [SystemMessage(content="..."), HumanMessage(content="...")]
        for round_num in range(self.max_rounds):
            response = run_with_retry(llm_with_tools.invoke, arg=messages)
            messages.append(response)
            if not response.tool_calls:
                return response.content, messages
            # Execute tool calls and append ToolMessages
            for tc in response.tool_calls:
                result = tools_dict[tc["name"]]._run(**tc["args"])
                messages.append(ToolMessage(content=result, name=tc["name"],
                                            tool_call_id=tc["id"]))
        return "Max rounds reached", messages

    def go(self, input_query: str, verbose=True) -> ExecutionResults:
        analysis = self._step1_analyze(input_query)
        answer, messages = self._step2_execute(analysis, input_query)
        return ExecutionResults(
            sandbox=None,
            message_history=[...],
            code_execution_results=[],
            final_response=answer,
        )
```

---

## Pattern C: Multi-Stage LangGraph Pipeline (Sub-Workflows as Stages)

> **Example**: `TrialGPTAgent` (`biodsa/agents/trialgpt/agent.py`)

Each stage is its own compiled LangGraph sub-workflow, and a main workflow chains them together.

### Graph Shape

```
Main workflow:
  retrieval_stage → extract_summary → matching_stage → END

Each stage internally:
  agent_node ──(has tool calls?)──→ tool_node ──→ agent_node
              └─(no)──────────────→ END
```

### Key Characteristics

- **Custom state** with stage-specific fields (e.g., `patient_note`, `retrieval_summary`, `candidate_trials`)
- Sub-workflows are compiled independently, then added as nodes in the main workflow
- Information flows between stages through the shared state

### State Definition

```python
# biodsa/agents/my_agent/state.py
class MyAgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Stage 1 outputs
    input_data: str = ""
    stage1_summary: str = ""

    # Stage 2 outputs
    final_results: List[Dict] = Field(default_factory=list)
```

### Graph Construction

```python
def _create_agent_graph(self):
    # Stage 1 sub-workflow
    stage1 = StateGraph(MyAgentState)
    stage1.add_node("stage1_agent", self._stage1_node)
    stage1.add_node("tool_node", self._tool_node)
    stage1.add_conditional_edges("stage1_agent", self._should_continue_stage1,
                                 {"tool_node": "tool_node", "end": END})
    stage1.add_edge("tool_node", "stage1_agent")
    stage1.set_entry_point("stage1_agent")
    stage1 = stage1.compile(name="stage1")

    # Stage 2 sub-workflow
    stage2 = StateGraph(MyAgentState)
    stage2.add_node("stage2_agent", self._stage2_node)
    stage2.add_node("tool_node", self._tool_node)
    stage2.add_conditional_edges("stage2_agent", self._should_continue_stage2,
                                 {"tool_node": "tool_node", "end": END})
    stage2.add_edge("tool_node", "stage2_agent")
    stage2.set_entry_point("stage2_agent")
    stage2 = stage2.compile(name="stage2")

    # Main workflow
    main = StateGraph(MyAgentState)
    main.add_node("stage1", stage1)
    main.add_node("extract_summary", self._extract_summary)
    main.add_node("stage2", stage2)
    main.add_edge("stage1", "extract_summary")
    main.add_edge("extract_summary", "stage2")
    main.add_edge("stage2", END)
    main.set_entry_point("stage1")
    return main.compile(name=self.name)
```

---

## Choosing a Pattern

| Criterion | Pattern A (ReAct) | Pattern B (Manual Pipeline) | Pattern C (LangGraph Pipeline) |
| --------- | ----------------- | --------------------------- | ------------------------------ |
| Simplicity | Simplest | Medium | Most structured |
| When to use | Single-purpose tool-calling agent | Multi-step with different prompts/tools per step | Multi-stage with shared state across stages |
| Graph needed | Yes (simple loop) | No (manual loop in `go()`) | Yes (sub-workflows + main) |
| Examples | ReactAgent, DSWizard | AgentMD | TrialGPT, GeneAgent |

---

## Common Conventions

1. **Class attribute `name`** — Set `name = "my_agent"` as a class attribute. Used as the LangGraph compiled name.
2. **Prompts in `prompt.py`** — Define system prompts as module-level constants in a separate file.
3. **State in `state.py`** — Keep state definitions separate from agent logic.
4. **Tools in `tools.py`** — Keep tool definitions in a separate file with a `get_<agent>_tools()` helper.
5. **Streaming with `generate()`** — Use `self.agent_graph.stream()` for token-by-token output.
6. **Return `ExecutionResults`** from `go()` — Always return an `ExecutionResults` instance.
