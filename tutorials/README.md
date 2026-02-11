# BioDSA Tutorials

This folder contains **tutorial notebooks** for each published agent and a **vibe-prototyping tutorial** that shows how to go from a natural-language idea to a working agent using the BioDSA framework and the agent-development skills.

---

## Tutorial notebooks (by agent)

| Agent | Tutorial | Description |
|-------|----------|-------------|
| DSWizard | [dswizard_agent.ipynb](./dswizard_agent.ipynb) | Two-phase data science agent |
| DeepEvidence | [deepevidence_agent.ipynb](./deepevidence_agent.ipynb) | Deep research across 17+ knowledge bases |
| TrialMind-SLR | [trialmind_slr_agent.ipynb](./trialmind_slr_agent.ipynb) | Systematic literature review (4-stage) |
| InformGen | [informgen_agent.ipynb](./informgen_agent.ipynb) | Clinical document generation |
| TrialGPT | [trialgpt_agent.ipynb](./trialgpt_agent.ipynb) | Patient-to-trial matching |
| AgentMD | [agentmd_agent.ipynb](./agentmd_agent.ipynb) | Clinical risk prediction with calculators |
| GeneAgent | [geneagent.ipynb](./geneagent.ipynb) | Gene set analysis with verification |
| Virtual Lab | [virtuallab_agent.ipynb](./virtuallab_agent.ipynb) | Multi-agent research meetings |

---

## Vibe prototyping: from idea to agent with skills

**Vibe prototyping** means describing what you want in natural language and having an AI coding assistant (Cursor, Claude Code, Codex, Gemini, etc.) design and implement a BioDSA agent for you. The assistant follows the **BioDSA Agent Development Skill** so the new agent fits the framework’s patterns, tools, and deliverables.

This section uses a **real example from a single session** to show the flow.

### 1. Prerequisites

- **Skills installed** so the assistant knows the framework:
  ```bash
  ./install-cursor.sh        # Cursor (project-level)
  # or: ./install-claude-code.sh, ./install-codex.sh, ./install-gemini.sh
  ```
- Skills live under `biodsa-agent-dev-skills/` and are copied to your assistant’s skills directory (e.g. `.cursor/skills/biodsa-agent-development/`). The skill describes BaseAgent, state graphs, tools, deliverables, and a **checklist** for creating a new agent.

### 2. The ask (example from this session)

The user said:

> *"Can you create a new agent so it can search pubmed and ctgov to do systematic literature review and meta-analysis to synthesize clinical evidence for a given research question?"*

So the goal was: **one agent** that uses **PubMed** and **ClinicalTrials.gov**, runs a **systematic literature review**, does **meta-analysis**, and **synthesizes clinical evidence** for a research question.

### 3. How the skill guides the assistant

With the skill loaded, the assistant:

1. **Interprets the goal** — SLR + meta-analysis, dual-source search (PubMed + CT.gov), structured synthesis.
2. **Chooses a pattern** — Multi-stage pipeline (like TrialMind-SLR): Search → Screen → Extract → Synthesize, with optional design proposal first (can be skipped if the user effectively says “just build it”).
3. **Plans reuse** — PubMed tools and SLR workflow already exist in TrialMind-SLR (`biodsa/agents/trialmind_slr/tools.py`); CT.gov has a low-level API in `biodsa/tools/clinical_trials/`. So: reuse PubMed + screening + extraction + synthesis tools, add a **CT.gov search tool** and a **meta-analysis** tool.
4. **Follows the checklist** — Create `biodsa/agents/slr_meta/` with `state.py`, `prompt.py`, `tools.py`, `agent.py`, `__init__.py`, `README.md`, `DESIGN.md`, and a top-level `run_slr_meta.py`.

The skill’s **Key Paths** and **Quick-Start Checklist** (propose → implement → document & verify) keep the structure consistent with other BioDSA agents.

### 4. What was built (the SLR-Meta agent)

