# 03 — Multi-Agent Frameworks

This guide covers how to build multi-agent systems in BioDSA, where multiple LLM agents collaborate. There are two established patterns.

---

## Pattern A: Orchestrator + Sub-Agent Workflows

> **Example**: `DeepEvidenceAgent` (`biodsa/agents/deepevidence/agent.py`)

An orchestrator agent delegates tasks to specialized sub-agents (BFS searcher, DFS searcher) via tool calls. Each sub-agent is a separate compiled LangGraph workflow.

### Architecture

```
Orchestrator (main agent)
  │
  ├── calls BFS tool → runs bfs_workflow (sub-agent with its own tools)
  ├── calls DFS tool → runs dfs_workflow (sub-agent with its own tools)
  │
  └── synthesizes results → END
```

### How It Works

1. The **orchestrator** is a ReAct-style agent with access to special "delegation tools" (e.g., `bfs_search`, `dfs_search`).
2. When the orchestrator calls a delegation tool, the tool's implementation invokes a **sub-workflow** (a separate compiled `StateGraph`).
3. The sub-workflow runs autonomously with its own tools (e.g., PubMed search, gene lookup).
4. The sub-workflow's final output is returned as the tool result to the orchestrator.
5. The orchestrator can call sub-agents multiple times and synthesize results.

### Implementation Steps

#### 1. Define Sub-Agent States

```python
# state.py
class BFSAgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    search_results: List[Dict] = Field(default_factory=list)

class DFSAgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    deep_findings: List[Dict] = Field(default_factory=list)

class OrchestratorState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    all_findings: List[Dict] = Field(default_factory=list)
    search_rounds: int = 0
```

#### 2. Build Sub-Workflows

```python
def _create_agent_graph(self):
    # BFS sub-workflow
    bfs_wf = StateGraph(BFSAgentState)
    bfs_wf.add_node("bfs_agent", self._bfs_agent_node)
    bfs_wf.add_node("bfs_tools", self._bfs_tool_node)
    bfs_wf.add_conditional_edges("bfs_agent", self._bfs_should_continue,
                                  {"bfs_tools": "bfs_tools", "end": END})
    bfs_wf.add_edge("bfs_tools", "bfs_agent")
    bfs_wf.set_entry_point("bfs_agent")
    self.bfs_workflow = bfs_wf.compile(name="bfs")

    # DFS sub-workflow (similar pattern)
    dfs_wf = StateGraph(DFSAgentState)
    # ... same pattern ...
    self.dfs_workflow = dfs_wf.compile(name="dfs")

    # Orchestrator workflow
    orch_wf = StateGraph(OrchestratorState)
    orch_wf.add_node("orchestrator", self._orchestrator_node)
    orch_wf.add_node("call_bfs", self._call_bfs_workflow)
    orch_wf.add_node("call_dfs", self._call_dfs_workflow)
    orch_wf.add_node("orch_tools", self._orch_tool_node)
    # ... conditional routing based on orchestrator's tool calls ...
    return orch_wf.compile(name=self.name)
```

#### 3. Bridge Orchestrator to Sub-Workflows

The key technique: create **factory tool functions** that invoke sub-workflows:

```python
def _call_bfs_workflow(self, state: OrchestratorState) -> dict:
    """Node that invokes the BFS sub-workflow."""
    # Extract the query from the last tool call
    tool_call = state.messages[-1].tool_calls[0]
    query = tool_call["args"]["query"]

    # Run the sub-workflow
    result = self.bfs_workflow.invoke({
        "messages": [("user", query)]
    })

    # Extract the sub-agent's final response
    sub_response = result["messages"][-1].content

    # Return as a ToolMessage to the orchestrator
    return {
        "messages": [ToolMessage(
            content=sub_response,
            name="bfs_search",
            tool_call_id=tool_call["id"]
        )]
    }
```

#### 4. Dynamic Tool Selection

The DeepEvidenceAgent dynamically selects which knowledge base tools to give sub-agents based on a `knowledge_bases` parameter:

```python
def go(self, query, knowledge_bases=["pubmed_papers", "clinical_trials", "drug"]):
    # Tools are selected based on knowledge_bases
    tools = self._get_tools_for_knowledge_bases(knowledge_bases)
    # Sub-agents receive these tools
    ...
```

