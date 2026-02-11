import os
import logging
import tempfile
import tarfile
from typing import Dict, Any, Callable, Literal, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
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

def run_with_retry(func: Callable, max_retries: int = 5, min_wait: float = 1.0, max_wait: float = 30.0, timeout: Optional[float] = None, arg=None, **kwargs):
    """
    Execute a function with exponential backoff, jitter, and optional timeout using tenacity.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        timeout: Maximum time in seconds to wait for a single function call (default: None for no timeout)
                 Note: Timed-out threads will be orphaned (not forcibly killed) to prevent hanging the main process.
        arg: Single positional argument to pass to the function (if needed)
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function if successful
        
    Raises:
        Exception: If all retries fail or timeout is exceeded
        
    Note:
        When timeout occurs, the function will be retried but the timed-out thread continues running
        in the background. This is a Python limitation - threads cannot be forcibly terminated.
        The executor is shut down without waiting to prevent the main process from hanging.
    """
    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_random_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def wrapped_func():
        try:
            if timeout is not None:
                # Use ThreadPoolExecutor to implement timeout
                executor = ThreadPoolExecutor(max_workers=1)
                try:
                    if arg is not None:
                        future = executor.submit(func, arg)
                    else:
                        future = executor.submit(func, **kwargs)
                    
                    try:
                        result = future.result(timeout=timeout)
                        return result
                    except FuturesTimeoutError:
                        logging.warning(f"Timeout exceeded: {func.__name__} did not complete within {timeout} seconds")
                        # Don't wait for the stuck thread - let it be orphaned
                        future.cancel()  # Try to cancel if not started yet
                        raise TimeoutError(f"{func.__name__} exceeded timeout of {timeout} seconds")
                finally:
                    # Shutdown without waiting for running threads to prevent hanging
                    executor.shutdown(wait=False)
            else:
                # No timeout, execute directly
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
    sandbox: ExecutionSandboxWrapper = None
    workdir: str = None

    def __init__(
        self,
        api_type: Literal["azure"],
        api_key: str,
        model_name: Literal["gpt-4o", "gpt-4o-mini", "o3-mini"] = None,
        endpoint: str=None,
        max_completion_tokens=5000,
        container_id: str = None,
        model_kwargs: Dict[str, Any] = None,
        llm_timeout: Optional[float] = None,
        **kwargs
    ):

        # initialize the sandbox (set to None if Docker is not available or fails)
        try:
            self.sandbox = ExecutionSandboxWrapper(container_id=container_id)
            dsa_tools_installed = self.install_biodsa_tools_in_sandbox()
            if not dsa_tools_installed:
                logging.warning("Failed to install biodsa.tools. Skipping sandbox.")
                self.sandbox = None
            else:
                logging.info("Sandbox initialized successfully and biodsa.tools installed")
        except Exception as e:
            logging.warning(f"Failed to initialize sandbox: {str(e)}")
            logging.warning("Tools will fall back to local execution when possible")
            self.sandbox = None
        
        if self.sandbox is not None:
            self.workdir = self.sandbox.workdir
        else:
            self.workdir = os.path.join(os.getcwd(), "workdir")
            # create the directory if it doesn't exist
            os.makedirs(self.workdir, exist_ok=True)

        # get endpoint using model type
        self.endpoint = endpoint
        self.api_key = api_key

        # load model config
        self.model_name = model_name
        
        self.api_type = api_type
        
        self.max_completion_tokens = max_completion_tokens

        self.model_kwargs = model_kwargs
        
        # Timeout for LLM calls in seconds (default: None for no timeout)
        self.llm_timeout = llm_timeout
        
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
                max_retries=0,
                **kwargs
            )
        elif (api == "openai"):
            llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                max_retries=0,
                **kwargs
            )
        elif (api == "google"): 
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                max_retries=0,
                **kwargs
            )
        elif (api == "azure"):
            # Azure does not support reasoning_effort (OpenAI o1-only parameter)
            kwargs = {k: v for k, v in kwargs.items() if k != "reasoning_effort"}
            llm = AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=model_name,
                api_key=api_key,
                api_version="2024-12-01-preview",
                max_retries=0,
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
            
            # Ensure msg_content is a string (handle cases where it might be a list)
            if isinstance(msg_content, list):
                # Convert list of content blocks to string
                content_parts = []
                for block in msg_content:
                    if isinstance(block, dict):
                        # Handle dict content blocks (e.g., from Claude API)
                        if 'text' in block:
                            content_parts.append(block['text'])
                        elif 'type' in block and block['type'] == 'text' and 'text' in block:
                            content_parts.append(block['text'])
                        else:
                            # For other block types, convert to string
                            content_parts.append(str(block))
                    elif isinstance(block, str):
                        content_parts.append(block)
                    else:
                        content_parts.append(str(block))
                msg_content = "".join(content_parts)
            elif not isinstance(msg_content, str):
                msg_content = str(msg_content)
            
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

    def _call_model(self, model_name: str, messages: List[BaseMessage], tools: List[BaseTool]=None, model_kwargs: Dict[str, Any]=None, parallel_tool_calls: bool=True, api_type: str=None, api_key: str=None, endpoint: str=None) -> BaseMessage:
        if tools is None:
            tools = []
        if model_kwargs is None:
            model_kwargs = self.model_kwargs
        else:
            model_kwargs = self._set_model_kwargs(model_name)
        if api_type is None:
            api_type = self.api_type
        if api_key is None:
            api_key = self.api_key
        if endpoint is None:
            endpoint = self.endpoint
        llm = self._get_model(
            api=api_type,
            model_name=model_name,
            api_key=api_key,
            endpoint=endpoint,
            **model_kwargs
        )
        if tools:
            llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=parallel_tool_calls)
            response = run_with_retry(llm_with_tools.invoke, arg=messages, timeout=self.llm_timeout)
        else:
            response = run_with_retry(llm.invoke, arg=messages, timeout=self.llm_timeout)
        return response

    def _get_input_output_tokens(self, response: BaseMessage) -> Tuple[int, int]:
        """
        Get the input and output tokens from the response.
        """
        return response.usage_metadata.get("input_tokens", 0), response.usage_metadata.get("output_tokens", 0)

    def _set_model_kwargs(self, model_name: str) -> Dict[str, Any]:
        """
        A function to set the model kwargs for the agent.
        """
        model_kwargs = {}
        if "claude" in model_name.lower():
            model_kwargs["thinking"] = {"type": "enabled", "budget_tokens": 5000}
            model_kwargs["max_tokens"] = 10000
            model_kwargs.pop("reasoning_effort", None)
        if "gpt" in model_name.lower():
            model_kwargs["reasoning_effort"] = "medium"
            model_kwargs.pop("thinking", None)
            model_kwargs["max_completion_tokens"] = 5000
        return model_kwargs

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

    def install_biodsa_tools_in_sandbox(self) -> bool:
        """
        Install biodsa.tools module in the sandbox.
        This allows using 'from biodsa.tools import xxx' in sandbox code.
        
        The installation is lightweight - only includes the tools module, 
        not agents or sandbox code, and doesn't require heavy dependencies like langchain_core.
        
        Returns:
            bool: True if installation was successful, False otherwise
        """
        # Check if sandbox is available
        if self.sandbox is None:
            logging.warning("Sandbox is not available. Cannot install biodsa.tools.")
            return False
        
        logging.info("Installing biodsa.tools module in sandbox...")
        
        # Get the biodsa package directory
        # Current file is at: biodsa/agents/base_agent.py
        current_file = os.path.abspath(__file__)
        biodsa_package_dir = os.path.dirname(os.path.dirname(current_file))  # biodsa/
        tools_dir = os.path.join(biodsa_package_dir, "tools")
        
        if not os.path.exists(tools_dir):
            logging.warning(f"biodsa/tools directory not found at {tools_dir}. Skipping tools installation.")
            return False
        
        # Create a tar.gz with minimal structure: biodsa/__init__.py and biodsa/tools/
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_tar:
            tar_path = tmp_tar.name
            
        try:
            with tarfile.open(tar_path, 'w:gz') as tar:
                # Add biodsa/__init__.py (empty or minimal)
                biodsa_init_path = os.path.join(biodsa_package_dir, "__init__.py")
                if os.path.exists(biodsa_init_path):
                    tar.add(biodsa_init_path, arcname='biodsa/__init__.py')
                else:
                    # Create empty __init__.py in memory
                    init_info = tarfile.TarInfo(name='biodsa/__init__.py')
                    init_info.size = 0
                    tar.addfile(init_info, fileobj=None)
                
                # Add the entire biodsa/tools directory
                tar.add(tools_dir, arcname='biodsa/tools')
            
            # Upload tar to sandbox
            self.sandbox.upload_file(
                local_file_path=tar_path,
                target_file_path=f"{self.sandbox.workdir}/biodsa_tools.tar.gz"
            )
            logging.info("Uploaded biodsa.tools module to sandbox")
            
        finally:
            # Clean up temp file
            if os.path.exists(tar_path):
                os.unlink(tar_path)
        
        # Extract the tools
        extract_cmd = "tar -xzf biodsa_tools.tar.gz"
        exit_code, output = self.sandbox.container.exec_run(
            extract_cmd, 
            workdir=self.sandbox.workdir
        )
        output_str = output.decode('utf-8')
        
        if exit_code != 0:
            logging.error(f"Failed to extract biodsa.tools: {output_str}")
            return False
        
        logging.info("Successfully extracted biodsa.tools module")
        
        # Add workdir to Python path using .pth file
        # This is the most reliable way to ensure imports work in all contexts
        pth_commands = [
            # Find the site-packages directory
            'python -c "import site; print(site.getsitepackages()[0])"',
        ]
        
        # Get site-packages path
        exit_code, output = self.sandbox.container.exec_run(
            pth_commands[0],
            workdir=self.sandbox.workdir
        )
        
        if exit_code != 0:
            logging.error(f"Failed to find site-packages: {output.decode('utf-8')}")
            return False
        
        site_packages = output.decode('utf-8').strip()
        
        # Create .pth file to add workdir to sys.path
        pth_file_path = f"{site_packages}/biodsa_tools.pth"
        create_pth_cmd = f'echo "{self.sandbox.workdir}" > {pth_file_path}'
        
        exit_code, output = self.sandbox.container.exec_run(
            f'sh -c \'{create_pth_cmd}\'',
            workdir=self.sandbox.workdir
        )
        
        if exit_code != 0:
            logging.error(f"Failed to create .pth file: {output.decode('utf-8')}")
            return False
        
        logging.info(f"Created .pth file at {pth_file_path}")
        logging.info(f"biodsa.tools module installed in sandbox at {self.sandbox.workdir}/biodsa")
        logging.info("You can now use 'from biodsa.tools import xxx' in your sandbox code")
        return True

    def register_workspace(self, workspace_dir: str = None, install_biodsa_tools: bool = True):
        """
        Register a workspace (a sandbox) to the agent.
        The dataset (.csv) under the workspace_dir will be collected and uploaded to the sandbox.
        
        Args:
            workspace_dir: The path to the workspace directory in local machine
            install_biodsa_tools: Whether to install biodsa.tools module in the sandbox (default: True)
                                 This allows using 'from biodsa.tools import xxx' in sandbox code
        """
        # Check if sandbox is available
        if self.sandbox is None:
            logging.warning("Sandbox is not available. Skipping workspace registration.")
            logging.warning("Tools will execute locally when possible.")
            return False
        
        # if sandbox is not started, start it
        if not self.sandbox.exists():
            self.sandbox.start()  # this will start the sandbox if it is not started

        # Install biodsa.tools module in the sandbox (lightweight, only tools, no agents/sandbox code)
        if install_biodsa_tools:
            self.install_biodsa_tools_in_sandbox()

        # upload the tables to the sandbox
        if workspace_dir is not None:
            local_table_paths = [os.path.join(workspace_dir, file) for file in os.listdir(workspace_dir)]
            local_table_paths = [file for file in local_table_paths if file.endswith(".csv")]
            target_table_paths = [os.path.join(self.sandbox.workdir, os.path.basename(file)) for file in local_table_paths]
            upload_dataset = UploadDataset(
                local_table_paths=local_table_paths,
                target_table_paths=target_table_paths,
            )
            res = self.sandbox.upload_tables(upload_dataset)
            # print what tables are uploaded to the sandbox
            logging.info("\n\n".join([f"Uploaded table: {file}" for file in local_table_paths]))
            self.registered_datasets.extend(target_table_paths)

        return True

    def clear_workspace(self):
        """
        Stop the sandbox and clean up the resources.
        """
        if self.sandbox is None:
            logging.warning("Sandbox is not available. Nothing to clear.")
            return False
            
        self.sandbox.stop()
        logging.info("Sandbox stopped and resources cleaned up")
        return True

    def go(self, input_query: str) -> Dict[str, Any]:
        """
        Go method for the agent.
        """
        raise NotImplementedError("go is not implemented yet")

