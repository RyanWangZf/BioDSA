from typing import Union

from pydantic import BaseModel


class Artifact(BaseModel):
    """
    Define the output artifact of code generation and execution
    """
    content: Union[bytes,str] = None # content of the artifact in bytes (like img) or string (like txt, html)
    file_name: str = None # the name of the artifact
    file_path: str = None # the path of the artifact in the local file system
    file_type: str = None # type of the artifact, e.g., "image", "csv", "json", "html", "pdf"

    def __str__(self) -> str:
        return f"""Artifact <{self.file_name}>"""
