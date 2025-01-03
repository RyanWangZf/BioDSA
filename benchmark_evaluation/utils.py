import os
import json
import pdb
import pandas as pd
import numpy as np
import itertools

from src.memory_utils import combine_dataframes as combine_dataframes_fn
from src.schema import Dataframe

def get_dataset_schema(
    data_input_dir,
    studyid, 
    schema_mapper,
    combine_dataframes=True,
    ):
    dataset_dir = os.path.join(data_input_dir, studyid)
    dataset_config = [x for x in os.listdir(dataset_dir) if x.endswith(".json")][0]
    dataset_config = os.path.join(dataset_dir, dataset_config)
    with open(dataset_config, "r") as f:
        dataset_config = json.load(f)
    
    input_dataframes = []
    table_dir = os.path.join(dataset_dir, dataset_config["table_dir"].split("/")[-1])
    for table in dataset_config["tables"]:
        table_path, table_name, sep = table
        sep = "\t" if sep == "tsv" else ","
        remote_path = f"/workdir/{table_name}.csv"
        local_data_path = os.path.join(table_dir, table_path)
        data_schema = schema_mapper(local_data_path=local_data_path, table_name=table_name, sep=sep)
        input_dataframes.append(Dataframe(table_name=table_name, path=remote_path, data_schema=data_schema))

    if combine_dataframes:
        schema_str = combine_dataframes_fn(input_dataframes)
        return schema_str
    else:
        return input_dataframes
    

def load_all_samples(data_input_dir, query_data_path, studies, schema_mapper, combine_dataframes=False):
    # build the inputs
    samples = {
        "queries": [],
        "chat_histories": [],
        "dataframes": [],
        "reference_codes": [],
        "code_histories": [],
        "study_ids": [],
        "question_ids": [],
        "test_cases": [],
        "reference_answer": [],
        "cot_instructions": []
    }
    for studyid in studies:
        input_dataframes = get_dataset_schema(data_input_dir, studyid, schema_mapper, combine_dataframes=combine_dataframes)
        df_q_a = pd.read_excel(query_data_path, sheet_name=studyid)

        testing_cols = [x for x in df_q_a.columns if "Testing" in x]
        for i, row in df_q_a.iterrows():
            samples["queries"].append(row["Question"])
            samples["dataframes"].append(input_dataframes)
            
            if not pd.isna(row["Prefix"]):
                samples["code_histories"].append([row["Prefix"]]) # code histories
            else:
                samples["code_histories"].append([])

            # add reference answer
            samples["reference_answer"].append(row["Reference answer"])

            # add generated instructions
            samples["cot_instructions"].append(row["Generated_Instructions"])

            # add placeholders
            samples["reference_codes"].append([])
            samples["chat_histories"].append([])
            samples["study_ids"].append(studyid)
            samples["question_ids"].append(i)

            # get all the unit tests
            test_cases = []
            for col in testing_cols:
                if not pd.isna(row[col]):
                    test_cases.append(row[col])
            test_cases = "\n".join(test_cases)
            samples["test_cases"].append(test_cases)

            # if studyid == 32437664 or studyid == "32437664": # bugs for gemini

    samples = pd.DataFrame(samples)
    return samples

def load_all_R_samples(data_input_dir, query_data_path, studies, schema_mapper, combine_dataframes=False):
    # build the inputs
    samples = {
        "queries": [],
        "chat_histories": [],
        "dataframes": [],
        "reference_codes": [],
        "code_histories": [],
        "study_ids": [],
        "question_ids": [],
        "test_cases": [],
        "reference_answer": [],
        "cot_instructions": []
    }
    for studyid in studies:
        input_dataframes = get_dataset_schema(data_input_dir, studyid, schema_mapper, combine_dataframes=combine_dataframes)
        df_q_a = pd.read_excel(query_data_path, sheet_name=studyid)

        testing_cols = [x for x in df_q_a.columns if "Testing" in x]
        for i, row in df_q_a.iterrows():
            samples["queries"].append(row["Question"])
            samples["dataframes"].append(input_dataframes)
            
            if not pd.isna(row["Prefix"]):
                samples["code_histories"].append([row["Prefix"]]) # code histories
            else:
                samples["code_histories"].append([])

            # add reference answer
            samples["reference_answer"].append(row["Reference Answer"])

            # add placeholders
            samples["reference_codes"].append([])
            samples["chat_histories"].append([])
            samples["study_ids"].append(studyid)
            samples["question_ids"].append(i)
            samples["cot_instructions"].append("") # add empty string for now

            # get all the unit tests
            test_cases = []
            for col in testing_cols:
                if not pd.isna(row[col]):
                    test_cases.append(row[col])
            test_cases = "\n".join(test_cases)
            samples["test_cases"].append(test_cases)

            # if studyid == 32437664 or studyid == "32437664": # bugs for gemini

    samples = pd.DataFrame(samples)
    return samples

def estimator_estimate_pass_at_k(n: int, c: int, k: int) -> float:
    """Calculates 1 - comb(n - c, k) / comb(n, k)."""
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

def estimate_pass_at_k(num_samples, num_correct, k):
    """Estimates pass@k of each problem and returns them in an array."""
    # code eval takes
    # https://huggingface.co/spaces/evaluate-metric/code_eval

    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)

    return np.array([estimator_estimate_pass_at_k(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)])
    