---

## Pattern B: Multi-Participant Meeting

> **Example**: `VirtualLabAgent` (`biodsa/agents/virtuallab/agent.py`)

Multiple LLM "participants" with different personas discuss a topic in rounds, like a virtual meeting.

### Architecture

```
Team Meeting:
  initialize → team_lead_initial → team_member_response (round 1)
                                 → team_member_response (round 2)
                                 → ... (N rounds)
                                 → team_lead_synthesize → team_lead_final → END

Individual Meeting:
  agent_response → critic_feedback → agent_revise → critic_feedback → ... → END
```

### How It Works

1. **Participants** are defined with roles and personas (e.g., PI, ML Specialist, Scientific Critic).
2. Each participant is an LLM call with a role-specific system prompt.
3. The **team lead** initiates discussion, **team members** respond in order, and the **team lead** synthesizes.
4. Multiple rounds of discussion are supported.

### Participant Definition

```python
# participant.py
class Participant(BaseModel):
    name: str           # e.g., "Immunologist"
    role: str           # e.g., "Domain Expert"
    expertise: str      # e.g., "Immunology and cancer biology"
    persona_prompt: str  # Full system prompt for this participant
```

### State Definition

```python
class VirtualLabState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    participants: List[Participant] = Field(default_factory=list)
    team_lead: Optional[Participant] = None
    current_round: int = 0
    max_rounds: int = 3
    meeting_type: str = "team"  # "team" or "individual"
```

### Implementation Skeleton

```python
class MyMeetingAgent(BaseAgent):
    name = "my_meeting"

    def _initialize_node(self, state):
        """Set up participants and initial context."""
        return {
            "participants": [...],
            "team_lead": Participant(name="Lead", ...),
        }

    def _team_lead_initial_node(self, state):
        """Team lead kicks off the discussion."""
        lead = state.team_lead
        llm = self._get_model(...)
        messages = [SystemMessage(content=lead.persona_prompt)] + list(state.messages)
        response = run_with_retry(llm.invoke, arg=messages)
        return {"messages": [response]}

    def _team_member_response_node(self, state):
        """Each team member responds in turn."""
        round_num = state.current_round
        for member in state.participants:
            llm = self._get_model(...)
            messages = [SystemMessage(content=member.persona_prompt)] + list(state.messages)
            response = run_with_retry(llm.invoke, arg=messages)
            # Append as named message
        return {"messages": [...], "current_round": round_num + 1}

    def _should_continue_rounds(self, state):
        if state.current_round >= state.max_rounds:
            return "synthesize"
        return "team_member_response"
```

### Workflow Support

The VirtualLab agent supports **multi-phase workflows** where the output of one meeting feeds into the next:

```python
def run_workflow(self, phases: List[Dict]):
    """Run a sequence of meetings."""
    context = ""
    for phase in phases:
        result = self.go(
            query=phase["query"],
            context=context,
            meeting_type=phase.get("type", "team"),
        )
        context += f"\n\n{result.final_response}"
    return context
```

---

## Choosing Between Multi-Agent Patterns

| Criterion | Orchestrator + Sub-Agents | Multi-Participant Meeting |
| --------- | ------------------------- | ------------------------ |
| When to use | Tasks requiring different search/analysis strategies | Tasks benefiting from diverse perspectives |
| Communication | Via tool calls (structured) | Via conversation messages (natural language) |
| Parallelism | Sub-agents can run independently | Participants respond sequentially |
| State sharing | Through tool inputs/outputs | Through shared message history |
| Examples | Deep evidence gathering, multi-source search | Research brainstorming, peer review, critique |

---

## Tips for Multi-Agent Development

1. **Start with a single agent**, then add orchestration once the core logic works.
2. **Keep sub-agent states minimal** — only include fields that sub-agent needs.
3. **Bridge via ToolMessages** — sub-workflow results should be formatted and returned as `ToolMessage` to the orchestrator.
4. **Budget control** — Add round/action budgets (e.g., `max_search_rounds`, `subagent_action_rounds_budget`) to prevent runaway execution.
5. **Memory** — For complex multi-agent flows, consider using `biodsa/memory/` to maintain a shared knowledge graph across sub-agents.
