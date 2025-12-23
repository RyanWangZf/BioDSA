import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def save_output_to_file(response: Any, file_path: str) -> None:
    """
    Save the JSON response to a file with proper error handling.

    Args:
        response (Any): The data to save to the file, typically a JSON-like object (dict or list).
        file_path (str): The path of the file where the response will be saved.

    Returns:
        None
    """
    try:
        # Write the response to the specified file path
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(response, indent=4))
        logger.info(f"Output successfully saved to {file_path}")
    except Exception as e:
        # Log the error if file saving fails
        logger.error(f"Failed to save output to {file_path}: {e}")
