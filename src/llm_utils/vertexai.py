# TODO(developer): Vertex AI SDK - uncomment below & run
# pip3 install --upgrade --user google-cloud-aiplatform
# gcloud auth application-default login
import tenacity
import pdb
import vertexai
import os
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models
from anthropic import AnthropicVertex
from multiprocessing import Pool
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# load llm configurations
from ..llm import GEMINI_MODEL_NAME_MAP, CLAUDE_MODEL_NAME_MAP

LOCATION = "us-central1"

SAFETY_SETTINGS = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

@tenacity.retry(wait=tenacity.wait_random_exponential(min=1, max=5), stop=tenacity.stop_after_attempt(10), reraise=True)
def api_call_single(inputs, model_name="gemini-1.5-pro", generation_config=None, stream=False):
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel(model_name)
    responses = model.generate_content(
        [inputs],
        generation_config=generation_config,
        safety_settings=SAFETY_SETTINGS,
        stream=stream,
    )
    return responses

def call_gemini(llm: str, inputs: str, temperature: float = 0.0, streaming=False, **kwargs):
    """
    Call the OpenAI API asynchronously to a list of messages using high-level asyncio APIs.
    """
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": temperature,
    }
    model_name = GEMINI_MODEL_NAME_MAP.get(llm)
    response = api_call_single(
        inputs, 
        model_name,
        generation_config=generation_config,
        stream=streaming,
        )
    return response

def batch_api_call_single(inputs, model_name, generation_config):
    """
    Wrapper function for api_call_single to be used with multiprocessing.
    """
    try:
        return api_call_single(inputs, model_name, generation_config)
    except Exception as e:
        print(f"Error processing input {inputs}: {e}")
        return None

def batch_call_gemini(llm, batch_inputs, temperature):
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": temperature,
    }
    model_name = GEMINI_MODEL_NAME_MAP.get(llm)
    if model_name is None:
        raise ValueError(f"Unsupported LLM model: {llm}")

    batch_args = [(index, inputs, model_name, generation_config) for index, inputs in enumerate(batch_inputs)]
    
    # Determine the number of threads to use
    num_threads = min([concurrent.futures.thread.ThreadPoolExecutor()._max_workers, len(batch_inputs)])
    
    # Use ThreadPoolExecutor to parallelize the API calls
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(batch_api_call_single, *args[1:]): args[0] for args in batch_args}
        responses = {future: index for future, index in futures.items()}
    
    parsed_results = [None] * len(batch_inputs)
    for future in concurrent.futures.as_completed(futures):
        index = responses[future]
        try:
            result = future.result()
            content = result.text
            parsed_results[index] = content
        except:
            parsed_results[index] = ""
    
    return parsed_results


@tenacity.retry(wait=tenacity.wait_random_exponential(min=1, max=5), stop=tenacity.stop_after_attempt(10), reraise=True)
def api_single_call_claude(messages, model_name, streaming, temperature, **kwargs):
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
    anthropic_client = AnthropicVertex(region="us-east5", project_id=PROJECT_ID)

    if streaming:
        return anthropic_client.messages.stream(
            max_tokens=1024,
            messages=messages,
            model=model_name,
            temperature=temperature,
            **kwargs
            )
    else:
        message = anthropic_client.messages.create(
        max_tokens=1024,
        messages=messages,
        model=model_name,
        temperature=temperature,
        **kwargs
        )
    return message


def call_vertexai_sonnet(
    llm: str,
    messages: list[dict],
    temperature: float = 0.0,
    streaming=False,
    **kwargs,
    ):
    model = CLAUDE_MODEL_NAME_MAP.get(llm)
    if model is None:
        raise ValueError(f"Unsupported LLM model: {llm}")
    
    response = api_single_call_claude(
            messages=messages,
            model_name=model,
            temperature=temperature,
            streaming=streaming,
            **kwargs,
            )
    return response


def batch_call_vertexai_sonnet(
    batch_messages,
    llm,
    temperature,
):
    model = CLAUDE_MODEL_NAME_MAP.get(llm)
    if model is None:
        raise ValueError(f"Unsupported LLM model: {llm}")
    
    batch_args = [(index, messages, model, False, temperature) for index, messages in enumerate(batch_messages)]
    num_threads = min([concurrent.futures.thread.ThreadPoolExecutor()._max_workers, len(batch_messages)])
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(api_single_call_claude, *args[1:]): args[0] for args in batch_args}
        responses = {future: index for future, index in futures.items()}
        
    parsed_results = [None] * len(batch_messages)
    for future in concurrent.futures.as_completed(responses):
        index = responses[future]
        try:
            result = future.result()
            content = result.content[0].text
            parsed_results[index] = content
        except:
            parsed_results[index] = ""
    
    return parsed_results
