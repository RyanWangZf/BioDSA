import json
import logging

logger = logging.getLogger(__name__)


def handle_response_with_format(
    response, format: str = "json", return_indented: bool = True
) -> str:
    """
    Generalized function to handle response and return it in JSON format.

    Args:
        response: The API response to handle.
        format (str): The format in which the response should be returned. Only 'json' is supported.
        return_indented (bool): Whether to return indented JSON for better readability.

    Returns:
        str: The formatted response as a JSON string.
    """
    try:
        # Handle JSON format (only supported format)
        if format != "json":
            logger.warning(
                f"Format '{format}' is not supported. Only 'json' format is supported. Returning JSON."
            )
        
        if return_indented:
            return json.dumps(response, indent=4)
        else:
            return response

    except Exception as e:
        logger.error(
            f"An error occurred while handling the response: {e}. Returning raw response."
        )
        return str(response)
