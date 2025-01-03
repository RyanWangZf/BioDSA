from typing import Union, Literal
from langchain_core.utils.function_calling import convert_to_openai_function
from tqdm import tqdm
import pdb
import os

# model name configuration
GEMINI_MODEL_NAME_MAP = {
    "gemini-pro": "gemini-1.5-pro",
    "gemini-flash": "gemini-1.5-flash",
}
CLAUDE_MODEL_NAME_MAP = {
    "sonnet": "claude-3-5-sonnet@20240620",
    "opus": "claude-3-opus@20240229",
    "hiku": "claude-3-haiku@20240307",
}
AZURE_OPENAI_MODEL_NAME_MAP = {
    "azure-gpt-4o": "gpt-4o",
    "azure-gpt-4": "gpt-4",
    "azure-gpt-35": "gpt-35",
    "azure-gpt-4o-mini": "gpt-4o-mini",
}
OPENAI_MODEL_NAME_GPT4 = "gpt-4-turbo"  # new gpt-4-turbo
OPENAI_MODEL_NAME_GPT35 = "gpt-3.5-turbo"
OPENAI_MODEL_NAME_GPT4o = "gpt-4o"
OPENAI_MODEL_NAME_GPT4o_mini = "gpt-4o-mini"
OPENAI_MODEL_NAME_MAP = {
    "openai-gpt-4": OPENAI_MODEL_NAME_GPT4,
    "openai-gpt-35": OPENAI_MODEL_NAME_GPT35,
    "openai-gpt-4o": OPENAI_MODEL_NAME_GPT4o,
    "openai-gpt-4o-mini": OPENAI_MODEL_NAME_GPT4o_mini,
}
BEDROCK_MODEL_NAME_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"
BEDROCK_MODEL_NAME_HIKU = "anthropic.claude-3-haiku-20240307-v1:0"
BEDROCK_MODEL_NAME_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
BEDROCK_MODEL_NAME_MAP = {
    "hiku": BEDROCK_MODEL_NAME_HIKU,
    "sonnet": BEDROCK_MODEL_NAME_SONNET,
    "opus": BEDROCK_MODEL_NAME_OPUS,
}
BEDROCK_MODEL_NAME_LIST = list(BEDROCK_MODEL_NAME_MAP.keys())

AZURE_MODEL_NAME_LIST = list(AZURE_OPENAI_MODEL_NAME_MAP.keys())
GEMINI_MODEL_NAME_LIST = list(GEMINI_MODEL_NAME_MAP.keys())
CLAUDE_MODEL_NAME_LIST = list(CLAUDE_MODEL_NAME_MAP.keys())
OPENAI_MODEL_NAME_LIST = list(OPENAI_MODEL_NAME_MAP.keys())
VERTEX_MODEL_NAME_LIST = GEMINI_MODEL_NAME_LIST

if os.environ.get("OPENAI_API_KEY") is not None:
    from .llm_utils.openai import call_openai, function_call_openai
    from .llm_utils.openai_async import batch_call_openai
    from .llm_utils.openai_async import batch_function_call_openai

if os.environ.get("GOOGLE_API_KEY") is not None:
    from .llm_utils.vertexai import call_gemini, batch_call_gemini
    from .llm_utils.vertexai import call_vertexai_sonnet, batch_call_vertexai_sonnet

if os.environ.get("AZURE_OPENAI_ENDPOINT") is not None:
    from .llm_utils.azure_openai import call_azure_openai, function_call_azure_openai
    from .llm_utils.azure_openai_async import batch_call_azure_openai, batch_function_call_azure_openai

if os.environ.get("AWS_ACCESS_KEY_ID") is not None:
    from .llm_utils.bedrock_async import batch_call_bedrock
    from .llm_utils.bedrock import call_bedrock

def _batch_inputs_to_messages(prompt_template, batch_inputs):
    # build messages for the openai
    batch_messages = []
    for i, batch_input in enumerate(batch_inputs):
        prompt_content = prompt_template.format(**batch_input)
        messages = [
            {
                "role": "user",
                "content": prompt_content
            }
        ]
        batch_messages.append(messages)
    return batch_messages

def _wrap_response_openai(response):
    # consider if n > 1
    n = len(response.choices)
    if n > 1:
        return [res.message.content for res in response.choices]
    else:
        return response.choices[0].message.content

def _wrap_streaming_openai(response):
    for res in response:
        chunk = res.choices[0].delta.content
        if chunk is not None:
            yield chunk

def _wrap_response_gemini(response):
    return response.text

def _wrap_streaming_gemini(response):
    for res in response:
        chunk = res.text
        if chunk is not None:
            yield chunk

def _wrap_response_vertexai_claude(response):
    return response.content[0].text

def _wrap_streaming_vertexai_claude(response):
    with response as stream:
        for text in stream.text_stream:
            if text is not None:
                yield text

def call_llm(
    prompt_template,
    inputs,
    llm=Union[str, Literal[
        "openai-gpt-35",
        "openai-gpt-4",
        "openai-gpt-4o",
        "openai-gpt-4o-mini",
        "gemini-pro",
        "gemini-flash",
        "sonnet",
        "opus",
        "hiku",
        "azure-gpt-4",
        "azure-gpt-35",
        "azure-gpt-4o",
        "azure-gpt-4o-mini"
    ]],
    temperature=0.0,
    streaming=False,
    stop_words=[],
    n = 1
):
    """Call Chat LLM models, with text inputs and text outputs.

        Args:
            prompt_template (str or BasePromptTemplate): The prompt template to be fed with user's request.
                e.g., "What is the difference between {item1} and {item2}".
            inputs (dict): The inputs to be fed to the prompt template. Should match the placeholders
                in the prompt template, e.g., {"item1": "apple", "item2": "orange"}.
            llm: (str): The name of the LLM model to be used. 
            temperature (float): The temperature for the LLM model.
                The higher the temperature, the more creative the text.
                The lower the temperature, the more predictable the text.
                The default value is 0.0.
            streaming (bool): Whether to use streaming mode.
                The default value is False.
            stop_words (list[str]): The stop words to be used in the LLM model.
                The default value is an empty list.
            n (int): How many chat completion choices to generate for each input message.
                Note that you will be charged based on the number of generated tokens across all of the choices. Keep n as 1 to minimize costs.

        Returns:
            str: The response from the LLM model.
    """
    assert not (n > 1 and streaming), "Streaming mode does not support n > 1."

    if llm in OPENAI_MODEL_NAME_LIST:
        messages = _batch_inputs_to_messages(prompt_template, [inputs])[0]
        response = call_openai(
            llm=llm,
            messages=messages,
            temperature=temperature,
            stop=stop_words,
            stream=streaming,
            n=n
        )
        if streaming:
            return _wrap_streaming_openai(response)
        return _wrap_response_openai(response)
    
    elif llm in AZURE_MODEL_NAME_LIST:
        messages = _batch_inputs_to_messages(prompt_template, [inputs])[0]
        response = call_azure_openai(
            llm=llm,
            messages=messages,
            temperature=temperature,
            stop=stop_words,
            stream=streaming,
            n=n
        )
        if streaming:
            return _wrap_streaming_openai(response)
        return _wrap_response_openai(response)
    
    elif llm in VERTEX_MODEL_NAME_LIST:
        # warning if n > 1 will be set to 1 cuz these models do not support n > 1
        if n > 1:
            print(f"Warning: Model {llm} does not support n > 1. Setting n to 1.")
        return call_vertexai(prompt_template=prompt_template, inputs=inputs, llm=llm, temperature=temperature, streaming=streaming)
    
    elif llm in BEDROCK_MODEL_NAME_LIST:
        return call_bedrock(llm=llm, prompt=prompt_template.format(**inputs), temperature=temperature, stop_words=stop_words, streaming=streaming)

    else:
        raise ValueError(f"Model {llm} is not supported.")


