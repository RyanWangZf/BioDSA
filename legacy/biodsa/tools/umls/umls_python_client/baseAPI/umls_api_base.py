import json
import logging
from typing import Any, Dict

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UMLSAPIBase:
    """
    Base class for handling common functionality for UMLS APIs (CUI, Source, Crosswalk, etc.).
    Attributes:
        api_key (str): The API key used for making requests to the UMLS API.
        version (str): The version of the UMLS content to use, defaults to "current".
        base_url (str): The base URL for the UMLS API.
        return_indented (bool): Whether or not to return indented JSON by default.
    """

    def __init__(self, api_key: str, version: str = "current"):
        """
        Initialize the UMLSAPIBase class with the API key, version, and return behavior.
        Args:
            api_key (str): The API key required for all API requests.
            version (str, optional): The version of the UMLS release to use. Defaults to "current".
            return_indented (bool, optional): Whether to return indented JSON by default. Defaults to True.
        Raises:
            ValueError: If the API key is not provided or is empty.
        """
        if not api_key:
            raise ValueError("API key is required for UMLS API requests.")

        self.api_key = api_key
        self.base_url = "https://uts-ws.nlm.nih.gov/rest"
        self.version = version

    def _format_json(self, data: Dict[str, Any]) -> str:
        """
        Format the JSON response with indentation.
        Args:
            data (Dict[str, Any]): The parsed JSON data.
        Returns:
            str: A formatted string of JSON data with indentation.
        """
        return json.dumps(data, indent=4)

    def _handle_response(self, response: requests.Response) -> Any:
        """
        Handle the response from an API request.
        Args:
            response (requests.Response): The HTTP response from the API request.
        Returns:
            Dict[str, Any] or str: The parsed JSON response if the request is successful,
            or an indented string if `return_indented` is True. Otherwise, returns a structured error message.
        """
        # Handle successful response
        if response.status_code == 200:
            try:
                response_json = response.json()  # Parse response as JSON

                return response_json  # Return raw JSON
            except ValueError as e:
                logger.error(f"Error parsing JSON response: {e}")
                return self._format_json({"error": "Invalid JSON in response."})

        # Handle Unauthorized (401)
        if response.status_code == 401:
            logger.error("Unauthorized: Invalid API key.")
            error_response = {
                "error": "Invalid API Key. Please verify your API key and try again.",
                "resolution": "Visit the UMLS API documentation for further details on how to obtain or renew your API key.",
                "documentation_url": "https://documentation.uts.nlm.nih.gov/rest/authentication.html",
            }
            return error_response

        # Handle Forbidden (403)
        if response.status_code == 403:
            logger.error("Forbidden: Access denied.")
            error_response = {
                "error": "Access denied. You do not have permission to access this resource.",
                "resolution": "Ensure that your API key has the appropriate permissions.",
            }
            return error_response
        # Handle Not Found (404)
        if response.status_code == 404:
            logger.error("Not Found: The requested resource does not exist.")
            error_response = {
                "error": "Resource not found. The requested resource could not be found.",
                "resolution": "Check the endpoint or resource identifier in the request.",
            }
            return error_response
        # Handle other client or server errors (4xx or 5xx)
        error_message = {
            "error": "API request failed.",
            "status_code": response.status_code,
            "message": response.text,
        }
        logger.error(
            f"API request failed with status code {response.status_code}: {response.text}"
        )
        return error_message
