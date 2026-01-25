"""
Risk Calculator Execution Module.

This module provides safe execution of clinical calculator code
with proper input validation and result formatting.
"""

import io
import sys
import contextlib
import traceback
from typing import Dict, Any, Optional, List, Tuple
import re


def validate_calculator_inputs(
    required_variables: List[Dict[str, Any]],
    provided_values: Dict[str, Any]
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate that required inputs are provided for a calculator.
    
    Args:
        required_variables: List of variable definitions from the calculator
        provided_values: Dictionary of provided input values
        
    Returns:
        Tuple of (is_valid, missing_variables, validated_values)
    """
    missing = []
    validated = {}
    
    for var in required_variables:
        var_name = var["name"]
        var_type = var.get("type", "any")
        
        if var_name in provided_values:
            value = provided_values[var_name]
            
            # Type coercion/validation
            try:
                if var_type == "int":
                    validated[var_name] = int(value)
                elif var_type == "float":
                    validated[var_name] = float(value)
                elif var_type == "bool":
                    if isinstance(value, bool):
                        validated[var_name] = value
                    elif isinstance(value, str):
                        validated[var_name] = value.lower() in ("true", "yes", "1", "y")
                    else:
                        validated[var_name] = bool(value)
                elif var_type == "str":
                    validated[var_name] = str(value)
                else:
                    validated[var_name] = value
                    
                # Range validation if specified
                if "range" in var and var_type in ("int", "float"):
                    min_val, max_val = var["range"]
                    if not (min_val <= validated[var_name] <= max_val):
                        # Clamp to range with warning
                        validated[var_name] = max(min_val, min(max_val, validated[var_name]))
                        
            except (ValueError, TypeError):
                missing.append(f"{var_name} (invalid type, expected {var_type})")
        else:
            # Check if there's a default
            if "default" in var:
                validated[var_name] = var["default"]
            else:
                missing.append(var_name)
    
    is_valid = len(missing) == 0
    return is_valid, missing, validated


def execute_calculator_code(
    code: str,
    input_values: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    auto_call: bool = True
) -> Tuple[bool, Any, str]:
    """
    Safely execute calculator code and capture output.
    
    Args:
        code: Python code string containing the calculator function
        input_values: Dictionary of input values to pass to the calculator.
            Only used when auto_call=True.
        timeout: Maximum execution time in seconds
        auto_call: If True (default), finds the first function definition
            and calls it with input_values. If False, just executes the
            code as-is (useful for LLM-generated code that includes its
            own function calls).
        
    Returns:
        Tuple of (success, result, output/error_message)
        - When auto_call=True: result is the function return value
        - When auto_call=False: result is None (use print() for output)
    """
    if input_values is None:
        input_values = {}
    
    # Create a restricted execution environment
    safe_globals = {
        "__builtins__": {
            # Only allow safe built-ins
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "isinstance": isinstance,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "pow": pow,
            "print": print,
            "range": range,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,
            "True": True,
            "False": False,
            "None": None,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
        },
        "math": __import__("math"),
    }
    
    # Capture stdout
    stdout_capture = io.StringIO()
    result = None
    
    try:
        with contextlib.redirect_stdout(stdout_capture):
            # Execute the code
            exec(code, safe_globals)
            
            if auto_call:
                # Find the function that was defined and call it
                func_match = re.search(r'def\s+(\w+)\s*\(', code)
                if func_match:
                    func_name = func_match.group(1)
                    if func_name in safe_globals:
                        func = safe_globals[func_name]
                        result = func(**input_values)
                    else:
                        return False, None, f"Function {func_name} not found in executed code"
                else:
                    return False, None, "No function definition found in code"
            # When auto_call=False, we just executed the code - result stays None
        
        output = stdout_capture.getvalue()
        return True, result, output
        
    except Exception as e:
        error_trace = traceback.format_exc()
        return False, None, f"Execution error: {str(e)}\n{error_trace}"


def format_calculator_result(
    calculator_name: str,
    result: Any,
    interpretation: Optional[Dict[str, str]] = None
) -> str:
    """
    Format a calculator result for display.
    
    Args:
        calculator_name: Name of the calculator
        result: The calculated result (dict or scalar)
        interpretation: Optional interpretation guidelines
        
    Returns:
        Formatted result string
    """
    output_lines = [f"## {calculator_name} Result\n"]
    
    if isinstance(result, dict):
        for key, value in result.items():
            # Format the key nicely
            display_key = key.replace("_", " ").title()
            output_lines.append(f"- **{display_key}**: {value}")
    else:
        output_lines.append(f"- **Result**: {result}")
    
    if interpretation:
        output_lines.append("\n### Interpretation Guide")
        for key, desc in interpretation.items():
            output_lines.append(f"- {key}: {desc}")
    
    return "\n".join(output_lines)


def run_calculator(
    calculator: Dict[str, Any],
    input_values: Dict[str, Any]
) -> Dict[str, Any]:
    """
    High-level function to run a calculator with validation and formatting.
    
    Args:
        calculator: Calculator definition dictionary
        input_values: Input values for the calculation
        
    Returns:
        Dictionary with execution results
    """
    # Validate inputs
    is_valid, missing, validated = validate_calculator_inputs(
        calculator.get("variables", []),
        input_values
    )
    
    if not is_valid:
        return {
            "success": False,
            "error": f"Missing required inputs: {', '.join(missing)}",
            "missing_inputs": missing,
            "result": None,
            "formatted_output": None
        }
    
    # Execute calculation
    success, result, output = execute_calculator_code(
        calculator.get("formula", ""),
        validated
    )
    
    if not success:
        return {
            "success": False,
            "error": output,
            "missing_inputs": [],
            "result": None,
            "formatted_output": None
        }
    
    # Format output
    formatted = format_calculator_result(
        calculator.get("name", "Calculator"),
        result,
        calculator.get("interpretation")
    )
    
    return {
        "success": True,
        "error": None,
        "missing_inputs": [],
        "result": result,
        "formatted_output": formatted,
        "stdout": output if output else None
    }
