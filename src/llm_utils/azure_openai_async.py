import pdb
import asyncio
from typing import List, Union
import httpx
from openai import AsyncAzureOpenAI
import tenacity
import json

from ..llm import AZURE_OPENAI_MODEL_NAME_MAP

async_azure_openai_client = AsyncAzureOpenAI(
    api_version="2023-05-15",
    http_client=httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=1000,
            max_keepalive_connections=100
        )
    )
)

@tenacity.retry(wait=tenacity.wait_random_exponential(min=60, max=600), stop=tenacity.stop_after_attempt(10), reraise=True)
async def api_call_single(client: AsyncAzureOpenAI, model: str, messages: list[dict], temperature: float = 0.0, **kwargs):
    # Call the API
    response = await client.chat.completions.create(
        model=model,
        messages=messages,  # Ensure messages is a list
        temperature=temperature,
        **kwargs
    )
    return response

@tenacity.retry(wait=tenacity.wait_random_exponential(min=60, max=600), stop=tenacity.stop_after_attempt(10), reraise=True)
async def api_function_call_single(client: AsyncAzureOpenAI, model: str, messages: list[dict], tools: list[dict], temperature: float = 0.0, **kwargs):
    # Call the API
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        temperature=temperature,
        **kwargs
    )
    return response

async def apply_async(client: AsyncAzureOpenAI, model: str, messages_list: list[list[dict]], **kwargs):
    """
    Apply the OpenAI API asynchronously to a list of messages using high-level asyncio APIs.
    """
    tasks = [api_call_single(client, model, messages, **kwargs) for messages in messages_list]
    results = await asyncio.gather(*tasks)
    return results

async def apply_function_call_async(client: AsyncAzureOpenAI, model: str, messages_list: list[list[dict]], tools: list[dict], **kwargs):
    """
    Apply the OpenAI API asynchronously to a list of messages using high-level asyncio APIs.
    """
    tasks = [api_function_call_single(client, model, messages, tools, **kwargs) for messages in messages_list]
    results = await asyncio.gather(*tasks)
    return results


def batch_call_azure_openai(batch_messages, llm, temperature, **kwargs):
    model = AZURE_OPENAI_MODEL_NAME_MAP.get(llm)
    if model is not None:
        results = _async_execute(
            async_function = apply_async, 
            client = async_azure_openai_client, 
            model=model, 
            messages_list=batch_messages, 
            temperature=temperature, 
            seed=0,
            **kwargs
            )
    else:
        raise ValueError(f"Unknown llm: {llm}")

    parsed_results = []
    for result in results:
        try:
            parsed_ = _wrap_response(result)
            parsed_results.append(parsed_)
        except:
            parsed_results.append("")
    return parsed_results

def batch_function_call_azure_openai(batch_messages, llm, tools, temperature):
    model = AZURE_OPENAI_MODEL_NAME_MAP.get(llm)
    if model is not None:
        results = _async_execute(
            async_function = apply_function_call_async, 
            client = async_azure_openai_client, 
            model=model, 
            messages_list=batch_messages, 
            tools=tools, 
            temperature=temperature, 
            seed=0
            )
    else:
        raise ValueError(f"Unknown llm: {llm}")
    parsed_results = []
    for result in results:
        try:
            # parse the outputs
            response_message = result.choices[0].message
            tool_calls = response_message.tool_calls
            outputs = {}
            if tool_calls:
                outputs = json.loads(tool_calls[0].function.arguments)
            parsed_results.append(outputs)
        except:
            parsed_results.append({})
    return parsed_results


def _async_execute(async_function, **kwargs):
    from concurrent.futures import ThreadPoolExecutor
    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(1) as executor:
            results = executor.submit(lambda: asyncio.run(async_function(**kwargs)))
            results = results.result()
    except RuntimeError:
        results = async_function(**kwargs)
        results = asyncio.run(results)
    return results


def prompts_as_chatcompletions_messages(prompts: List[str]):
    """
    chat messages for the OpenAI GPT4 chat completions API
    """
    conversations = []
    for prompt in prompts:
        messages = [{
            "role": "user",
            "content": prompt
        }]
        conversations.append(messages)

    return conversations

def _wrap_response(response):
    results = []
    if len(response.choices) > 1:
        for choice in response.choices:
            results.append(choice.message.content)
        return results
    else:
        return response.choices[0].message.content