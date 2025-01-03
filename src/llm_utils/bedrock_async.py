import pdb
import asyncio
from typing import List, Union
from typing import Dict, List, Tuple
import tenacity
import os

import json
import time
import asyncio
import requests as req
import botocore.session
from itertools import groupby
from operator import itemgetter
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from src.llm import BEDROCK_MODEL_NAME_MAP
import boto3

def inner_join(a, b):
    L = a + b
    L.sort(key=itemgetter(0)) # sort by the first column
    for _, group in groupby(L, itemgetter(0)):
        row_a, row_b = next(group), next(group, None)
        if row_b is not None: # join
            yield row_a + row_b[1:] # cut 1st column from 2nd row

def get_inference(model_id: str, region: str, payload: List) -> Tuple:
    try:
        ## Initialize the runtime rest API to be called for the endpoint
        endpoint: str = f"https://bedrock-runtime.{region}.amazonaws.com/model/{model_id}/invoke"

        # Converting the payload dictionary into a JSON-formatted string to be sent in the HTTP request
        request_body = json.dumps(payload[1])

        # Creating an AWSRequest object for a POST request with the service specified endpoint, JSON request body, and HTTP headers
        request = AWSRequest(method='POST',
                             url=endpoint,
                             data=request_body,
                             headers={'content-type': 'application/json'})

        # Initializing a botocore session
        session = botocore.session.Session()

        # Adding a SigV4 authentication information to the AWSRequest object, signing the request
        sigv4 = SigV4Auth(session.get_credentials(), "bedrock", region)
        sigv4.add_auth(request)

        # Prepare the request by formatting it correctly
        prepped = request.prepare()

        # Send the HTTP POST request to the prepared URL with the specified headers & JSON-formatted request body, storing the response
        response = req.post(prepped.url, headers=prepped.headers, data=request_body)

        if response.status_code == 200:
            return (payload[0], response.json())
        else:
            print(f"Error: Received status code {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

@tenacity.retry(wait=tenacity.wait_random_exponential(min=60, max=600), stop=tenacity.stop_after_attempt(10), reraise=True)
async def async_calls_on_model(model_id, region, payload):
    return await asyncio.to_thread(get_inference, model_id, region, payload)

# Asynchronously calling all of the prompts based on user input on the specific model offering with the given payload 
async def parallel_calls(model_id, region, payloads):
    responses = await asyncio.gather(*[async_calls_on_model(model_id, region, payload) for payload in payloads])
    # the responses would usually not be in the same order as the payloads, so join the the payload and response  
    responses = list(inner_join(payloads, responses))
    return responses

# Function to create the payload
def create_payload_titan(prompt: str) -> Dict:
    return {"inputText": prompt}

def create_payload_claude(prompt: str, temperature: float) -> Dict:
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "messages": [
        {
            "role": "user",
            "content": [{ "type": "text", "text": prompt }],
        },
        ],
        "temperature": temperature,
    }
    return payload

async def apply_async_claude(model_id, payloads):
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
    tasks = [async_calls_on_model(model_id, AWS_DEFAULT_REGION, payload) for i, payload in enumerate(payloads)]
    results = await asyncio.gather(*tasks)
    return results

def batch_call_bedrock(batch_prompts, llm, temperature):
    """
    Args:
        llm: "claude", "hiku", "sonnet", "opus"
    """
    model = BEDROCK_MODEL_NAME_MAP.get(llm)
    if model is None:
        raise ValueError(f"Unknown llm: {llm}")
    payloads: List = [(i, create_payload_claude(p, temperature=temperature)) for i, p in enumerate(batch_prompts)]
    results = _async_execute(async_function = apply_async_claude, model_id = model, payloads = payloads)
    results = list(inner_join(payloads, results))
    parsed_results = []
    for result in results:
        try:
            content = result[-1]['content'][0]['text']
            parsed_results.append(content)
        except:
            parsed_results.append("")
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