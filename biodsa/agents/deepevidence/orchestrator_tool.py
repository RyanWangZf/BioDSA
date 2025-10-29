"""Tools for the DeepEvidence agent.
"""
from typing import List, Type
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import BaseTool

from biodsa.agents.deepevidence.schema import KNOWLEDGE_BASE_LIST


def create_bfs_tool(allowed_knowledge_bases: List[str]) -> Type[BaseTool]:
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
        search_target: str = Field(
            ..., 
            description=(
                "Clear and informative research objective that must include: "
                "(1) WHAT specific information or data is needed (e.g., percentages, residues, experimental conditions, evidence types), "
                "(2) KEY ENTITIES to search for (e.g., gene names, protein names, disease names, chemical names, specific PMIDs if known), "
                "(3) CONTEXT and constraints (e.g., cell types, species, experimental methods, study types), "
                "(4) SUCCESS CRITERIA - what constitutes a complete answer (e.g., 'need exact percentage', 'need PMID with full experimental details', 'need specific residue ranges'). "
                "Be concrete and specific so the sub-agent knows exactly what to look for and when to stop searching."
            )
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
        
        def _run(self, search_target: str, knowledge_bases: List[str]) -> str:
            """
            Start a round of breadth-first search on the given knowledge base.
            """
            return f"Breadth-first search started on {knowledge_bases}."
    
    return GoBreadthFirstSearchTool


def create_dfs_tool(allowed_knowledge_bases: List[str]) -> Type[BaseTool]:
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
        search_target: str = Field(
            ..., 
            description=(
                "Clear and informative research objective that must include: "
                "(1) WHAT specific information or data is needed (e.g., specific mutations, exact experimental results, citation chain to follow), "
                "(2) KEY ENTITIES to search for (e.g., gene names, protein interactions, specific papers or authors), "
                "(3) CONTEXT and constraints (e.g., cell types, species, experimental methods, publication timeframe), "
                "(4) SUCCESS CRITERIA - what constitutes a complete answer (e.g., 'need primary paper with deletion mutant data', 'need full text to extract Table 2', 'trace citation to original source'). "
                "For DFS, also specify: which papers to follow citations from, or which review papers to trace back to primary sources. "
                "Be concrete and specific so the sub-agent knows exactly what to look for and when to stop searching."
            )
        )
        knowledge_base: str = Field(
            ..., 
            description=f"One target knowledge base to search on in depth. Valid options: {allowed_knowledge_bases}. You MUST choose from these options only.",
            json_schema_extra={
                "enum": allowed_knowledge_bases
            }
        )
        
        @field_validator('knowledge_base')
        @classmethod
        def validate_knowledge_base(cls, v: str) -> str:
            if v not in allowed_knowledge_bases:
                raise ValueError(f"Invalid knowledge base: {v}. Must be one of {allowed_knowledge_bases}")
            return v

    class GoDepthFirstSearchTool(BaseTool):
        """
        Call this tool to start a depth-first search on the given knowledge base.
        """
        name: str = "go_depth_first_search"
        description: str = f"Call this tool to start a round of depth-first search on the given knowledge base. Available knowledge bases: {allowed_knowledge_bases}"
        args_schema: Type[BaseModel] = GoDepthFirstSearchToolInput
        
        def _run(self, search_target: str, knowledge_base: str) -> str:
            """
            Start a round of depth-first search on the given knowledge base.
            """
            return f"Depth-first search started on {knowledge_base}."
    
    return GoDepthFirstSearchTool


# Default tool classes for backward compatibility (use all available knowledge bases)
GoBreadthFirstSearchTool = create_bfs_tool(KNOWLEDGE_BASE_LIST)
GoDepthFirstSearchTool = create_dfs_tool(KNOWLEDGE_BASE_LIST)