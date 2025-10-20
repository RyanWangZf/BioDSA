"""Tools for the DeepEvidence agent.
"""
from typing import Literal, List, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class GoBreadthFirstSearchToolInput(BaseModel):
    search_target: str = Field(..., description="A one sentence description of the target of this round of breadth-first search.")
    knowledge_base: Literal["pubmed_papers", "pubmed_references"] = Field(..., description="The knowledge base to search on.")

class GoBreadthFirstSearchTool(BaseTool):
    """
    Call this tool to start a breadth-first search on the given knowledge base.
    """
    name: str = "go_breadth_first_search"
    description: str = "Call this tool to start a round of breadth-first search on the given knowledge base."
    args_schema: Type[BaseModel] = GoBreadthFirstSearchToolInput    
    def _run(self, 
        search_target: str,
        knowledge_base: Literal["pubmed_papers", "pubmed_references"]) -> str:
        """
        Start a round of breadth-first search on the given knowledge base.
        """
        pass

class GoDepthFirstSearchToolInput(BaseModel):
    search_target: str = Field(..., description="A one sentence description of the target of this round of depth-first search.")
    knowledge_base: Literal["pubmed_papers", "pubmed_references"] = Field(..., description="The knowledge base to search on.")

class GoDepthFirstSearchTool(BaseTool):
    """
    Call this tool to start a depth-first search on the given knowledge base.
    """
    name: str = "go_depth_first_search"
    description: str = "Call this tool to start a round of depth-first search on the given knowledge base."
    args_schema: Type[BaseModel] = GoDepthFirstSearchToolInput
    def _run(self, 
        search_target: str,
        knowledge_base: Literal["pubmed_papers", "pubmed_references"]) -> str:
        """
        Start a round of depth-first search on the given knowledge base.
        """
        pass