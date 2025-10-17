"""
Proposed by:

Wang, Z., et al. (2025). Making Large Language Models Reliable Data Science Copilot for Biomedical Research. Nature Biomedical Engineering.
"""
from biodsa.agents.base_agent import BaseAgent
from biodsa.utils.token_utils import truncate_middle_tokens
from biodsa.agents.state import CodeExecutionResult
from biodsa.agents.dswizard.state import DSWizardAgentState
from biodsa.sandbox.execution import ExecutionResults


PLAN_AGENT_SYSTEM_PROMPT_TEMPLATE = """
"""

CODE_AGENT_SYSTEM_PROMPT_TEMPLATE = """
"""

class DSWizardAgent(BaseAgent):
    name = "dswizard"
    pass