**Artifacts:**

- **`biodsa/agents/slr_meta/`**
  - **state.py** — State for both sources (`identified_studies`, `ctgov_trials`), screening, extraction, synthesis/meta-analysis.
  - **tools.py** — New `ctgov_search` (wraps `biodsa.tools.clinical_trials.search_trials`), new `meta_analysis` (template for quantitative synthesis); reuse of TrialMind-SLR’s `pubmed_search`, `fetch_abstracts`, screening, extraction, `synthesize_evidence`, `generate_slr_report`.
  - **prompt.py** — Prompts for dual-source search, screening, extraction, synthesis and meta-analysis.
  - **agent.py** — 4-stage LangGraph workflow and `SLRMetaExecutionResults`.
  - **README.md** — Usage and tool list.
  - **DESIGN.md** — Purpose, pattern, workflow (Mermaid), state, tools, input/output.
- **`run_slr_meta.py`** — Example run at repo root.
- **`biodsa/agents/__init__.py`** — Updated to export `SLRMetaAgent`.

**Workflow (high level):**

1. **Search** — PICO-based queries to PubMed and ClinicalTrials.gov; results stored in state.
2. **Screening** — Eligibility criteria applied to titles/abstracts and trial summaries.
3. **Extraction** — Structured data from included studies/trials.
4. **Synthesis** — Narrative synthesis + meta-analysis (pooled estimates, heterogeneity) and final report.

So “vibe prototyping” here meant: one natural-language request → one session with the skill → a full agent that fits the framework and is runnable.

### 5. Run the example agent

From the repo root:

```bash
# Ensure .env has AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT (or other LLM config)
pipenv run python run_slr_meta.py
```

In code:

```python
from biodsa.agents.slr_meta import SLRMetaAgent

agent = SLRMetaAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    max_search_results=20,
    max_ctgov_results=20,
)

results = agent.go(
    research_question="What is the efficacy and safety of CAR-T cell therapy in relapsed/refractory B-cell lymphoma?",
    target_outcomes=["overall_response_rate", "complete_response", "overall_survival", "cytokine_release_syndrome"],
)

print(results.final_report)
# results.identified_pubmed, results.identified_ctgov, results.included_studies
```

### 6. Try it yourself: a prompt you can use

After installing the skill (e.g. `./install-cursor.sh`), open a chat in Cursor and try a prompt like:

- *"Create a new agent that searches PubMed and ClinicalTrials.gov to do systematic literature review and meta-analysis to synthesize clinical evidence for a given research question."*

Or shorten to:

- *"Build an agent that does SLR and meta-analysis using PubMed and CT.gov for a research question."*

You can then:

- Ask for a **design proposal** first (workflow diagram, tools, state) and then say “proceed.”
- Or say **“just build it”** to skip the proposal and go straight to implementation.
- After it’s built, run `run_slr_meta.py` (or the new run script the assistant adds) and iterate on prompts/tools if needed.

### 7. Flow summary

```
You describe the agent (natural language)
         ↓
Assistant uses BioDSA Agent Development Skill
         ↓
Proposal (optional) → Implement → Document
         ↓
biodsa/agents/<name>/ + run_<name>.py
         ↓
Run & iterate
```

### 8. Where to read more

- **Main README**: [../README.md](../README.md) — Motivation, flow diagram, install, benchmarking.
- **Skill library**: [../biodsa-agent-dev-skills/](../biodsa-agent-dev-skills/) — When to use the skill, repository overview, key paths, checklist (propose → implement → document & verify).
- **SLR-Meta agent**: [../biodsa/agents/slr_meta/README.md](../biodsa/agents/slr_meta/README.md) and [DESIGN.md](../biodsa/agents/slr_meta/DESIGN.md) — Concrete outcome of the vibe-prototyping example above.

Using this session as the example, vibe prototyping with skills and the BioDSA framework is: **install skills → describe your agent → let the assistant follow the skill → run and refine.**
