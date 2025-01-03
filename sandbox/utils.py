import os
import time
from typing import List, Tuple

import tqdm
from sandbox import DEFAULT_REMOTE_PATH, SANDBOX_IMANGE_IDENTIFIER
from sandbox.ExecutionSandboxWrapper import ExecutionSandboxWrapper
from sandbox.EvalDatasetLoader import EvalDataset


def create_sandbox(dataset: EvalDataset, remote_path: str = DEFAULT_REMOTE_PATH, image_id: str = SANDBOX_IMANGE_IDENTIFIER) -> ExecutionSandboxWrapper:
    """
    Create a sandbox for the dataset
    """
    sandbox = ExecutionSandboxWrapper(
        image_identifier=image_id, target_dir=remote_path)

    print(f"Execution sandbox created - id: `{sandbox.container.id}`")

    data_paths = sandbox.start(
        dataset=dataset
    )
    
    print(f"Data placed in sandbox: {data_paths}")
    
    return sandbox


def execute_in_sandbox(code_strings: List[str], language: str, dataset: EvalDataset, remote_path: str) -> List[Tuple[str, str, List[str]]]:
    """
    Create a new sandbox, execute code strings in the sandbox

    Args:
        code_strings: List of code strings to execute
        language: Language of the code strings
        dataset: EvalDatasetLoader instance
        remote_path: Remote path to place dataset files

    Returns:
        List of execution outputs, where each output is a tuple of (exit_code, stdout, artifacts)
    """
    progress = tqdm.tqdm(
        code_strings, desc="Progress for code execution in sandbox")
    exec_outputs: Tuple[str, str, List[str]] = []
    for code in code_strings:
        sandbox = create_sandbox(
            dataset=dataset,
            remote_path=remote_path
        )

        start = time.time()
        exit_code, output, artifacts = sandbox.execute(
            language=language,
            code=code
        )
        end = time.time()

        exec_outputs.append(
            (exit_code, output.decode('utf-8'), artifacts, end - start))

        sandbox.stop()
        progress.update(1)

    return exec_outputs
