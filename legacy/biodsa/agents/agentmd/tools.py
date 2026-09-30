"""
Custom tools for the AgentMD clinical risk prediction agent.

These tools enable AgentMD to:
1. Retrieve relevant clinical calculators based on patient descriptions
2. Execute calculator code to compute risk predictions
3. Validate inputs and interpret results
"""
# IMPORTANT: Apply nest_asyncio FIRST before any other imports
# This is required for Jupyter notebooks and LangGraph which run their own event loops
import nest_asyncio
nest_asyncio.apply()

import warnings
warnings.filterwarnings("ignore", message="coroutine .* was never awaited", category=RuntimeWarning)

from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.tools.risk_calculators import (
    RiskCalcRetriever,
    retrieve_calculators,
    get_calculator_by_name,
    list_calculator_names,
    list_categories,
    # Full RiskCalcs dataset functions
    get_riskcalcs,
    get_riskcalc_raw,
    search_riskcalcs,
)
from biodsa.tools.risk_calculators.execution import (
    execute_calculator_code,
    validate_calculator_inputs,
    format_calculator_result,
    run_calculator,
)


class CalculatorSearchInput(BaseModel):
    """Input schema for clinical calculator search."""
    query: str = Field(
        description="Description of the clinical scenario or risk assessment needed. "
                    "E.g., 'chest pain risk stratification' or 'stroke risk in atrial fibrillation'"
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional category filter (cardiovascular, mortality, renal, bleeding, etc.)"
    )
    top_k: int = Field(
        default=5,
        description="Number of calculators to retrieve"
    )


class CalculatorSearchTool(BaseTool):
    """Tool for searching and retrieving relevant clinical calculators."""
    
    name: str = "search_calculators"
    description: str = """Search for relevant clinical calculators based on a patient description or clinical question.
    
Use this tool to find appropriate risk assessment calculators for a given clinical scenario.
You can search by:
- Clinical scenario (e.g., "chest pain evaluation", "stroke risk assessment")
- Condition (e.g., "atrial fibrillation", "pneumonia severity")
- Risk type (e.g., "mortality risk", "bleeding risk")

Returns a list of matching calculators with their names, purposes, and required inputs.
"""
    args_schema: Type[BaseModel] = CalculatorSearchInput
    
    def _run(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> str:
        """Execute the calculator search."""
        try:
            retriever = RiskCalcRetriever()
            results = retriever.retrieve(query, top_k=top_k, category_filter=category)
            
            if not results:
                return f"No calculators found for query: '{query}'. Try broadening your search terms."
            
            output_parts = [
                f"# Clinical Calculator Search Results",
                f"**Query:** {query}",
                f"**Results found:** {len(results)}",
                ""
            ]
            
            for i, result in enumerate(results, 1):
                calc_info = result.metadata
                variables = calc_info.get("variables", [])
                var_names = [v.get("name", "?") for v in variables]
                
                calc_block = [
                    f"## {i}. {result.title}",
                    f"**ID:** {result.calculator_id}",
                    f"**Category:** {calc_info.get('category', 'N/A')}",
                    f"**Purpose:** {result.purpose}",
                    f"**Required Inputs:** {', '.join(var_names)}",
                    f"**Relevance Score:** {result.score:.3f}",
                    ""
                ]
                output_parts.extend(calc_block)
            
            return "\n".join(output_parts)
            
        except Exception as e:
            return f"Error searching calculators: {str(e)}"


class CalculatorDetailsInput(BaseModel):
    """Input schema for getting calculator details."""
    calculator_id: str = Field(
        description="The ID of the calculator to get details for (e.g., 'heart_score', 'cha2ds2_vasc')"
    )


class CalculatorDetailsTool(BaseTool):
    """Tool for getting detailed information about a specific calculator."""
    
    name: str = "get_calculator_details"
    description: str = """Get detailed information about a specific clinical calculator including its formula, required inputs, and interpretation guidelines.
    
Use this tool when you need the full details of a calculator to apply it to a patient.
Returns the complete calculator specification including:
- Full list of input variables with types and descriptions
- The calculation formula/code
- Interpretation guidelines for the results
- Reference citation

This tool searches both the common built-in calculators and the full RiskCalcs dataset
(2,164+ clinical calculators from the original AgentMD repository).
"""
    args_schema: Type[BaseModel] = CalculatorDetailsInput
    
    def _run(self, calculator_id: str) -> str:
        """Get calculator details."""
        try:
            # First try common calculators
            calc = get_calculator_by_name(calculator_id)
            
            if calc is not None:
                # Format from Calculator dataclass (common calculators)
                var_lines = []
                for var in calc.variables:
                    var_desc = var.get("description", "No description")
                    var_type = var.get("type", "any")
                    unit = var.get("unit", "")
                    unit_str = f" ({unit})" if unit else ""
                    var_lines.append(f"- **{var['name']}** ({var_type}{unit_str}): {var_desc}")
                
                interp_lines = []
                for key, desc in calc.interpretation.items():
                    interp_lines.append(f"- **{key}**: {desc}")
                
                output = f"""# {calc.name}

**ID:** {calc.id}
**Category:** {calc.category}
**PMID:** {calc.pmid if calc.pmid else 'N/A'}

## Purpose
{calc.purpose}

## Required Variables
{chr(10).join(var_lines)}

## Formula/Code
```python
{calc.formula}
```

## Interpretation
{chr(10).join(interp_lines)}

## Reference
{calc.reference}
"""
                return output
            
            # Try the full RiskCalcs dataset
            raw_calc = get_riskcalc_raw(calculator_id)
            
            if raw_calc is not None:
                title = raw_calc.get("title", "").strip()
                purpose = raw_calc.get("purpose", "").strip()
                specialty = raw_calc.get("specialty", "N/A")
                eligibility = raw_calc.get("eligibility", "N/A").strip()
                computation = raw_calc.get("computation", "No computation available")
                interpretation = raw_calc.get("interpretation", "No interpretation available").strip()
                utility = raw_calc.get("utility", "").strip()
                example = raw_calc.get("example", "No example available")
                citation = raw_calc.get("citation", "N/A")
                citations_per_year = raw_calc.get("citations_per_year", "N/A")
                
                output = f"""# {title}

**ID (PMID):** {calculator_id}
**Specialty:** {specialty}
**Citations:** {citation} (citations/year: {citations_per_year:.1f if isinstance(citations_per_year, float) else citations_per_year})

## Purpose
{purpose}

## Eligibility
{eligibility}

## Computation
{computation}

## Interpretation
{interpretation}

## Clinical Utility
{utility}

## Example
{example}
"""
                return output
            
            # Calculator not found in any dataset
            common_available = list_calculator_names()
            return f"Calculator '{calculator_id}' not found.\n\n**Common calculators:** {', '.join(common_available)}\n\n**Note:** You can also search for calculators in the full RiskCalcs dataset (2,164+ calculators) using the search_calculators tool."
            
        except Exception as e:
            return f"Error getting calculator details: {str(e)}"


class RunCalculatorInput(BaseModel):
    """Input schema for running a calculator."""
    calculator_id: str = Field(
        description="The ID of the calculator to run"
    )
    input_values: Dict[str, Any] = Field(
        description="Dictionary of input values for the calculator. "
                    "Keys should match the variable names from the calculator specification."
    )


class RunCalculatorTool(BaseTool):
    """Tool for executing a clinical calculator with patient data."""
    
    name: str = "run_calculator"
    description: str = """Execute a clinical calculator with patient-specific input values.
    
Use this tool to apply a selected calculator to a patient's data.
Provide:
- calculator_id: The ID of the calculator (from search results)
- input_values: A dictionary mapping variable names to values

This tool works with both built-in common calculators and calculators from the
full RiskCalcs dataset (2,164+ calculators).

Example for common calculator:
```json
{
    "calculator_id": "heart_score",
    "input_values": {
        "history": 2,
        "ecg": 1,
        "age": 2,
        "risk_factors": 1,
        "troponin": 0
    }
}
```

For RiskCalcs calculators, the computation code is included in the calculator data
and will be executed with the provided input values.

Returns the calculated result with interpretation.
"""
    args_schema: Type[BaseModel] = RunCalculatorInput
    
    def _run(
        self,
        calculator_id: str,
        input_values: Dict[str, Any]
    ) -> str:
        """Run the calculator."""
        try:
            # First try common calculators
            calc = get_calculator_by_name(calculator_id)
            
            if calc is not None:
                # Run common calculator
                calc_dict = calc.to_dict()
                result = run_calculator(calc_dict, input_values)
                
                if not result["success"]:
                    return f"Calculation failed: {result['error']}"
                
                output_parts = [
                    f"# {calc.name} - Calculation Result",
                    "",
                    "## Inputs Used"
                ]
                
                for key, value in input_values.items():
                    output_parts.append(f"- **{key}**: {value}")
                
                output_parts.append("")
                output_parts.append("## Results")
                
                calc_result = result["result"]
                if isinstance(calc_result, dict):
                    for key, value in calc_result.items():
                        display_key = key.replace("_", " ").title()
                        output_parts.append(f"- **{display_key}**: {value}")
                else:
                    output_parts.append(f"- **Result**: {calc_result}")
                
                if result.get("stdout"):
                    output_parts.append("")
                    output_parts.append("## Execution Output")
                    output_parts.append(f"```\n{result['stdout']}\n```")
                
                output_parts.append("")
                output_parts.append("## Interpretation Guide")
                for key, desc in calc.interpretation.items():
                    output_parts.append(f"- **{key}**: {desc}")
                
                return "\n".join(output_parts)
            
            # Try RiskCalcs dataset
            raw_calc = get_riskcalc_raw(calculator_id)
            
            if raw_calc is not None:
                title = raw_calc.get("title", "Unknown Calculator").strip()
                computation = raw_calc.get("computation", "")
                interpretation = raw_calc.get("interpretation", "")
                
                if not computation:
                    return f"Calculator '{calculator_id}' found but has no computation code."
                
                # Extract and execute the Python code from computation
                # The computation field contains description + code block
                import re
                code_match = re.search(r'```python\s*(.*?)\s*```', computation, re.DOTALL)
                
                if code_match:
                    code = code_match.group(1).strip()
                else:
                    # Sometimes code is not in markdown blocks
                    code = computation
                
                # Execute the code with input values
                success, result_value, output = execute_calculator_code(code, input_values)
                
                output_parts = [
                    f"# {title} - Calculation Result",
                    f"**Calculator ID (PMID):** {calculator_id}",
                    "",
                    "## Inputs Used"
                ]
                
                for key, value in input_values.items():
                    output_parts.append(f"- **{key}**: {value}")
                
                output_parts.append("")
                
                if success:
                    output_parts.append("## Results")
                    if result_value is not None:
                        if isinstance(result_value, dict):
                            for key, value in result_value.items():
                                display_key = key.replace("_", " ").title()
                                output_parts.append(f"- **{display_key}**: {value}")
                        else:
                            output_parts.append(f"- **Result**: {result_value}")
                    
                    if output:
                        output_parts.append("")
                        output_parts.append("## Execution Output")
                        output_parts.append(f"```\n{output}\n```")
                else:
                    output_parts.append("## Execution Failed")
                    output_parts.append(f"```\n{output}\n```")
                    output_parts.append("")
                    output_parts.append("**Note:** The calculation code may require specific function calls.")
                    output_parts.append("Check the calculator details for the expected function signature and parameters.")
                
                if interpretation:
                    output_parts.append("")
                    output_parts.append("## Interpretation")
                    output_parts.append(interpretation[:1000] + ("..." if len(interpretation) > 1000 else ""))
                
                return "\n".join(output_parts)
            
            return f"Calculator '{calculator_id}' not found in common calculators or RiskCalcs dataset."
            
        except Exception as e:
            return f"Error running calculator: {str(e)}"


class ExecuteCodeInput(BaseModel):
    """Input schema for executing custom Python code."""
    code: str = Field(
        description="Python code to execute for custom calculations. "
                    "Use print() to output results. Basic math functions are available."
    )


class ExecuteCodeTool(BaseTool):
    """Tool for executing custom Python calculation code."""
    
    name: str = "execute_calculation"
    description: str = """Execute Python code for clinical calculations and return the output.

Use this tool to run Python code that applies clinical calculators.
The code should include print() statements to show results.

Your code should:
1. Define any needed functions (or use provided calculator functions)
2. Set up the patient values as variables
3. Call the function with those values
4. Print the results

Example:
```python
def calculate_bmi(height_m, weight_kg):
    return weight_kg / (height_m ** 2)

# Patient values
height = 1.75
weight = 80

# Calculate and print
bmi = calculate_bmi(height, weight)
print(f"BMI: {bmi:.1f} kg/m²")
```

The output from print() statements will be returned to you.
"""
    args_schema: Type[BaseModel] = ExecuteCodeInput
    
    def _run(self, code: str) -> str:
        """Execute the code using BioDSA's execution engine."""
        # Use BioDSA's execute_calculator_code with auto_call=False
        # This just runs the code as-is without trying to find/call functions
        success, result, output = execute_calculator_code(code, auto_call=False)
        
        if not success:
            return f"## Execution Error\n```\n{output}\n```\n\nPlease fix the error and try again."
        
        if output:
            return f"## Execution Output\n```\n{output}```"
        else:
            return "Code executed successfully but produced no output. Make sure to use print() to show results."


class ListCalculatorsInput(BaseModel):
    """Input schema for listing calculators."""
    category: Optional[str] = Field(
        default=None,
        description="Optional category to filter by (cardiovascular, mortality, renal, etc.)"
    )
    include_riskcalcs_info: bool = Field(
        default=True,
        description="Whether to include information about the full RiskCalcs dataset availability"
    )


class ListCalculatorsTool(BaseTool):
    """Tool for listing all available clinical calculators."""
    
    name: str = "list_calculators"
    description: str = """List all available clinical calculators in the toolkit.
    
Use this tool to see what calculators are available before searching.
Can optionally filter by category.

The toolkit includes:
- 8 common built-in calculators (always available, no download required)
- 2,164+ calculators from the RiskCalcs dataset (downloaded and cached on first use)

Use the search_calculators tool to search across the full RiskCalcs dataset.
"""
    args_schema: Type[BaseModel] = ListCalculatorsInput
    
    def _run(self, category: Optional[str] = None, include_riskcalcs_info: bool = True) -> str:
        """List calculators."""
        try:
            from biodsa.tools.risk_calculators.calculator_library import COMMON_CALCULATORS
            
            categories = list_categories()
            
            output_parts = [
                "# Available Clinical Calculators",
                "",
                "## Built-in Common Calculators",
                f"**Total:** {len(COMMON_CALCULATORS)}",
                f"**Categories:** {', '.join(categories)}",
                ""
            ]
            
            if category:
                filtered = {k: v for k, v in COMMON_CALCULATORS.items() 
                           if v.category.lower() == category.lower()}
                output_parts.append(f"### Filtered by: {category}")
            else:
                filtered = COMMON_CALCULATORS
            
            # Group by category
            by_category: Dict[str, List] = {}
            for calc_id, calc in filtered.items():
                cat = calc.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append((calc_id, calc))
            
            for cat, calcs in sorted(by_category.items()):
                output_parts.append(f"\n### {cat.title()}")
                for calc_id, calc in calcs:
                    output_parts.append(f"- **{calc_id}**: {calc.name} - {calc.purpose[:60]}...")
            
            # Add information about full RiskCalcs dataset
            if include_riskcalcs_info:
                output_parts.append("")
                output_parts.append("---")
                output_parts.append("")
                output_parts.append("## Full RiskCalcs Dataset")
                output_parts.append("**Total Available:** 2,164+ clinical calculators")
                output_parts.append("")
                output_parts.append("The full RiskCalcs dataset from the AgentMD paper is available and will be")
                output_parts.append("automatically downloaded and cached when you use the **search_calculators** tool.")
                output_parts.append("")
                output_parts.append("**Specialties covered include:**")
                output_parts.append("- Cardiology, Neurology, Pulmonology, Nephrology")
                output_parts.append("- Emergency Medicine, Critical Care, Oncology")
                output_parts.append("- Internal Medicine, Geriatrics, and many more")
                output_parts.append("")
                output_parts.append("Use `search_calculators` with a clinical query to find the most relevant")
                output_parts.append("calculator for your patient scenario.")
            
            return "\n".join(output_parts)
            
        except Exception as e:
            return f"Error listing calculators: {str(e)}"


def get_agentmd_tools() -> List[BaseTool]:
    """Get all tools for the AgentMD agent."""
    return [
        CalculatorSearchTool(),
        CalculatorDetailsTool(),
        RunCalculatorTool(),
        ExecuteCodeTool(),
        ListCalculatorsTool(),
    ]