def batch_call_llm(
    prompt_template,
    batch_inputs,
    llm: Union[str, Literal[
        "openai-gpt-35",
        "openai-gpt-4",
        "openai-gpt-4o",
        "openai-gpt-4o-mini",
        "gemini-pro",
        "gemini-flash",
        "sonnet",
        "opus",
        "azure-gpt-4",
        "azure-gpt-35",
        "azure-gpt-4o",
        "azure-gpt-4o-mini"
    ]],
    temperature=0.0,
    batch_size=None,
    n = 1,
    ):
    """Call Chat LLM models on a batch of inputs in parallel, with text inputs and text outputs.

    Args:
        prompt_template (str): The prompt template to be fed with user's request.
            e.g., "What is the difference between {item1} and {item2}".
        batch_inputs (List[dict]): A batch of inputs to be fed to the prompt template. Should match the placeholders
            in the prompt template, e.g., {"item1": "apple", "item2": "orange"}.
        output_parser (langchain_core.output_parsers, optional): The output parser to parse the output from the LLM model.
            The default value is `langchain_core.output_parsers.StrOutputParser()`.
        llm: (str): The name of the LLM model to be used. 
        temperature (float): The temperature for the LLM model.
            The higher the temperature, the more creative the text.
            The lower the temperature, the more predictable the text.
            The default value is 0.0.
        batch_size (int): The batch size for the batch call. Define
            the number of inputs to be processed in parallel.
            The default value is None, will proceed with all inputs in one batch.
        n (int): How many chat completion choices to generate for each input message. 
            Note that you will be charged based on the number of generated tokens across all of the choices. Keep n as 1 to minimize costs.

    Returns:
        str: The response from the LLM model.
    """

    if llm in OPENAI_MODEL_NAME_LIST:
        batch_messages = _batch_inputs_to_messages(prompt_template=prompt_template, batch_inputs=batch_inputs)
        if batch_size is not None:
            results = []
            for i in range(0, len(batch_messages), batch_size):
                batch_results = batch_call_openai(batch_messages[i:i+batch_size], llm=llm, temperature=temperature, n=n)
                results.extend(batch_results)
        else:
            results = batch_call_openai(batch_messages, llm=llm, temperature=temperature, n=n)

    elif llm in AZURE_MODEL_NAME_LIST:
        batch_messages = _batch_inputs_to_messages(prompt_template=prompt_template, batch_inputs=batch_inputs)
        if batch_size is not None:
            results = []
            for i in range(0, len(batch_messages), batch_size):
                batch_results = batch_call_azure_openai(batch_messages[i:i+batch_size], llm=llm, temperature=temperature, n=n)
                results.extend(batch_results)
        else:
            results = batch_call_azure_openai(batch_messages, llm=llm, temperature=temperature, n=n)

    elif llm in VERTEX_MODEL_NAME_LIST:
        results = batch_call_vertexai(
            prompt_template=prompt_template,
            batch_inputs=batch_inputs,
            llm=llm,
            temperature=temperature,
            batch_size=batch_size,
        )

    elif llm in BEDROCK_MODEL_NAME_LIST:
        if batch_size is not None:
            results = []
            for i in tqdm(range(0, len(batch_inputs), batch_size)):
                batch_results = batch_call_bedrock(
                    batch_prompts=[prompt_template.format(**batch_input) for batch_input in batch_inputs[i:i+batch_size]],
                    llm=llm,
                    temperature=temperature,
                )
                results.extend(batch_results)
        else:
            results = batch_call_bedrock(
                batch_prompts=[prompt_template.format(**batch_input) for batch_input in batch_inputs],
                llm=llm,
                temperature=temperature,
            )

    else:
        raise ValueError(f"Model {llm} is not supported.")
    
    return results


def function_call_llm(
    prompt_template,
    inputs,
    schema,
    llm: Union[str, Literal[
        "openai-gpt-35",
        "openai-gpt-4",
        "openai-gpt-4o",
        "openai-gpt-4o-mini",
        "azure-gpt-4",
        "azure-gpt-35",
        "azure-gpt-4o"
    ]],
    temperature=0.0,
    ):
    """Call LLM models with function call, so it outputs
    the structured data instead of text, strictly following
    the schema.

    Args:
        prompt_template (str or PromptTemplateBase): The prompt template to be fed with user's request.
        inputs (dict): The inputs to be fed to the prompt template.
        schema: Either a dictionary, a pydantic.BaseModel class, or a Python function.
            If a dictionary is passed in, it is assumed to already be a valid OpenAI
            function or a JSON schema with top-level 'title' and 'description' keys
            specified.
            # refer to
            https://api.python.langchain.com/en/latest/chains/langchain.chains.structured_output.base.create_structured_output_runnable.html#langchain.chains.structured_output.base.create_structured_output_runnable
            for the definition of the schema can be like.
        llm: (str): The name of the LLM model to be used. 
            Support: "gpt-35", "gpt-4", "openai-gpt-35", "openai-gpt-4"
        temperature (float): The temperature for the LLM model.
            The higher the temperature, the more creative the text.
            The lower the temperature, the more predictable the text.
            The default value is 0.0.

    Returns:
        dict: The structured data output from the LLM model.
    """
    from langchain_core.utils.function_calling import convert_to_openai_function
    schema_desc = convert_to_openai_function(schema)
    messages = _batch_inputs_to_messages(prompt_template, [inputs])[0]
    tools = [
        {
            "type": "function",
            "function": schema_desc,
        }
    ]
    tool_choice = {"type": "function", "function": {"name": schema_desc['name']}}

    if llm in OPENAI_MODEL_NAME_LIST:
        response = function_call_openai(
            llm=llm,
            messages=messages,
            tools=tools,
            temperature=temperature,
            tool_choice=tool_choice,
        )

    elif llm in AZURE_MODEL_NAME_LIST:
        response = function_call_azure_openai(
            llm=llm,
            messages=messages,
            tools=tools,
            temperature=temperature,
            tool_choice=tool_choice
        )

    else:
        raise ValueError(f"Model {llm} is not supported.")
    
    return response

