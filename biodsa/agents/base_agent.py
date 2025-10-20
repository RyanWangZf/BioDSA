import os
import logging
from typing import Dict, Any, Callable, Literal, List
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.tools import BaseTool
from langchain_anthropic import ChatAnthropic
# from langchain_together import Together
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import BaseMessage
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper, UploadDataset
from biodsa.agents.state import CodeExecutionResult

def run_with_retry(func: Callable, max_retries: int = 5, min_wait: float = 30.0, max_wait: float = 90.0, arg=None, **kwargs):
    """
    Execute a function with exponential backoff and jitter using tenacity.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        arg: Single positional argument to pass to the function (if needed)
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function if successful
        
    Raises:
        Exception: If all retries fail
    """
    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_random_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def wrapped_func():
        try:
            if arg is not None:
                return func(arg)
            else:
                return func(**kwargs)
        except Exception as e:
            logging.warning(f"Retry triggered: {func.__name__} failed with error: {str(e)}")
            raise
        
    return wrapped_func()

class BaseAgent():
    
    system_prompt: str = None
    registered_datasets: List[str] = []
    
    def __init__(
        self,
        api_type: Literal["azure"],
        api_key: str,
        model_name: Literal["gpt-4o", "gpt-4o-mini", "o3-mini"] = None,
        endpoint: str=None,
        max_completion_tokens=5000,
        container_id: str = None,
        **kwargs
    ):

        # initialize the sandbox
        self.sandbox = ExecutionSandboxWrapper(container_id=container_id)

        # get endpoint using model type
        self.endpoint = endpoint
        self.api_key = api_key

        # load model config
        self.model_name = model_name
        
        self.api_type = api_type
        
        self.max_completion_tokens = max_completion_tokens
        
        # get the model            
        self.llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **kwargs
        )

    def _get_model(
            self,
            api: str,
            api_key: str,
            model_name: str,
            endpoint: str = None,
            **kwargs
    ) -> BaseLanguageModel:
        """
        Get the appropriate language model based on the API type
        
        Args:
            api: The API provider ('anthropic', 'openai', 'google', 'azure')
            api_key: The API key for the provider
            model: The model name
            **kwargs: Additional arguments to pass to the model constructor
            
        Returns:
            A language model instance
        """
        if (model_name not in ["o3-mini", "o3-preview"]):
            # remove max_completion_tokens from kwargs since it's not supported
            # by all models
            if "max_completion_tokens" in kwargs:
                del kwargs["max_completion_tokens"]
        
        llm = None
        if (api == "anthropic"):
            llm = ChatAnthropic(
                model=model_name,
                api_key=api_key,
                **kwargs
            )
        elif (api == "openai"):
            llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                **kwargs
            )
        elif (api == "google"): 
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                **kwargs
            )
        elif (api == "azure"):
            llm = AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=model_name,
                api_key=api_key,
                api_version="2024-12-01-preview",
                **kwargs
            )
        else:
            raise ValueError(f"Invalid API: {api}")
        return llm

    def _format_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """
        Format the messages to the format expected by the agent graph.
        """
        outputs = []
        for message in messages:
            msg_content = message.content
            if hasattr(message, "tool_calls"):
                msg_tool_calls = message.tool_calls
                if msg_tool_calls is not None:
                    if not isinstance(msg_tool_calls, list):
                        msg_tool_calls = [msg_tool_calls]
                    tool_call_strs = []
                    for tool_call in msg_tool_calls:
                        tool_call_strs.append(f"\nTool call: {tool_call['name']}\nTool call input: {tool_call['args']}")
                    msg_content += "\n" + "\n".join(tool_call_strs)
            outputs.append({
                "role": message.type,
                "content": msg_content
            })
        return outputs

    def _format_code_execution_results(self, code_execution_results: List[CodeExecutionResult]) -> List[Dict[str, str]]:
        """
        Format the code execution results to the format expected by the agent graph.
        """
        return [res.model_dump() for res in code_execution_results]

    def _call_model(self, model_name: str, messages: List[BaseMessage], tools: List[BaseTool]=None, model_kwargs: Dict[str, Any]=None) -> BaseMessage:
        if tools is None:
            tools = []
        if model_kwargs is None:
            model_kwargs = {}
        llm = self._get_model(
            api=self.api_type,
            model_name=model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )
        if tools:
            llm_with_tools = llm.bind_tools(tools)
            response = run_with_retry(llm_with_tools.invoke, arg=messages)
        else:
            response = run_with_retry(llm.invoke, arg=messages)
        return response

    def generate(self, **kwargs) -> Dict[str, Any]:
        """
        Base method for generating code.
        
        Args:
            input_query: The user query to process
            **kwargs: Additional arguments to pass to the agent graph
            
        Returns:
            Dict[str, Any]: The result from the agent graph or an error dict
        """
        
        assert self.agent_graph is not None, "Agent graph is not set"
        
        # Extract input_query from kwargs
        input_query = kwargs.pop("input_query", None)
        if input_query is None:
            return {"error": "input_query is required"}
        
        try:
            # Prepare inputs for agent graph
            inputs = {
                "messages": [("user", input_query)],
                **kwargs  # Pass remaining kwargs to the agent graph
            }
            
            # Invoke the agent graph and return the result
            result = self.agent_graph.invoke(inputs)
            return result
            
        except Exception as e:
            logging.error(f"Error generating code: {e}")
            raise e

    def register_dataset(self, dataset_dir: str):
        """
        Register a dataset to the agent.
        The dataset is a directory containing the dataset files.
        Only the files with .csv extension will be uploaded.
        
        Args:
            dataset_dir: The path to the dataset directory
        """
        local_table_paths = [os.path.join(dataset_dir, file) for file in os.listdir(dataset_dir)]
        local_table_paths = [file for file in local_table_paths if file.endswith(".csv")]
        target_table_paths = [os.path.join(self.sandbox.workdir, os.path.basename(file)) for file in local_table_paths]
        upload_dataset = UploadDataset(
            local_table_paths=local_table_paths,
            target_table_paths=target_table_paths,
        )

        # if sandbox is not started, start it
        if not self.sandbox.exists():
            self.sandbox.start() # this will start the sandbox if it is not started

        # upload the tables to the sandbox
        res = self.sandbox.upload_tables(upload_dataset)

        # print what tables are uploaded to the sandbox
        logging.info("\n\n".join([f"Uploaded table: {file}" for file in local_table_paths]))
        self.registered_datasets.extend(target_table_paths)
        return True

    def clear_workspace(self):
        """
        Stop the sandbox and clean up the resources.
        """
        self.sandbox.stop()
        logging.info("Sandbox stopped and resources cleaned up")
        return True

    def go(self, input_query: str) -> Dict[str, Any]:
        """
        Go method for the agent.
        """
        raise NotImplementedError("go is not implemented yet")

