import re
import logging
from typing import Dict, Any, List, Literal
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry, cut_off_tokens
from biodsa.agents.state import FinalResponse, AgentState, CodeResult
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper


class FinalResponseForStructuring(BaseModel):
    """
    Used for generating the final response from the structured output of the model.
    """
    final_answer: Literal["True", "False", "Not Verifiable"]
    analysis: List[str]
    def __str__(self):
        return f"Final Answer: {self.final_answer}\n Analysis: {self.analysis}"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SYSTEM_PROMPT = """
# TASK
Given the user's ask, you write python code which will be executed to answer the user's question.

# IMPORTANT: CODE OUTPUT REQUIREMENTS
You must import all the necessary libraries at the beginning of your code.

You must use explicit print() statements for ALL outputs you want to see or analyze. Simply writing expressions like 'df.head()' will NOT show results in the execution log. Always use:
- print(df.head())
- print(analysis_result)
- print(statistical_test_output)
Every intermediate result and final output must be wrapped in a print() statement to be visible in the execution log.
You should avoid adding any comments in the code to reduce the size of the code.

## Ouptut
Your output should be in Markdown format and you should wrap the generated code in ```python ``` tags.
"""

FINAL_ANSWER_PROMPT = """
# TASK
Evaluate the user's ask taking into account the evidence provided.

# IMPORTANT
You should make your final answer completely based on the observations provided.
Do not make any assumptions or include any other information which is not included in the observations.

# FINAL ANSWER
The final answer is one of the following values:

True - the hypothesis is supported by the data
False - the hypothesis is not supported by the data
Not Verifiable - The hypothesis is not verifiable with the provided datasets

As a part of the final answer, you must output
- analysis: a list of concise analyses that justifies your evaluation of the hypothesis
- final_answer: one of the following values: True, False, Not Verifiable
"""

class CoderAgent(BaseAgent):
    
    name = "baseline_coder_agent"

    def __init__(
        self, 
        model_name: str, 
        api_type: str,
        api_key: str,
        endpoint: str,
        language: str = "python",
        sandbox: ExecutionSandboxWrapper = None
    ):
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
        )
        
        assert language in ["python"], "Language is not supported"
        self.language = language

        # if it is not None, the sandbox will be used for executing the code
        # otherwise, it will only generate the code
        self.sandbox = sandbox

        self.agent_graph = self.create_agent_graph()
            
    
    def generate_code(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> AgentState:
        """
        A function to generate the code for the agent.
        """
        messages = state.messages        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
        ] + messages

        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})

        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )
        result = run_with_retry(llm.invoke, arg=messages)

        code = result.content
        code_blocks = re.findall(rf"```{self.language}(.*?)```", code, flags=re.DOTALL | re.IGNORECASE)
        combined_code = "\n\n".join(block.strip() for block in code_blocks)
        
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory_mb = self.sandbox.execute(
                language=self.language,
                code=combined_code
            )
            stdout = cut_off_tokens(output, 4096)
            peak_memory = peak_memory_mb
            
            # Log execution metrics
            logging.info(f"Execution completed in {running_time:.2f}s, peak memory: {peak_memory:.2f} MB")
        else:
            stdout = ""
            running_time = 0.0
            peak_memory = 0.0

        # attach the output message to the messages
        output_message = AIMessage(content=f"# Executed code:\n\n```python\n{combined_code}``` \n\n # Console Output:\n\n {stdout}   ")        
        return {
            "code_results": [CodeResult(
                code=combined_code,
                console_output=stdout,
                running_time=running_time,
                peak_memory=peak_memory,
            )],
            "messages": [output_message],
        }

    def generate_structured_response(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> FinalResponse:

        # use the final response model to generate the final response
        llm = self.get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            max_completion_tokens=5000,
        )
        
        model_with_structured_output = llm.with_structured_output(FinalResponseForStructuring)
        
        messages = state.messages
        
        messages = [
            SystemMessage(content=FINAL_ANSWER_PROMPT),
        ] + messages
        
        response = run_with_retry(model_with_structured_output.invoke, arg=messages)
        
        return FinalResponse(
            executions=state.code_results,
            final_answer=response.final_answer,
            analysis=response.analysis
        )

    def create_agent_graph(self, debug: bool = False) -> StateGraph:    
        # the actual agent workflow graph
        workflow = StateGraph(
            AgentState,
            input=AgentState,
            output=FinalResponse
        )
        
        workflow.add_node("generate_code", self.generate_code)
        workflow.add_node("generate_structured_response", self.generate_structured_response)
        
        workflow.add_edge("generate_code", "generate_structured_response")
        workflow.add_edge("generate_structured_response", END)
        
        workflow.set_entry_point("generate_code")
        
        workflow = workflow.compile(
            debug=debug,
            name=self.name
        )
        return workflow
    
    def generate(
        self,
        input_query: str
    ) -> Dict[str, Any]:
        """
        Override the base method for generating code.
        
        Args:
            input_query: The user query to process
        """
        assert self.agent_graph is not None, "Agent graph is not set"
        
        # Extract input_query from kwargs
        if input_query is None:
            return {"error": "input_query is required"}
        
        try:
            inputs = {
                "messages": [("user", input_query)]
            }
        
            # Invoke the agent graph and return the result
            result = self.agent_graph.invoke(
                inputs,
                config={
                    "configurable": {
                        "model_kwargs": {
                            "max_completion_tokens": 5000,
                            "reasoning_effort": "minimal",
                            "temperature": 1.0
                        }
                    },
                    "recursion_limit": 20
                }
            )
            return result
            
        except Exception as e:
            print(f"Error streaming code: {e}")
            raise e
    