def batch_function_call_llm(
    prompt_template,
    batch_inputs,
    schema,
    llm: Union[str, Literal[
        "openai-gpt-35",
        "openai-gpt-4",
        "openai-gpt-4o",
        "openai-gpt-4o-mini",
        "azure-gpt-4",
        "azure-gpt-35",
        "azure-gpt-4o"
    ]],
    temperature=0.0,
    batch_size=None,
):
    """
    Call LLM models with function call with a batch of inputs, so it outputs
        the structured data instead of text, strictly following
        the schema.

        Args:
            prompt_template (str or PromptTemplateBase): The prompt template to be fed with user's request.
            batch_inputs (list[dict]): The list of inputs to be fed to the prompt template.
            schema (pydantic.v1.BaseModel): The schema of the output data specified in Pydantic.
                Refer to "trialmind/TrialSearch/schema.ClinicalTrialQuery" for an example.
            llm: (str): The name of the LLM model to be used. 
                Currently, only "gpt-4" and "gpt-35" support `function call`.
            temperature (float): The temperature for the LLM model.
                The higher the temperature, the more creative the text.
                The lower the temperature, the more predictable the text.
                The default value is 0.0.
            batch_size (int): The batch size for the batch call. Define
                the number of inputs to be processed in parallel.
                The default value is None, will proceed with all inputs in one batch.

        Returns:
            dict: The structured data output from the LLM model.
    """
    schema_desc = convert_to_openai_function(schema)
    tools = [
        {
            "type": "function",
            "function": schema_desc,
        }
    ]
    batch_call_fn = None
    if llm in OPENAI_MODEL_NAME_LIST:
        batch_call_fn = batch_function_call_openai
    elif llm in AZURE_MODEL_NAME_LIST:
        batch_call_fn = batch_function_call_azure_openai
    else:
        raise ValueError(f"Model {llm} is not supported.")
    
    batch_messages = _batch_inputs_to_messages(prompt_template=prompt_template, batch_inputs=batch_inputs)
    if batch_size is not None:
        results = []
        for i in range(0, len(batch_messages), batch_size):
            batch_results = batch_call_fn(batch_messages[i:i+batch_size], llm=llm, tools=tools, temperature=temperature)
            results.extend(batch_results)
    else:
        results = batch_call_fn(batch_messages, llm=llm, tools=tools, temperature=temperature)
    return results


def call_vertexai(
    prompt_template,
    inputs,
    llm=Union[str, Literal[
        "gemini-pro",
        "gemini-flash",
        "sonnet",
        "opus",
    ]],
    temperature=0.0,
    streaming=False,
    stop_words=[],
    ):
    """Call Vertex AI models, with text inputs and text outputs."""


    if llm in CLAUDE_MODEL_NAME_LIST:
        messages = _batch_inputs_to_messages(prompt_template, [inputs])[0]
        response = call_vertexai_sonnet(
            llm=llm,
            messages=messages,
            temperature=temperature,
            streaming=streaming
        )
        if streaming:
            return _wrap_streaming_vertexai_claude(response)
        return _wrap_response_vertexai_claude(response)

    elif llm in GEMINI_MODEL_NAME_LIST:
        inputs = prompt_template.format(**inputs)
        response = call_gemini(
            llm=llm,
            inputs=inputs,
            temperature=temperature,
            streaming=streaming,
        )
        if streaming:
            return _wrap_streaming_gemini(response)
        return _wrap_response_gemini(response)

    else:
        raise ValueError(f"Model {llm} is not supported.")


def batch_call_vertexai(
    prompt_template,
    batch_inputs,
    llm: Union[str, Literal[
        "gemini-pro",
        "gemini-flash",
        "sonnet",
        "opus"
    ]],
    temperature=0.0,
    batch_size=None,
    verbose=False,
    ):
    """Call Vertex AI models on a batch of inputs in parallel, with text inputs and text outputs."""

    if llm in CLAUDE_MODEL_NAME_LIST:
        batch_messages = _batch_inputs_to_messages(prompt_template, batch_inputs)
        if batch_size is not None:
            results = []
            for i in range(0, len(batch_messages), batch_size):
                batch_results = batch_call_vertexai_sonnet(batch_messages[i:i+batch_size], llm=llm, temperature=temperature)
                results.extend(batch_results)
        else:
            results = batch_call_vertexai_sonnet(batch_messages, llm=llm, temperature=temperature)
        return results

    elif llm in GEMINI_MODEL_NAME_LIST:
        batch_inputs = [
            prompt_template.format(**batch_input)
            for batch_input in batch_inputs
        ]
        if batch_size is not None:
            results = []
            for i in range(0, len(batch_inputs), batch_size):
                batch_results = batch_call_gemini(batch_inputs=batch_inputs[i:i+batch_size], llm=llm, temperature=temperature)
                results.extend(batch_results)
                if verbose:
                    print(f"Processed {i+batch_size}/{len(batch_inputs)} inputs.")
        else:
            results = batch_call_gemini(batch_inputs=batch_inputs, llm=llm, temperature=temperature)
        return results