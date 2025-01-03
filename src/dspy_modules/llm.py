import dspy
import os
import pdb

OPENAI_MODEL_NAME_MAP = {
    "openai-gpt-4o": "gpt-4o",
    "openai-gpt-4o-mini": "gpt-4o-mini",
    "azure-gpt-4o": "gpt-4o",
    "azure-gpt-4": "gpt-4",
    "azure-gpt-35": "gpt-35",
    "azure-gpt-4o-mini": "gpt-4o-mini",
}

LOCATION = "us-central1"
GEMINI_MODEL_NAME_MAP = {
    "gemini-pro": "gemini-1.5-pro-001",
    "gemini-flash": "gemini-1.5-flash-001",
}
CLAUDE_MODEL_NAME_MAP = {
    "sonnet": "claude-3-5-sonnet@20240620",
    "opus": "claude-3-opus@20240229",
}
AWS_MODEL_NAME_MAP = {
    "sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "opus": "anthropic.claude-3-opus-20240229-v1:0",
}
AVAILABLE_GEMINI_MODELS = [x for x in GEMINI_MODEL_NAME_MAP.keys()]
AVAILABLE_CLAUDE_MODELS = [x for x in CLAUDE_MODEL_NAME_MAP.keys()]
AVAILABLE_OPENAI_MODELS = [x for x in OPENAI_MODEL_NAME_MAP.keys() if "openai" in x]
AVAILABLE_AZURE_MODELS = [x for x in OPENAI_MODEL_NAME_MAP.keys() if "azure" in x]
AVAILABLE_AWS_MODELS = [x for x in AWS_MODEL_NAME_MAP.keys()]

from dsp.modules import GoogleVertexAI  # Import the GoogleVertexAI class
from anthropic import AnthropicVertex
import boto3

class GoogleVertexClaudeAI(GoogleVertexAI):
    def __init__(
        self,
        model: str,
        **kwargs,
        ):
        super().__init__(model)
        model_cls = AnthropicVertex
        self.available_args = {
            "max_output_tokens",
            "temperature",
            "top_k",
            "top_p",
            "stop_sequences",
            "candidate_count",
            "model",
        }
        self.client = model_cls(
            region=kwargs.get("location", kwargs["location"]),
            project_id=kwargs.get("project", kwargs["project"]),
        )
        self.kwargs = {
            **self.kwargs,
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "top_p": 1.0,
            "top_k": 1,
            "model": model,
            **kwargs,
        }

    def basic_request(self, prompt: str, **kwargs):
        raw_kwargs = kwargs
        kwargs = self._prepare_params(raw_kwargs)

        # ##############
        # debug
        # from vertexai.generative_models import GenerativeModel
        # model = GenerativeModel("gemini-1.5-pro")
        # num_tokens = model.count_tokens(prompt)
        # print("prompt length tokens by gemini: ", num_tokens)
        # num_tokens = num_tokens.total_billable_characters
        # print(kwargs)
        # if num_tokens > 100000:
        #     # save buggy prompt
        #     import uuid
        #     uuid_str = str(uuid.uuid4())
        #     with open(f"/home/ZF/DSAgent/DSCodeGen/buggy_prompt_{uuid_str}.txt", "w") as f:
        #         f.write(str(prompt))
        # # ##############

        # prompt to messages
        messages = [
            {
                "role":"user", 
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        response = self.client.messages.create(
            model=kwargs["model"],
            messages=messages,
            max_tokens=kwargs["max_output_tokens"],
            temperature=kwargs["temperature"],
            top_k=kwargs["top_k"],
            top_p=kwargs["top_p"],
        )

        history = {
            "prompt": prompt,
            "response": {
                "prompt": prompt,
                "choices": [
                    {
                        "text": c.text,
                    }
                    for c in response.content
                ],
            },
            "kwargs": kwargs,
            "raw_kwargs": raw_kwargs,
        }
        self.history.append(history)

        return [i["text"] for i in history["response"]["choices"]]


def get_openai_model(model_name: str, max_tokens: int = 2048, temperature: float = 0.0):
    if model_name in AVAILABLE_OPENAI_MODELS:
        model_name = OPENAI_MODEL_NAME_MAP.get(model_name, None)
        if model_name is None:
            raise ValueError(f"Model name {model_name} is not supported.")    
        return dspy.OpenAI(model=model_name, max_tokens=max_tokens, model_type="chat", temperature=temperature)
    elif model_name in AVAILABLE_AZURE_MODELS:
        model_name = OPENAI_MODEL_NAME_MAP.get(model_name, None)
        if model_name is None:
            raise ValueError(f"Model name {model_name} is not supported.") 
        api_base = os.environ.get("AZURE_OPENAI_ENDPOINT", None)   
        return dspy.AzureOpenAI(api_base=api_base, model=model_name, api_version="2023-05-15", max_tokens=max_tokens, model_type="chat", temperature=temperature)
    else:
        raise ValueError(f"Model name {model_name} is not supported.")
    
def get_vertexai_model(model_name: str, max_tokens: int = 2048, credentials: str = None, temperature: float = 0.7):

    if model_name in AVAILABLE_GEMINI_MODELS:
        model_id = GEMINI_MODEL_NAME_MAP.get(model_name)
        vertex_ai = GoogleVertexAI(
            model=model_id,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT_ID", None),
            location="us-central1",
            credentials=credentials,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
    
    elif model_name in AVAILABLE_CLAUDE_MODELS:
        model_id = CLAUDE_MODEL_NAME_MAP.get(model_name)
        vertex_ai = GoogleVertexClaudeAI(
            model=model_id,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT_ID", None),
            location="us-east5",
            credentials=credentials,
            max_output_tokens=1024,
            temperature=temperature
        )

    else:
        raise ValueError(f"Model name {model_name} is not supported.")
    
    return vertex_ai

class BedrockClient(dspy.Bedrock):
    def __init__(self, region_name: str, **kwargs):
        super().__init__(region_name=region_name, **kwargs)
        self.predictor = boto3.client(
            "bedrock-runtime",
            region_name=region_name, 
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), 
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )

def get_aws_model(model_name, temperature:float=0.7, max_tokens=2048, **kwargs):
    model_id = AWS_MODEL_NAME_MAP.get(model_name, None)
    bedrock = BedrockClient(region_name="us-west-2")
    llm = dspy.AWSAnthropic(
        bedrock, model_id, 
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
        )    
    return llm


