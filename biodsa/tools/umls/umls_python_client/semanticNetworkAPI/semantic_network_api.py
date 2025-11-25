import logging
import os

import requests

from biodsa.tools.umls.umls_python_client.baseAPI.umls_api_base import UMLSAPIBase
from biodsa.tools.umls.umls_python_client.utils.save_output import save_output_to_file
from biodsa.tools.umls.umls_python_client.utils.utils import handle_response_with_format

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


class SemanticNetworkAPI(UMLSAPIBase):
    """
    A class to interact with the UMLS REST API's semantic network functionality, inheriting from UMLSAPIBase.

    The SemanticNetworkAPI class provides methods to retrieve semantic type information by its TUI (Type Unique Identifier).

    Attributes:
        api_key (str): The UMLS API key used for authentication (inherited from the UMLSAPIBase class).
        version (str): The version of the UMLS release to use (inherited from UMLSAPIBase).
    """

    def get_semantic_type(
        self,
        tui: str,
        save_to_file: bool = False,
        file_path: str = None,
        return_indented: bool = True,
        **kwargs,
    ):
        """
        Retrieve information about a semantic type using its TUI (Type Unique Identifier).
        Args:
            tui (str): The TUI identifier for the semantic type you want to retrieve.
        Returns:
            dict: The semantic type information retrieved from the UMLS API.
        """
        if "format" in kwargs:
            logger.warning(
                "Format is unavailable for this function, it will be enabled in future."
            )

        # Construct the URL for the semantic network endpoint
        url = f"{self.base_url}/semantic-network/{self.version}/TUI/{tui}"
        params = {"apiKey": self.api_key}

        # Log the API request
        logger.info(f"Fetching semantic type for TUI: {tui}")

        # Make the API request
        try:
            response = requests.get(url, params=params)
        except requests.RequestException as e:
            logger.error(f"Error during API request: {e}")
            return {"error": f"Request failed: {e}"}

        if save_to_file:
            if file_path == None:
                file_path = f"semantic_type_{tui}.txt"
            else:
                file_path = os.path.join(file_path, f"semantic_type_{tui}.txt")
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        # Handle the response (always returns JSON format)
        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )
