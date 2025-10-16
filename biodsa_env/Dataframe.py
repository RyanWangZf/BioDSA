from pydantic import BaseModel


class Dataframe(BaseModel):
    """
    Define the input dataset for code generation and execution
    """
    dataframe_id: str = None # unique identifier of the dataframe
    path: str = None # remote path (in the sandbox) or local path of the data
    table_name: str = None # name of the table, e.g., "adsl"
    data_schema: str = None # schema description of the data

    def __str__(self) -> str:
        return f"""Dataframe schema <{self.data_schema}>"""