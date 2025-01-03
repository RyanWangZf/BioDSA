"""Define the input code snippet for code generation and execution
"""
from typing import List, Union, Literal
from pydantic import BaseModel

class CodeSnippet(BaseModel):
    code: str = None
    doc_id: str = None # unique identifier for the code snippet in the indexed database
    data_story: str = None # the data story that the code snippet is associated with
    desc: str = None # description of the code snippet functions
    dependency: List[str] = None # list of doc ids of the code snippet's dependencies
    imported: List[str] = None # list of functions and variables imported in the code snippet

"""Define the input dataset for code generation and execution
"""
from typing import List, Union, Literal
from pydantic import BaseModel

class Dataframe(BaseModel):
    dataframe_id: str = None # unique identifier of the dataframe
    path: str = None # remote path (in the sandbox) or local path of the data
    table_name: str = None # name of the table, e.g., "adsl"
    data_schema: str = None # schema description of the data

    def __str__(self) -> str:
        return f"""Dataframe schema <{self.data_schema}>"""
    
class Artifact(BaseModel):
    content: Union[bytes,str] = None # content of the artifact in bytes (like img) or string (like txt, html)
    file_name: str = None # the name of the artifact
    file_path: str = None # the path of the artifact in the local file system
    file_type: str = None # type of the artifact, e.g., "image", "csv", "json", "html", "pdf"

    def __str__(self) -> str:
        return f"""Artifact <{self.file_name}>"""
    
"""Define the schema for the input and output used in the TrialMindAPIs
"""
from typing import List, Union, Literal
from pydantic import BaseModel

class MessageObject(BaseModel):
    # each message object should have either the StringData or the ObejctData, but never both.
    # we keep the same interface for them, however, to make implementation more concise

    # StringData
    text: str = None

    # ObjectData
    data_modality: str = None
    data_uuid: str = None


class ChatResponse(BaseModel):
    message_objects: List[MessageObject] = None
    # should be the data_uuid of a previous messages ObjectData
    message_subjects: List[str] = None


class Message(BaseModel):
    role: Literal['assistant','user','system'] = None  # 'assistant' | 'user' | 'system'
    content: ChatResponse

    def __str__(self) -> str:
        return f"""Message with role: <{self.role}> content <{self.content}>"""

