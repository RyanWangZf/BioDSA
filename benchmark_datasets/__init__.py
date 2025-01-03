import os
import json
import pdb
import pandas as pd
from typing import Dict, List

from pydantic import BaseModel

from sandbox.EvalDatasetLoader import EvalDataset

class DatasetConfig(BaseModel):
    owner: str
    dataset_name: str
    dataset_description: str
    table_dir: str
    tables: List[List[str]]

def get_dataset_files(base_datasets_path: str, name: str):
    """
    Get the dataset files based on the configuration file
    """

    assert os.path.exists(base_datasets_path), f"Path {base_datasets_path} does not exist"

    # get the configuration file and parse it to get the tables and names
    data_dir = os.path.join(base_datasets_path, name)
    config_json = [x for x in os.listdir(data_dir) if x.endswith(".json")][0]
    config_json = os.path.join(data_dir, config_json)
    with open(config_json, "r") as f:
        config = json.load(f)
        
        # check that the json schema is valid
        try:
            DatasetConfig(**config)
        except Exception as e: 
            print(f"Error in the dataset configuration file: {e}")

    # get the tables
    table_dir = config["table_dir"].split("/")[-1]
    table_dir = os.path.join(data_dir, table_dir)

    tables = config["tables"]
    for table in tables:
        table_path, table_name, sep = table
        sep = "\t" if sep == "tsv" else ","
        table_path = os.path.join(table_dir, table_path)
        yield table_name, pd.read_csv(table_path, sep=sep)


def get_dataset(base_datasets_path: str, name: str) -> EvalDataset:
    """
    Load the dataset in the format for the EvalDataset object

    Args:
        name: str, the alias for a certain dataset defined in the `get_dataset_files` function
    """

    # dataset should be: key the target table name, value the dataframe
    # get the json under that folder
    tables = {}
    for table_name, table in get_dataset_files(base_datasets_path, name):
        table_name = f"{table_name}.csv"
        tables[table_name] = table

    return EvalDataset(tables)


# example
if __name__ == "__main__":
    dataset = get_dataset_files('/home/ubuntu/DSCodeGen/benchmark_datasets/python/datasets', '28472509')
    for table_name, table in dataset:
        print(table)