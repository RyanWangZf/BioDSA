from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import InjectedToolArg
from typing import Annotated, Type
from pydantic import BaseModel, Field

from biodsa.utils.token_utils import truncate_middle_tokens
from biodsa.agents.base_agent import run_with_retry

PLAN_GENERATION_SYSTEM_PROMPT_TEMPLATE = """
You are a precise and obedient assistant responsible for creating a structured analysis plan.

You are given these inputs:
1. INSTRUCTIONS: A concise description of the key logical steps to be included in the analysis plan (must be less than 100 words). Be concise while keeping all the table, column, value references intact.
2. CONTEXT_STR: A string that contains the context which covers the previous dataset exploration results.

Your task is to create a new analysis plan following the instructions and pull the information from the context.
You should reflect the successful and failed runs in the context so to enrich the analysis plan with the necessary hints, including but not limited to:
- the table, column, value references
- the library imports
- the right way to use the external library
- the right way to process the dataset
- etc.
 for successful execution of the analysis plan in the future.

Your analysis plan should be natural language and should be easy to understand by a non-technical user.
In this sense, it should not contain excessive code snippets or code blocks. Instead, it is only allowed to have pseudo code to describe the logics and include key function names.
Your analysis plan should be less than 1000 words.

# OUTPUT FORMAT
Your output should start from a tag <analysis_plan> and end with a tag </analysis_plan>. Do not include any other text or tags in your output.
For example,
<analysis_plan>
1. load the dataset
2. print hello world
</analysis_plan>
"""

INSTRUCTIONS_GUIDANCE = """
"A concise description of the key logical steps to be included in the analysis plan (must be less than 200 words).

Cover the following aspects:
- concisely the key logical steps
- the key table, column, value references
- the key library imports
- the guidance on how to use the external library
- the guidance on how to process the dataset
- etc.
"""

class AnalysisPlanToolInput(BaseModel):
    """Input for the update current analysis plan tool"""
    instructions: str = Field(..., description=INSTRUCTIONS_GUIDANCE)

class AnalysisPlanTool(BaseTool):
    name: str = "create_analysis_plan"
    description: str = "A tool to create a step-by-step analysis plan written in natural language to ensure it can be faithfully implemented as Python code."
    args_schema: Type[BaseModel] = AnalysisPlanToolInput
    
    llm: BaseChatModel = None

    def __init__(self, llm: BaseChatModel):
        super().__init__()
        self.llm = llm

    def _run(self, instructions: str, context_str: Annotated[str, InjectedToolArg]) -> str:
        context_str = truncate_middle_tokens(context_str, 4096)
        context_str = f"CONTEXT_STR: \n\n{context_str}"
        instructions = f"INSTRUCTIONS: \n\n{instructions}"
        messages = [
            SystemMessage(content=PLAN_GENERATION_SYSTEM_PROMPT_TEMPLATE),
            HumanMessage(content=context_str),
            HumanMessage(content=instructions),
        ]
        result = run_with_retry(self.llm.invoke, arg=messages)
        return result.content