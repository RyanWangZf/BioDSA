import logging
import os
from typing import Any, Dict, Optional, Union

import requests

from biodsa.tools.umls.umls_python_client.baseAPI.umls_api_base import UMLSAPIBase
from biodsa.tools.umls.umls_python_client.utils.save_output import save_output_to_file
from biodsa.tools.umls.umls_python_client.utils.utils import handle_response_with_format

API_KEY = os.getenv("API_KEY")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


class CUIAPI(UMLSAPIBase):
    """
    The CUIAPI class is designed to interact with the UMLS REST API for Concept Unique Identifier (CUI) data retrieval.
    This class provides methods to fetch detailed information, atoms, definitions, and relations related to a given CUI.

    The CUIAPI class allows you to:
    - Retrieve detailed information about a CUI from the UMLS Metathesaurus.
    - Retrieve atoms (the smallest units of meaning) associated with a CUI.
    - Retrieve definitions tied to a given CUI.
    - Retrieve relationships (semantic relations between concepts) for a CUI.

    Attributes:
        api_key (str): The UMLS API key used for authentication (inherited from the UMLSAPIBase class).
        version (str): The version of the UMLS release to use (inherited from UMLSAPIBase).
        base_url (str): The base URL for UMLS API requests (inherited from UMLSAPIBase).
    """

    def get_cui_info(
        self,
        cui,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Fetches detailed information about the specified CUI from the UMLS Metathesaurus.
        - Parameters:
            - cui (str): The Concept Unique Identifier (CUI) to query.
        - Returns:
            - A dictionary containing the detailed information about the CUI.
        """

        url = f"{self.base_url}/content/{self.version}/CUI/{cui}"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)
        logger.info(f"Fetching CUI concept: {cui}")

        # Save to file if required
        if save_to_file:
            if file_path == None:
                file_path = f"cui_info_{cui}.txt"
            else:
                file_path = os.path.join(file_path, f"cui_info_{cui}.txt")
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_atoms(
        self,
        cui: str,
        return_indented: bool = True,
        sabs: Optional[str] = None,
        ttys: Optional[str] = None,
        language: Optional[str] = None,
        include_obsolete: bool = False,
        include_suppressible: bool = False,
        page_number: int = 1,
        page_size: int = 25,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Fetches atoms associated with the specified CUI.
        - Parameters:
            - cui (str): The Concept Unique Identifier (CUI) to query.
        - Returns:
            - A dictionary containing atoms related to the CUI.
        """
        # --format holdup
        url = f"{self.base_url}/content/{self.version}/CUI/{cui}/atoms"
        params = {
            "apiKey": self.api_key,
            "sabs": sabs,
            "ttys": ttys,
            "language": language,
            "includeObsolete": str(include_obsolete).lower(),
            "includeSuppressible": str(include_suppressible).lower(),
            "pageNumber": page_number,
            "pageSize": page_size,
        }

        # Filter out any None values from params
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        logger.info(f"Fetching CUI atoms for: {cui}")

        # Save to file if required
        if save_to_file:
            if file_path == None:
                file_path = f"cui_atoms_{cui}.txt"
            else:
                file_path = os.path.join(file_path, f"cui_atoms_{cui}.txt")
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_definitions(
        self,
        cui: str,
        return_indented: bool = True,
        sabs: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 25,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Fetches definitions associated with the specified CUI.
        - Parameters:
            - cui (str): The Concept Unique Identifier (CUI) to query.
        - Returns:
            - A dictionary containing definitions tied to the CUI.
        """

        url = f"{self.base_url}/content/{self.version}/CUI/{cui}/definitions"
        params = {
            "apiKey": self.api_key,
            "sabs": sabs,
            "pageNumber": page_number,
            "pageSize": page_size,
        }

        # Filter out any None values from params
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        logger.info(f"Fetching CUI definitions for: {cui}")

        # Save to file if required
        if save_to_file:
            if file_path == None:
                file_path = f"cui_definitions_{cui}.txt"
            else:
                file_path = os.path.join(file_path, f"cui_definitions_{cui}.txt")
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_relations(
        self,
        cui,
        return_indented: bool = True,
        sabs: Optional[str] = None,
        include_relation_labels: Optional[str] = None,
        include_additional_labels: Optional[str] = None,
        include_obsolete: bool = False,
        include_suppressible: bool = False,
        page_number: int = 1,
        page_size: int = 25,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Fetches relationships for the specified CUI.
        - Parameters:
            - cui (str): The Concept Unique Identifier (CUI) to query.
        - Returns:
            - A dictionary containing the relationships of the CUI.
        """

        url = f"{self.base_url}/content/{self.version}/CUI/{cui}/relations"
        params = {
            "apiKey": self.api_key,
            "sabs": sabs,
            "includeRelationLabels": include_relation_labels,
            "includeAdditionalRelationLabels": include_additional_labels,
            "includeObsolete": str(include_obsolete).lower(),
            "includeSuppressible": str(include_suppressible).lower(),
            "pageNumber": page_number,
            "pageSize": page_size,
        }

        # Filter out any None values from params
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        logger.info(f"Fetching CUI relations for: {cui}")

        # Save to file if required
        if save_to_file:
            if file_path == None:
                file_path = f"cui_relations_{cui}.txt"
            else:
                file_path = os.path.join(file_path, f"cui_relations_{cui}.txt")
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )
