import pdb
import os
import re
from typing import Callable, Iterator, List, Dict, Optional, Tuple, Union
from bs4 import BeautifulSoup
import pandas as pd

from .memory_utils import (
    combine_chat_history,
    combine_dataframes,
    combine_code_history,
)
from .llm import (
    call_llm,
    batch_call_llm,
)
from .schema import CodeSnippet, Dataframe, Message

# prevent matplotlib from generating plots through the UI
import matplotlib
matplotlib.use('Agg')  # set the backend before importing pyplot

from logging import getLogger
logger = getLogger(__name__)


def fix_print_statements(code):
    fixed_code_lines = []
    open_print = False
    temp_line = ""

    for line in code.split('\n'):
        stripped_line = line.strip()
        if stripped_line.startswith('print(') and not stripped_line.endswith(')'):
            open_print = True
            temp_line = line
        elif open_print:
            temp_line += ' ' + line
            if stripped_line.endswith(')'):
                fixed_code_lines.append(temp_line)
                open_print = False
                temp_line = ""
        else:
            fixed_code_lines.append(line)

    if open_print:
        fixed_code_lines.append(temp_line)

    return '\n'.join(fixed_code_lines)

def fix_logging_statements(code):
    fixed_code_lines = []
    open_print = False
    temp_line = ""

    for line in code.split('\n'):
        stripped_line = line.strip()
        if (stripped_line.startswith('logging.') or stripped_line.startswith('logger.') ) \
            and not stripped_line.endswith(')'):
            open_print = True
            temp_line = line
        elif open_print:
            temp_line += ' ' + line
            if stripped_line.endswith(')'):
                fixed_code_lines.append(temp_line)
                open_print = False
                temp_line = ""
        else:
            fixed_code_lines.append(line)

    if open_print:
        fixed_code_lines.append(temp_line)

    return '\n'.join(fixed_code_lines)

def remove_unclosed_backticks(text):
    import re
    
    # Find all triple backtick occurrences
    triple_backticks = [match.start() for match in re.finditer(r'```', text)]
    
    # Initialize a list to keep track of backtick pairs
    stack = []
    to_remove = []
    
    # Iterate through the indices of triple backticks
    for index in triple_backticks:
        if stack and stack[-1][1] == 'open':
            stack[-1][1] = 'closed'
        else:
            stack.append([index, 'open'])
    
    # Collect indices of unclosed backticks
    to_remove = [index for index, status in stack if status == 'open']
    
    # Remove unclosed backticks from the original text
    for index in sorted(to_remove, reverse=True):
        text = text[:index] + text[index+3:]
    
    return text

def extract_code(_raw_output: str) -> str:
    if pd.isna(_raw_output) or _raw_output is None:
        _raw_output =  ""

    if "```html" in _raw_output:
        _raw_output = _raw_output.replace("```html", "```")

    try:
        # use regex to extract all the code snippets wrapped by <code> tag
        pattern = r"<code>(.*?)</code>"
        matches = re.findall(pattern, _raw_output, re.DOTALL)
        if len(matches) > 0:
            combined_snippets = '\n'.join(matches)
            _raw_output = combined_snippets
        _raw_output = remove_unclosed_backticks(_raw_output)
        # soup = BeautifulSoup(_raw_output, "html.parser")
        # _raw_output = soup.find("code").text
    except:
        _raw_output = _raw_output

    if "```" in _raw_output:
        pattern = r"```(?:python|r|R)?\s*(.*?)(?:\s*```|$)"
        matches = re.findall(pattern, _raw_output, re.DOTALL)
        if len(matches) > 0:
            combined_snippets = '\n'.join(matches)
            _raw_output = combined_snippets

    # fix the split strings bugs
    _raw_output = _raw_output.replace("\\n", "\n")
    _raw_output = fix_print_statements(_raw_output)
    _raw_output = fix_logging_statements(_raw_output)
    return _raw_output

class CodeSnippetRetriever:
    """Get user input, retrieve code snippets from the local code database, 
    return code snippets to the user.

    It has two steps:
    (1) decide which data story this user's request is most likely to be related to;
    (2) retrieve the code snippets that belong to this data story (filter + rank)

    If `query` is None, then user must pass the `filters` or `ids` to retrieve the code snippets through
    the given doc ids or data story. `top_k` is then ignored.

    Args:
        query (str): user's question in natural language
        top_k (int): number of code snippets to return
        filters (dict): filter the code snippets by their metadata, e.g., {"data_story": "car-t-scrs-analysis"}
        ids: (list): list of doc ids (e.g., ["doc_1", "doc_2"])

    Returns:
        list: list of code snippets
    """

    def __init__(
        self,
        persist_directory,
    ) -> None:
        # load the code database index to the memory
        from .code_database import load_code_snippet_index
        self.db = load_code_snippet_index(persist_directory)

    def run(self,
            query: str = None,
            top_k: int = 5,
            filters: dict = {},
            ids: List[str] = [],
            ):
        """Retrieve code snippets from the local code database.
        """
        if query is None:
            # get the code snippets based on the filters directly if we apply filters
            ret_docs = self.db.get(where=filters, ids=ids)
            ret_docs = {k: v for k, v in ret_docs.items() if v is not None}
            ret_docs = [dict(zip(ret_docs, t))
                        for t in zip(*ret_docs.values())]
            code_snippets = []
            for doc in ret_docs:
                code_snippets.append(self._build_snippet(doc, score=None))
            return code_snippets

        test_docs = self.db.similarity_search_with_relevance_scores(
            query, k=top_k, filter=filters)
        code_snippets = []
        for doc, score in test_docs:
            code_snippets.append(self._build_snippet(doc, score))
        return code_snippets

    def _build_snippet(self, doc, score):
        metadata = doc.metadata
        dependency = metadata.pop("dependency", None)
        if dependency is not None:
            dependency = dependency.split(",")
        else:
            dependency = []
        imported = metadata.pop("imported", None)
        if imported is not None:
            imported = imported.split(",")
        else:
            imported = []
        snippet = {
            "relevance_score": score,
            "code_snippet": doc.page_content,
            "dependency": dependency,
            "imported": imported,
        }
        snippet.update(metadata)
        return snippet


