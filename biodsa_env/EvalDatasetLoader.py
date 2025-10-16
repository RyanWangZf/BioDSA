from typing import Dict
import os
import pandas as pd

from sandbox import Dataframe


class EvalDataset:

    def __init__(
        self,
        tables: Dict[str, pd.DataFrame] = {},
    ):
        """
        A module to wrap raw datasets into a single object.

        The dataset is a dictionary of dataframes, where the key is the name of the table used in code.
        note: the dataset name should contain the extension of the file, e.g. "table.csv" or "table.tsv"
        """

        assert all([isinstance(df, pd.DataFrame) for df in tables.values()]
                   ), "All values in the dataset should be pandas dataframes"
        
        assert all([name.endswith(".csv") for name in tables.keys()]
                   ), "All file names in the dataset should end with .csv to match the table names in the code"

        self.tables = tables

        