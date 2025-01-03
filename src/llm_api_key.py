import os
import json

def set_vertexai_key(REPO_BASE_DIR):
    with open(f"{REPO_BASE_DIR}/vertexai.json", "r") as f:
        vertexai_key = json.load(f)
        os.environ["GOOGLE_API_KEY"] = vertexai_key["GOOGLE_API_KEY"]
        os.environ["GOOGLE_CLOUD_PROJECT_ID"] = vertexai_key["GOOGLE_CLOUD_PROJECT_ID"]

def set_openai_key(REPO_BASE_DIR):
    with open(f"{REPO_BASE_DIR}/openai.key", "r") as f:
        os.environ["OPENAI_API_KEY"] = f.read().strip()

def set_azure_openai_key(REPO_BASE_DIR):
    # load azure openai's configurations
    with open(f"{REPO_BASE_DIR}/azure_openai_credentials.json", "r") as f:
        azure_openai_credentials = json.load(f)
    os.environ["AZURE_OPENAI_ENDPOINT"] = azure_openai_credentials["AZURE_OPENAI_ENDPOINT"]
    os.environ["AZURE_OPENAI_API_KEY"] = azure_openai_credentials["AZURE_OPENAI_API_KEY"]

def set_aws_bedrock_key(REPO_BASE_DIR):
    with open(f"{REPO_BASE_DIR}/aws_credentials.json", "r") as f:
        aws_credentials = json.load(f)
    os.environ["AWS_ACCESS_KEY_ID"] = aws_credentials["AWS_ACCESS_KEY_ID"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_credentials["AWS_SECRET_ACCESS_KEY"]