class CodeGeneration:
    """Generate exeuctable code based on input user question and code blocks.

    It supports two functionalities:
    (1) generate code based on the input user question;
    (2) interactively edit the target code if the parameter `code` is not None;
    (3) if `ctx_blocks` is given, they will be used to guide LLM to adjust the code generation considering the context.
    (4) if `dataframes` is given, they will be used to guide LLM to generate code to execute on the given dataframes.

    `ctx_blocks` are code blocks in the context of the target code to guide the code generation. Each block is a dictionary with the following keys:
    - code_snippet: the source code of the code block
    - desc: the description of the code block
    - imported: a list of imported functions, classes, or variables in string format

    `dataframes` are standard dataframes defined in ADaM and SDTM standards, e.g., adsl, adae, adcm, adex, adlbmi, admh, adpr, adrs, advs, etc.
    It should be defined as a list of dictionaries, each dictionary has the following keys:
    - name: the name of the dataframe
    - schema (optional): the dictionary of column names and their properties

    Args:
        query (str): user's question in natural language
        chat_history (List[Message]): list of messages representing the chat history in the context
        dataframes (List[Dict]): list of dataframes and its schema in the context that the code will be executed on
        reference_code (str): the target code string
        code_history (List[Dict]): list of code blocks in the context of the target code to guide the code generation
        llm (str): the name of the LLM model to be used. Currently, only "gpt-4" and "gpt-35" is available.
        streaming (bool): whether to use streaming mode. The default value is False.
        language (str): the programming language of the code to be generated. The default value is "python".
            support languages: "python", "R".
        debug (bool): whether to enable the debug mode. The default value is False. If True, LLM will take the
            reference_code as the input and try to debug it. The debugging error needs to passed to `query`.
            The other parameters are optional.
    Returns:
        str: the generated code
    """

    def __init__(self) -> None:
        pass

    def run(
        self,
        query: str,
        chat_history: List[Message] = [],
        dataframes: List[Dataframe] = [],
        reference_code: Union[CodeSnippet, str] = "",
        code_history: List[Union[CodeSnippet,str]] = [],
        llm: str = "gpt-4",
        streaming: bool = False,
        language = "python",
        debug = False,
        temperature = 0.0,
        num_return_samples = 1, # n for openai chat completions
    ):
        # revisit once ds codegen is complete
        # get the schema of the input dataframes
        context_strs = self._build_context_str(chat_history, code_history, dataframes)
        chat_history_str = context_strs["chat"]
        code_history_str = context_strs["code"]
        schema_str = context_strs["data"]

        # build the code generation prompt
        if not debug:
            language = language.lower()
            if language == "python":
                prompt_template = self.create_python_prompt()
            elif language == "r":
                prompt_template = self.create_r_prompt()
            else:
                raise ValueError(f"Language {language} is not supported. Please use 'python' or 'R'.")
            
            # call LLM to generate the code
            outputs = call_llm(
                prompt_template,
                {
                    "chat_history": chat_history_str,
                    "history_code": code_history_str,
                    "question": query,
                    "data": schema_str,
                    "reference_code": reference_code,
                },
                llm=llm,
                streaming=streaming,
                stop_words=["</code>"],
                n = num_return_samples,
                temperature=temperature
            )

        else:
            prompt_template = self.create_debug_prompt()
            # call LLM to generate the code
            outputs = call_llm(
                prompt_template,
                {
                    "question": query,
                    "data": schema_str,
                    "reference_code": reference_code,
                },
                llm=llm,
                streaming=streaming,
                stop_words=["</code>"],
                n = num_return_samples,
                temperature=temperature
            )


        if streaming:
            # return the streaming response
            return {
                "output": self.streaming_with_code_cleanup(outputs, cleanup_fn=self._cleanup)
            }

        else:
            if isinstance(outputs, str):
                outputs = [outputs]

            # parse outputs
            results = []
            for output in outputs:
                code = self._cleanup(output)
                results.append(
                    {"output": code}
                )

            if len(results) == 1:
                return results[0]
            else:
                return results

    def batch_run(self,
        queries: List[str],
        chat_histories: List[List[Message]],
        dataframes: List[List[Dataframe]],
        reference_codes: List[Union[CodeSnippet, str]],
        code_histories: List[List[Union[CodeSnippet,str]]],
        llm: str = "openai-gpt-4o",
        language = "python",
        debug = False,
        batch_size = None,
        temperature = 0.0,
        ):
        """Used to run experiments in a batch.
        """
        if not debug:
            language = language.lower()
            if language == "python":
                prompt_template = self.create_python_prompt()
            elif language == "r":
                prompt_template = self.create_r_prompt()
            else:
                raise ValueError(f"Language {language} is not supported. Please use 'python' or 'R'.")
        else:
            prompt_template = self.create_debug_prompt(language)

        batch_inputs = []
        for i, query in enumerate(queries):
            chat_history = []
            if chat_histories is not None:
                chat_history = chat_histories[i]
            reference_code = ""
            if reference_codes is not None:
                reference_code = reference_codes[i]
            code_history = []
            if code_histories is not None:
                code_history = code_histories[i]

            dataframes_ = dataframes[i]
            context_strs = self._build_context_str(chat_history, code_history, dataframes_)
            chat_history_str = context_strs["chat"]
            code_history_str = context_strs["code"]
            schema_str = context_strs["data"]

            if not debug:
                # build batch inputs
                batch_inputs.append({
                    "chat_history": chat_history_str,
                    "history_code": code_history_str,
                    "question": query,
                    "data": schema_str,
                    "reference_code": reference_code,
                })

            else:
                # build batch inputs for debug
                batch_inputs.append({
                    "question": query,
                    "data": schema_str,
                    "reference_code": reference_code,
                })
        

        # call LLM to generate the code
        outputs = batch_call_llm(
            prompt_template,
            batch_inputs,
            llm=llm,
            temperature=temperature,
            batch_size=batch_size,
        )
        
        # parse outputs
        results = []
        for output in outputs:
            code = self._cleanup(output)
            results.append(
                {"output": code}
            )
        return results

    def create_python_prompt(self):
        # 1. build the prompt
        from .prompts.python.manual import USER_PROMPT, SYSTEM_PROMPT
        from langchain_core.prompts.chat import ChatPromptTemplate
        from langchain_core.prompts.chat import SystemMessage, HumanMessagePromptTemplate
        input_variables = ["history_code", "question", "data", "reference_code", "chat_history"]
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(template=USER_PROMPT),
        ]
        prompt_template = ChatPromptTemplate(
            input_variables=input_variables, messages=messages)
        return prompt_template
    
    def create_r_prompt(self):
        from .prompts.R.manual import USER_PROMPT, SYSTEM_PROMPT

        # 1. build the prompt
        from langchain_core.prompts.chat import ChatPromptTemplate
        from langchain_core.prompts.chat import SystemMessage, HumanMessagePromptTemplate
        input_variables = ["history_code", "question", "data", "reference_code", "chat_history"]
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(template=USER_PROMPT),
        ]
        prompt_template = ChatPromptTemplate(
            input_variables=input_variables, messages=messages)
        return prompt_template
    
    def create_debug_prompt(self, language="python"):
        from .prompts.python.manual import DEBUG_PROMPT_UT, DEBUG_PROMPT_PT
        return DEBUG_PROMPT_PT

    def _cleanup(self, output: str) -> str:
        """
        Clean up the code snippets in the output.
        """
        return extract_code(output)

    def streaming_with_code_cleanup(self, output_stream: Iterator[str], cleanup_fn: Callable[[str], str]) -> Iterator[Tuple[bool, str]]:
        """Stream the output from the LLM and clean up the code snippets.
        output_stream: the output stream from the LLM
        cleanup_fn: the function to clean up the code snippets. This function is applied to the aggregated output string.
        The cleanup function should take a string as input and return a string as output.

        Returns:
        A tuple, where the first element indicates whether the entire output stream is cleaned up successfully. The second element is a token to be rendered.

        Note:
        In the user interface, if we recieve the boolean indicating that cleanup was successful, we will render the last token only.
        The effect will be that the user will see the final cleaned up code snippet, rather than the entire output stream.
        This will make the user interface more responsive and user-friendly.
        """
        aggregated_output = ""
        for output in output_stream:
            aggregated_output += output
            yield False, output

        # clean up the code snippets
        aggregated_output = aggregated_output + "</code>"
        try:
            cleaned_output = cleanup_fn(aggregated_output)
            yield True, cleaned_output
        except:
            logger.error("Failed to clean up the code snippets.")
            yield False, None

    def _build_context_str(self, chat_history, code_history, dataframes):
        schema_str = ""
        if len(dataframes) > 0:
            schema_str = dataframes

        # build chat history
        chat_history_str = ""
        if len(chat_history) > 0:
            chat_history_str = combine_chat_history(chat_history)

        # build code history
        code_history_str = ""
        if len(code_history) > 0:
            code_history_str = combine_code_history(code_history)
        
        return {
            "chat": chat_history_str, 
            "code": code_history_str, 
            "data": schema_str
        }


