"""
Implement tools to get the data model of the trial patient database.
"""

import os
import pdb
import pandas as pd
import numpy as np


class VanillaMapper:
    """Accept dataframe dict, read the first five rows, and build the schema description
    and the example column descriptions.
    """
    MAX_COLS = 100 # the maximum number of columns to show in the schema description
    def __init__(self):
        pass

    def __call__(self, df=None, local_data_path=None, table_name=None, sep=","):
        """Args:
        local_data_path (str): the path of the data file in the local file system
        table_name (str): the name of the table, by default is None.
            Then will use the basename of the data_path as the table name.
        sep (str): the separator of the data file, by default is "," (for csv file)
            For the other separators, please specify the sep.
        """
        # assert: df and data_path cant be both None
        assert df is not None or local_data_path is not None, "Either `df` or `local_data_path` should be provided."
        
        if table_name is None:
            if local_data_path is None:
                table_name = "df"
            else:
                table_name = os.path.basename(local_data_path).split(".")[0]
            
        if df is not None:
            # read the data
            df = df
        else:
            # read the data
            df = pd.read_csv(local_data_path, sep=sep, nrows=5)

        # get the schema description
        return self.create_description(table_name, df)
    
    def create_description(self, table_name: str, df: pd.DataFrame):
        """Create a description of the table schema.
        """
        # for columns with all NaN, drop them in the schema description
        df = df.dropna(axis=1, how="all")

        # if too many columns, cut the columns to save space
        n_all_columns = len(df.columns)
        if n_all_columns > self.MAX_COLS:
            df = df[df.columns[:self.MAX_COLS]].copy()
            df[f"... [{n_all_columns} columns in total, the remaining are cut]"] = ["... [More columns]"] * len(df)

        # get the schema description
        data_str = f"""A Pandas Dataframe whose name is `{table_name}`, shape is {df.shape}.
This is the result of reading `{table_name}`'s first five rows by `{table_name}.head().to_string()`:"""

        # get the a string of the first five rows
        head_str = df.head(n=5).to_string()
        
        data_str = f"{data_str}\n\n{head_str}"

        return data_str


class TCGADataSchemaMapper:
    """Accept dataframe dict, read the first five rows, and build the schema description
    and the example column descriptions.
    """
    MAX_COLS = 100 # the maximum number of columns to show in the schema description
    def __init__(self):
        pass

    def __call__(self, df=None, local_data_path=None, table_name=None, sep=","):
        """Args:
        local_data_path (str): the path of the data file in the local file system
        table_name (str): the name of the table, by default is None.
            Then will use the basename of the data_path as the table name.
        sep (str): the separator of the data file, by default is "," (for csv file)
            For the other separators, please specify the sep.
        """
        # assert: df and data_path cant be both None
        assert df is not None or local_data_path is not None, "Either `df` or `local_data_path` should be provided."
        
        if table_name is None:
            if local_data_path is None:
                table_name = "df"
            else:
                table_name = os.path.basename(local_data_path).split(".")[0]
            
        if df is not None:
            # read the data
            df = df
        else:
            # read the data
            df = pd.read_csv(local_data_path, sep=sep, nrows=10000)

        # get the schema description
        return self.create_description(table_name, df)
    
    def create_description(self, table_name: str, df: pd.DataFrame):
        """Create a description of the table schema.
        """
        # for columns with all NaN, drop them in the schema description
        df = df.dropna(axis=1, how="all")

        # get the schema description
        data_str = f"""A Pandas Dataframe whose name is `{table_name}`. Shape is {df.shape}. 
This is the result of reading `{table_name}`'s first five rows by `{table_name}.head().to_string()`:"""
        
        n_all_columns = len(df.columns)
        if n_all_columns > self.MAX_COLS:
            df = df[df.columns[:self.MAX_COLS]].copy()
            df[f"... [{n_all_columns} columns in total, the remaining are cut]"] = ["... [More columns]"] * len(df)

        # get the a string of the first five rows
        head_str = df.head(n=5).to_string()

        # get the schema description for each column
        # cover: column name, column type, example values, NA values, etc.
        cols = []
        for col in df.columns[:self.MAX_COLS]:
            # get the example values of the columns
            col_values = df[col].value_counts().index[:10].to_list() # keep NaN values
            col_values = [str(x) if not pd.isna(x) else "NaN" for x in col_values]
            this_col_str = f"\nColumn `{col}``: top-10 frequent values: {col_values}"
            this_col_str = self.add_hint_to_column(col, this_col_str)
            cols.append(this_col_str)

        # join the column descriptions
        col_str = "\n".join(cols)
        data_str = f"{data_str}\n\n{head_str}\n\nHere are the columns' description:\n{col_str}"

        # add hint to the table description
        data_str = self.add_hint_to_table(table_name, data_str)

        return data_str
    
    def add_hint_to_column(self, col, this_col_str):
        """Add hint to the column description.
        """
        if col.lower() in ["patient_id"]:
            this_col_str = f"{this_col_str}\tNote: The unique identifier of a patient."
        
        # if col.lower() in ["sample_id", "tumor_sample_barcode"]:
        #     this_col_str = f"{this_col_str}\tColDesc: The identifier of the patient's clinical samples (e.g., a sample of tissue, blood, urine, etc). One patient may have multiple clinical samples."

        if col.lower() in ["os_status", "rfs_status", "dor_status", "pfs_status"]:
            this_col_str = f"{this_col_str}\tNote: Need to deal with NaN values. Try to apply lambda function to convert the status to binary values when making KM analysis, e.g., `df['OS_STATUS'] = df['OS_STATUS'].apply(lambda x: 1 if x == '1:DECEASED' else 0)`."

        if col.lower() in ["os_months", "rfs_months", "dor_months", "pfs_months"]:
            this_col_str = f"{this_col_str}\tNote: The survival time in months. Try to drop NaN values before applying any KM analysis."

        return this_col_str

    def add_hint_to_table(self, table, data_str):
        if table.lower() in ["data_cna"]:
            data_str = f"{data_str}\n\nTableNote: `{table}` contains the copy number alteration data. The CNA value `2` means amplification, `-2` means deep deletion, and `0` means no change. "

        if table.lower() in ["data_sv"]:
            data_str = f"{data_str}\n\nTableNote: The structural variation data. All the genes in this table meet the mutation type `rearrangement`."

        return data_str
    
    def add_hint_to_study(self):
        """TODO: add hints for different types of studies, e.g., clinical study, genomic study, etc.
        """
        pass