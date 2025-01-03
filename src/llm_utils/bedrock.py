import tenacity
import json
import os

from src.llm import BEDROCK_MODEL_NAME_MAP
import boto3


@tenacity.retry(wait=tenacity.wait_random_exponential(min=1, max=5), stop=tenacity.stop_after_attempt(10), reraise=True)
def call_bedrock(llm: str, prompt:str, temperature:float, stop_words:list[str] = [],
                streaming:bool = False, **kwargs):
    model = BEDROCK_MODEL_NAME_MAP.get(llm)
    if model is None:
        raise ValueError(f"Unknown LLM: {llm}")
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",    
        "max_tokens": 2048,
        "messages": [
            {
                "role": "user",
                "content": [
                    { "type": "text", "text": prompt}
        ]
            }
        ],
        "temperature": temperature,
    }
    if len(stop_words) > 0 and isinstance(stop_words, list):
        request_body["stop_sequences"] = stop_words
    request_body = json.dumps(request_body)

    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

    boto3_client = boto3.client("bedrock-runtime",
        region_name=AWS_DEFAULT_REGION, 
        aws_access_key_id=AWS_ACCESS_KEY_ID, 
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    if not streaming:
        response = boto3_client.invoke_model(
            body=request_body,
            modelId=model
        )
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text']
    else:
        response = boto3_client.invoke_model_with_response_stream(
            body=request_body,
            modelId=model
        )
        response_body = response.get("body")
        return _wrap_response_stream(response_body)
    
def _wrap_response_stream(response_body):
    for event in response_body:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk['type'] == 'content_block_delta':
            if chunk['delta']['type'] == 'text_delta':
                yield chunk['delta']['text']