class VanillaPromptCodeGeneration:
    """Code generation with the vanilla prompting strategy.
    """
    def __init__(self):
        pass

    def run(self,
        query: str,
        dataframes: List[Dataframe],
        llm: str = "gpt-4",
        language = "python",
        temperature = 0.0,
        ):
        # get the schema of the input dataframes
        schema_str = dataframes
        
        language = language.lower()
        if language == "python":
            prompt_template = self.create_python_prompt()
        elif language == "r":
            prompt_template = self.create_r_prompt()
        else:
            raise ValueError(f"Language {language} is not supported. Please use 'python' or 'R'.")
        
        # call LLM to generate the code
        outputs = call_llm(
            prompt_template,
            {
                "question": query,
                "data": schema_str,
            },
            llm=llm,
            streaming=False,
            stop_words=["</code>"],
            temperature=temperature
        )

        try:
            code = self._cleanup(outputs)
        except:
            code = outputs
        
        return {
            "output": code
        }


    def batch_run(self,
        queries: List[str],
        dataframes: List[str],
        llm: str = "openai-gpt-4o",
        language = "python",
        batch_size = None,
        temperature = 0.0,
        ):
        """Used to run experiments in a batch.
        """
        language = language.lower()
        if language == "python":
            prompt_template = self.create_python_prompt()
        elif language == "r":
            prompt_template = self.create_r_prompt()
        else:
            raise ValueError(f"Language {language} is not supported. Please use 'python' or 'R'.")

        batch_inputs = []
        for i, query in enumerate(queries):
            dataframes_ = dataframes[i]
            schema_str = dataframes_

            # build batch inputs
            batch_inputs.append({
                "question": query,
                "data": schema_str,
            })
        

        # call LLM to generate the code
        outputs = batch_call_llm(
            prompt_template,
            batch_inputs,
            llm=llm,
            temperature=temperature,
            batch_size=batch_size
        )
        
        # parse outputs
        results = []
        for output in outputs:
            code = self._cleanup(output)
            results.append(
                {"output": code}
            )
        return results

    def _cleanup(self, output: str) -> str:
        """
        Clean up the code snippets in the output.
        """
        return extract_code(output)
    
    def create_python_prompt(self):
        from .prompts.python.vanilla import PROMPT
        return PROMPT
    
    def create_r_prompt(self):
        from .prompts.R.vanilla import PROMPT
        return PROMPT