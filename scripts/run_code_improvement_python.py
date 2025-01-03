import os, sys
import json
from typing import Union, Literal
import pdb
import pandas as pd
from tqdm import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    return results


def execute_python_code_single_sandbox_with_timeout(sandbox, input_code_list, timeout=60):
    def _execute_code(sandbox, input_code, output_list, err_event):
        try:
            exit_code, output, artifacts = sandbox.execute(
                language="python",
                code=input_code
            )
            output_list.append((exit_code, output))
        except Exception as e:
            output_list.append((1, f"Error: {str(e)}"))
        finally:
            err_event.set()
    
    output_results = []
    err_flag = False

    # execute the code in the sandbox
    try:
        for code in input_code_list:
            # get the prefix and add it to the output_code
            # Initialize event and result container
            err_event = threading.Event()
            output_list = []
            exec_thread = threading.Thread(target=_execute_code, args=(sandbox, code, output_list, err_event))
            exec_thread.start()
            err_event.wait(timeout=timeout)

            if not err_event.is_set():
                exit_code = 1
                output = f"Timeout: Code execution exceeded {SANDBOX_EXEC_TIMEOUT} seconds."
            else:
                exit_code, output = output_list[0]

            output_results.append({
                "study_ids": study_id,
                "input_code": code,
                "exit_code": exit_code,
                "output_log": output,
            })

        sandbox.stop()

    except Exception as e:
        print(f"""Error {e} \n in study {study_id}
            when executing the code: {code}
            """)
        err_flag = True
        sandbox.stop()
        return [], err_flag
    
    return output_results, err_flag

def run_self_reflection_codegen_python(
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
    from src.api import CodeGeneration
    api = CodeGeneration()
    results = api.batch_run(
        queries = samples["queries"],
        dataframes = samples["dataframes"],
        llm = llm,
        language = "python",
        chat_histories=samples["chat_histories"],
        code_histories=samples["code_histories"],
        reference_codes=samples["output_code"],
        temperature=0.01,
        batch_size=10,
        debug=True, # set debug mode for self-reflection
    )
    for idx, res in enumerate(results):
        print("=== Question ===")
        print(samples.iloc[idx]["queries"])
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

    # here we generate the code for a given question for a given dataset
    # vanilla prompt
    outputs = run_vanilla_prompt_codegen_python(samples.iloc[:1], "azure-gpt-4o-mini")

    # here we start the sandbox locally to accept data and execute the generated code on them
    # need to prepare the patient-level data in advance
    # load sandbox related tools
    from benchmark_datasets.utils import get_dataset
    from sandbox.utils import create_sandbox
    from sandbox import DEFAULT_REMOTE_PATH
    SANDBOX_EXEC_TIMEOUT = 3*60 # 3 mins
    study_id = samples.iloc[0]['study_ids']
    dataset = get_dataset(base_datasets_path=f"{REPO_BASE_DIR}/benchmark_datasets/python/datasets", name=str(study_id))
    sandbox = create_sandbox(
        dataset=dataset,
        remote_path=DEFAULT_REMOTE_PATH
    )
    
    # prepare the input code list
    input_code_list = []
    for idx, output in enumerate(outputs):
        prefix_code = eval(samples.iloc[idx]["code_histories"])
        prefix_code = "\n".join(prefix_code)
        input_code = f"{prefix_code}\n{output['output']}"

        # add a typo to insert bugs into the code
        input_code = f"{input_code}\nn = len(n)"

        input_code_list.append(input_code)

    # execute the code in the sandbox
    output_results, err_flag = \
        execute_python_code_single_sandbox_with_timeout(sandbox=sandbox, input_code_list=input_code_list, timeout=SANDBOX_EXEC_TIMEOUT)
    for result in output_results:
        print("=== Input ===")
        print(result["input_code"])
        print("=== Output ===")
        print("Exit code:", result["exit_code"])
        print("Printed logs:", result["output_log"])
        print("\n\n\n")

    # ask LLM to reflect the results and improve it
    debug_samples = []
    for idx, output in enumerate(output_results):
        raw_question = samples.iloc[idx]["queries"]
        output_log = output["output_log"]
        previous_code = output["input_code"]
        query = f"""The original quesiton is: 
        ```{raw_question}```

        and execute the reference code raises an error. Note that assertion errors mean the code does not pass the golden test cases.  Here's the log by executing the code which can help debug:

        ```{output_log}```
        """
        debug_samples.append({
            "queries": query, # the debug query
            "output_code": previous_code, # the code to be improved
            "dataframes": samples.iloc[idx]["dataframes"],
            "chat_histories": [],
            "code_histories": samples.iloc[idx]["code_histories"],
        })
    debug_samples = pd.DataFrame(debug_samples)

    # run the LLM self-reflection code generation
    run_self_reflection_codegen_python(debug_samples, "azure-gpt-4o-mini")






