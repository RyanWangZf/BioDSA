import os, sys
import json
from typing import Union, Literal
import pdb
import pandas as pd

def set_environment():
    REPO_BASE_DIR  = "/home/ubuntu/dscodegen_submission_code"
    os.environ["REPO_BASE_DIR"] = REPO_BASE_DIR
    sys.path.append(REPO_BASE_DIR)

def run_vanilla_prompt_codegen_python(
    samples,
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
    ):
    from src.api import VanillaPromptCodeGeneration

    # build queries with the raw queries and all the prefix code
    input_quries = []
    for idx, row in samples.iterrows():
        query = row["queries"]
        prefix_code = row["code_histories"]
        prefix_code = "\n".join(prefix_code)
        input_quries.append(f"{query}\n{prefix_code}")

    # run the vanilla prompt code generation
    api = VanillaPromptCodeGeneration()
    results = api.batch_run(
        queries = input_quries,
        dataframes = samples["dataframes"],
        llm = llm,
        language = "python",
        temperature=0.0,
        batch_size=10,
    )
    for idx, res in enumerate(results):
        print("=== Question ===")
        print(samples.iloc[idx]["queries"])
        print("=== Generated ===")
        print(res["output"])
        print("\n\n\n")


def run_manual_prompt_codegen_python(
    samples,
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
    ]]):
    from src.api import CodeGeneration

    # run the manual prompt code generation
    api = CodeGeneration()
    results = api.batch_run(
        queries = samples["queries"],
        dataframes = samples["dataframes"],
        llm = llm,
        language = "python",
        chat_histories=None,
        code_histories=samples["code_histories"], # prefix code
        reference_codes=None,
        temperature=0.0,
        batch_size=10,
    )
    for idx, res in enumerate(results):
        print("=== Question ===")
        print(samples.iloc[idx]["queries"])
        print("=== Generated ===")
        print(res["output"])
        print("\n\n\n")

def run_cot_codegen_python(
    samples,
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
    ]]):
    from src.api import VanillaPromptCodeGeneration
    # build queries with the raw queries and all the prefix code
    input_quries = []
    for idx, row in samples.iterrows():
        query = row["queries"]
        prefix_code = eval(row["code_histories"])
        prefix_code = "\n".join(prefix_code)
        cot_instructions = row["cot_instructions"]
        input_quries.append(f"{query}\n{cot_instructions}\n{prefix_code}")

    # run the cot prompt code generation
    api = VanillaPromptCodeGeneration()
    results = api.batch_run(
        queries = input_quries,
        dataframes = samples["dataframes"],
        llm = llm,
        language = "python",
        temperature=0.0,
        batch_size=10,
    )
    for idx, res in enumerate(results):
        print("=== Question ===")
        print(input_quries[idx])
        print("=== Generated ===")
        print(res["output"])
        print("\n\n\n")


def run_auto_prompt_codegen_python(
    samples,
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
    ]]
    ):
    from src.dspy_modules.codegen import run_dspy_codegen

    # build queries with the raw queries and all the prefix code
    input_quries = []
    for idx, row in samples.iterrows():
        query = row["queries"]
        prefix_code = eval(row["code_histories"])
        prefix_code = "\n".join(prefix_code)
        input_quries.append(f"{query}\n{prefix_code}")

    batch_inputs = []
    for idx, sample in samples.iterrows():
        # print("====================================")
        # print("study_id:", sample["study_ids"])
        # print("question_id:", sample["question_ids"])
        # print("query length:", return_num_of_tokens(sample["queries"]))
        # print("dataframe schema length:", return_num_of_tokens(sample["dataframes"]))
        batch_inputs.append({
            "question": input_quries[idx],
            "dataset_schema": sample["dataframes"],
            })

    results = run_dspy_codegen(
        batch_inputs=batch_inputs,
        llm=llm,
        language="python",
        batch_size=5,
        mode="Optimized",
        temperature=0.0,
    )
    for idx, res in enumerate(results):
        print("=== Question ===")
        print(input_quries[idx])
        print("=== Generated ===")
        print(res["output"])
        print("\n\n\n")


def run_fewshot_prompt_codegen_python(
    samples,
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
    ]]
    ):
    from src.dspy_modules.codegen import run_dspy_codegen

    # build queries with the raw queries and all the prefix code
    input_quries = []
    for idx, row in samples.iterrows():
        query = row["queries"]
        prefix_code = eval(row["code_histories"])
        prefix_code = "\n".join(prefix_code)
        input_quries.append(f"{query}\n{prefix_code}")

    batch_inputs = []
    for idx, sample in samples.iterrows():
        batch_inputs.append({
            "question": input_quries[idx],
            "dataset_schema": sample["dataframes"],
            "temperature": 0.0,
        })

    results = run_dspy_codegen(
        batch_inputs=batch_inputs,
        llm=llm,
        language="python",
        batch_size=10,
        mode="FewShot",
        temperature=0.0,
    )
    for idx, res in enumerate(results):
        print("=== Question ===")
        print(input_quries[idx])
        print("=== Generated ===")
        print(res["output"])
        print("\n\n\n")


if __name__ == "__main__":
    # setup 
    set_environment()
    REPO_BASE_DIR = os.environ["REPO_BASE_DIR"]

    # depending on the project, you might want to use different keys
    from src.llm_api_key import (
        set_vertexai_key,
        set_openai_key,
        set_azure_openai_key,
        set_aws_bedrock_key
    )

    # load the coding tasks
    samples = pd.read_csv(f"{REPO_BASE_DIR}/benchmark_datasets/python/coding_tasks.csv")

    # here we use azure openai's key as an example
    # this allows us to use GPT-4o, GPT-4o-mini, GPT-3.5, etc.
    # if you have them deployed in azure openai cloud
    set_azure_openai_key(REPO_BASE_DIR)

    # vanilla prompt
    # run_vanilla_prompt_codegen_python(samples.iloc[:2], "azure-gpt-4o-mini")

    # manual prompt
    # run_manual_prompt_codegen_python(samples.iloc[:2], "azure-gpt-4o-mini")

    # cot prompt
    # run_cot_codegen_python(samples.iloc[:2], "azure-gpt-4o-mini")

    # auto prompt (dspy required)
    # run_auto_prompt_codegen_python(samples.iloc[:2], "azure-gpt-4o-mini")

    # fewshot prompt (dspy required)
    run_fewshot_prompt_codegen_python(samples.iloc[:2], "azure-gpt-4o-mini")