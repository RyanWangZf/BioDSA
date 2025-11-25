"""Tools for the DeepEvidence agent.
"""
from typing import List, Type
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import BaseTool

from biodsa.agents.deepevidence.schema import KNOWLEDGE_BASE_LIST


def create_bfs_tool(allowed_knowledge_bases: List[str], maximum_search_rounds: int) -> Type[BaseTool]:
    """
    Factory function to create a BFS tool with dynamically constrained knowledge bases.
    
    Args:
        allowed_knowledge_bases: List of knowledge bases that the user wants to make available
    
    Returns:
        A tool class with the specified knowledge base constraints
    """
    # Validate that allowed knowledge bases are in the predefined list
    for kb in allowed_knowledge_bases:
        if kb not in KNOWLEDGE_BASE_LIST:
            raise ValueError(f"Unknown knowledge base: {kb}. Must be one of {KNOWLEDGE_BASE_LIST}")
    
    class GoBreadthFirstSearchToolInput(BaseModel):
        search_rounds_budget: int = Field(
            ...,
            description=f"The maximum round of search the BFS agent can perform. it should be greater than 3 and less than {maximum_search_rounds}."
        )
        knowledge_bases: List[str] = Field(
            ..., 
            description=f"A list of target knowledge bases to search on in breadth. Valid options: {allowed_knowledge_bases}. You MUST choose from these options only.",
            json_schema_extra={
                "items": {
                    "type": "string",
                    "enum": allowed_knowledge_bases
                }
            }
        )
        search_target: str = Field(
            ..., 
            description=(
                "Clear and informative research objective that must include: "
                "(1) WHAT specific information or data is needed (e.g., percentages, residues, experimental conditions, evidence types), "
                "(2) KEY ENTITIES to search for (e.g., gene names, protein names, disease names, chemical names, specific PMIDs if known), better to use the standardized entity names or IDs found if possible, e.g., pubtator ID, UMLS CUI, etc."
                "Be concrete and specific so the sub-agent knows exactly what to look for and when to stop searching."
                "Make sure the search target is restricted to searching entities exist in the given knowledge bases."
            )
        )
        
        @field_validator('knowledge_bases')
        @classmethod
        def validate_knowledge_bases(cls, v: List[str]) -> List[str]:
            for kb in v:
                if kb not in allowed_knowledge_bases:
                    raise ValueError(f"Invalid knowledge base: {kb}. Must be one of {allowed_knowledge_bases}")
            return v

    class GoBreadthFirstSearchTool(BaseTool):
        """
        Call this tool to start a breadth-first search on the given knowledge base.
        """
        name: str = "go_breadth_first_search"
        description: str = f"Call this tool to start a round of breadth-first search on the given knowledge bases. Available knowledge bases: {allowed_knowledge_bases}"
        args_schema: Type[BaseModel] = GoBreadthFirstSearchToolInput
        
        def _run(self, search_rounds_budget: int, knowledge_bases: List[str], search_target: str) -> str:
            """
            Start a round of breadth-first search on the given knowledge base.
            """
            return f"Breadth-first search started on {knowledge_bases} with budget {search_rounds_budget}."
    
    return GoBreadthFirstSearchTool


def create_dfs_tool(allowed_knowledge_bases: List[str], maximum_search_rounds: int) -> Type[BaseTool]:
    """
    Factory function to create a DFS tool with dynamically constrained knowledge bases.
    
    Args:
        allowed_knowledge_bases: List of knowledge bases that the user wants to make available
    
    Returns:
        A tool class with the specified knowledge base constraints
    """
    # Validate that allowed knowledge bases are in the predefined list
    for kb in allowed_knowledge_bases:
        if kb not in KNOWLEDGE_BASE_LIST:
            raise ValueError(f"Unknown knowledge base: {kb}. Must be one of {KNOWLEDGE_BASE_LIST}")
    
    class GoDepthFirstSearchToolInput(BaseModel):
        search_rounds_budget: int = Field(
            ...,
            description=f"The maximum round of search the DFS agent can perform. it should be greater than 3 and less than {maximum_search_rounds}."
        )
        knowledge_bases: List[str] = Field(
            ..., 
            description=f"A list of target knowledge bases to search on in depth. Valid options: {allowed_knowledge_bases}. You MUST choose from these options only.",
            json_schema_extra={
                "items": {
                    "type": "string",
                    "enum": allowed_knowledge_bases
                }
            }
        )
        search_target: str = Field(
            ..., 
            description=(
                "Clear and informative research objective that must include: "
                "(1) WHAT specific information or data is needed (e.g., specific mutations, exact experimental results, citation chain to follow), "
                "(2) KEY ENTITIES to search for (e.g., gene names, protein interactions, specific papers or authors), better to use the standardized entity names or IDs found if possible, e.g., pubtator ID, UMLS CUI, etc."
                "Be concrete and specific so the sub-agent knows exactly what to look for and when to stop searching."
                "Make sure the search target is restricted to searching entities exist in the given knowledge bases."
            )
        )
        
        @field_validator('knowledge_bases')
        @classmethod
        def validate_knowledge_bases(cls, v: List[str]) -> List[str]:
            for kb in v:
                if kb not in allowed_knowledge_bases:
                    raise ValueError(f"Invalid knowledge base: {kb}. Must be one of {allowed_knowledge_bases}")
            return v

    class GoDepthFirstSearchTool(BaseTool):
        """
        Call this tool to start a depth-first search on the given knowledge bases.
        """
        name: str = "go_depth_first_search"
        description: str = f"Call this tool to start a round of depth-first search on the given knowledge bases. Available knowledge bases: {allowed_knowledge_bases}"
        args_schema: Type[BaseModel] = GoDepthFirstSearchToolInput
        
        def _run(self, search_rounds_budget: int, knowledge_bases: List[str], search_target: str) -> str:
            """
            Start a round of depth-first search on the given knowledge bases.
            """
            return f"Depth-first search started on {knowledge_bases} with budget {search_rounds_budget}."
    
    return GoDepthFirstSearchTool
