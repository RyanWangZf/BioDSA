"""
State definitions for the AgentMD agent.

Note: The current AgentMD implementation uses a simple two-step workflow
without LangGraph. These Pydantic models are provided for potential
future extensions or for structured data handling.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RiskQAQuestion(BaseModel):
    """A question from the RiskQA benchmark dataset."""
    question: str = Field(description="The clinical question")
    choices: Dict[str, str] = Field(
        default_factory=dict,
        description="Answer choices (A, B, C, D)"
    )
    answer: str = Field(default="", description="Correct answer letter")
    pmid: str = Field(default="", description="PMID of the relevant calculator")


class CalculatorResult(BaseModel):
    """Result from applying a clinical calculator."""
    calculator_id: str = Field(description="PMID of the calculator used")
    calculator_title: str = Field(description="Title of the calculator")
    input_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input values used in calculation"
    )
    result_value: Optional[Any] = Field(
        default=None,
        description="Calculated result value"
    )
    interpretation: str = Field(default="", description="Clinical interpretation of the result")
    execution_success: bool = Field(default=True, description="Whether calculation succeeded")
    error_message: str = Field(default="", description="Error message if calculation failed")
