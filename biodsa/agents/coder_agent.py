import re
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry, cut_off_tokens
from biodsa.agents.state import AgentState, CodeExecutionResult
from biodsa.sandbox.execution import ExecutionResults

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SYSTEM_PROMPT_TEMPLATE = """
# TASK: Given the user's ask, you must write {language} code which will be executed to answer the user's question.

# IMPORTANT: CODE OUTPUT REQUIREMENTS
You must import all the necessary libraries at the beginning of your code.

You must use explicit print() statements for ALL outputs you want to see or analyze. Simply writing expressions like 'df.head()' will NOT show results in the execution log. Always use:
- print(df.head())
- print(analysis_result)
- print(statistical_test_output)
Every intermediate result and final output must be wrapped in a print() statement to be visible in the execution log.
You should avoid adding any comments in the code to reduce the size of the code.

# Available data:
You have access to the following data when executing the code:
{registered_datasets_str}

## Ouptut
Your output should be in Markdown format and you should wrap the generated code in ```{language} ``` tags.
"""

FINAL_ANSWER_PROMPT = """
# TASK: Please try to answer the user's question based on the code execution results.
"""

class CoderAgent(BaseAgent):
    
    name = "coder_agent"
    system_prompt = SYSTEM_PROMPT_TEMPLATE

    def __init__(
        self, 
        model_name: str, 
        api_type: str,
        api_key: str,
        endpoint: str,
        language: str = "python",
        container_id: str = None,
        **kwargs
    ):
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
        )
        
        assert language in ["python"], f"Language {language} is not supported"
        self.language = language
        self.agent_graph = self._create_agent_graph()

    def _build_system_prompt(self):
        registered_datasets_str = "\n".join([f"- {dataset}" for dataset in self.registered_datasets])
        return SYSTEM_PROMPT_TEMPLATE.format(language=self.language, registered_datasets_str=registered_datasets_str)
            
    def _generate_code(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> AgentState:
        """
        A function to generate the code for the agent.
        """
        messages = state.messages        
        messages = [
            SystemMessage(content=self._build_system_prompt()),
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
            "code_execution_results": [CodeExecutionResult(
                code=combined_code,
                console_output=stdout,
                running_time=running_time,
                peak_memory=peak_memory,
            )],
            "messages": [output_message],
        }

    def _generate_final_response(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> AgentState:
        """
        A function to generate the final response for the agent.
        """
        messages = state.messages
        messages = [
            SystemMessage(content=FINAL_ANSWER_PROMPT),
        ] + messages
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )
        response = run_with_retry(llm.invoke, arg=messages)
        return {
            "messages": [response],
        }

    def _create_agent_graph(self, debug: bool = False) -> StateGraph:    
        # the actual agent workflow graph
        workflow = StateGraph(
            AgentState,
            input=AgentState,
            output=AgentState
        )
        
        workflow.add_node("generate_code", self._generate_code)
        workflow.add_node("generate_final_response", self._generate_final_response)
        
        workflow.add_edge("generate_code", "generate_final_response")
        workflow.add_edge("generate_final_response", END)
        
        workflow.set_entry_point("generate_code")
        
        workflow = workflow.compile(
            debug=debug,
            name=self.name
        )
        return workflow
    
    def generate(
        self,
        input_query: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        A function to generate the code for the agent.
        
        Args:
            input_query: The user query to process
        """
        assert self.agent_graph is not None, "Agent graph is not set"
        
        # Extract input_query from kwargs
        if input_query is None:
            return {"error": "input_query is required"}
        
        try:
            all_results = []
            inputs = {
                "messages": [("user", input_query)]
            }
        
            # Invoke the agent graph and return the result
            for stream_mode, chunk in self.agent_graph.stream(
                inputs,
                stream_mode = ["values"],
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
                ):
                if verbose:
                    last_message = chunk['messages'][-1]
                    print("-" * 100)
                    print(f"{last_message.type}: \n\n{last_message.content}\n\n")
                    all_results.append(chunk)
            return all_results
            
        except Exception as e:
            print(f"Error streaming code: {e}")
            raise e

    def go(
        self,
        input_query: str,
        verbose: bool = True
    ) -> ExecutionResults:
        """
        A function to execute the agent and return the execution results.
        
        Args:
            input_query: The user query to process
        """
        results = self.generate(input_query, verbose=verbose)
        # prepare the execution results
        final_state = results[-1]
        message_history = self._format_messages(final_state['messages'])
        code_execution_results = self._format_code_execution_results(final_state['code_execution_results'])
        final_response = final_state['messages'][-1].content

        return ExecutionResults(
            sandbox=self.sandbox,
            message_history=message_history,
            code_execution_results=code_execution_results,
            final_response=final_response
        )