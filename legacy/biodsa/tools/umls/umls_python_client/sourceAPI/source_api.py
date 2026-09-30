import json
import logging
import os
from typing import Any, Dict, Optional, Union

import requests

from biodsa.tools.umls.umls_python_client.baseAPI.umls_api_base import UMLSAPIBase
from biodsa.tools.umls.umls_python_client.utils.save_output import save_output_to_file
from biodsa.tools.umls.umls_python_client.utils.utils import handle_response_with_format

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


class SourceAPI(UMLSAPIBase):
    """Class for handling source-asserted UMLS API requests."""

    def get_source_concept(
        self,
        source: str,
        id: str,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:

        # Construct the URL and parameters for the API request
        url = f"{self.base_url}/content/{self.version}/source/{source}/{id}"
        params = {"apiKey": self.api_key}

        try:
            # Make the API request
            logger.info(f"Fetching source concept: {source}/{id}")
            response = requests.get(url, params=params)
            # If the status code error handling is already in _handle_response, no need to add it here

            # Save to file if required
            if save_to_file:
                if file_path == None:
                    file_path = f"source_concept_{source}_{id}.txt"
                else:
                    file_path = os.path.join(
                        file_path, f"source_concept_{source}_{id}.txt"
                    )
                save_output_to_file(
                    response=self._handle_response(response), file_path=file_path
                )

            return handle_response_with_format(
                response=self._handle_response(response),
                format="json",
                return_indented=return_indented,
            )

        except requests.RequestException as e:
            logger.error(f"Error making the API request: {e}")
            raise Exception(f"API request error: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding the API response as JSON: {e}")
            raise Exception(f"JSON decode error: {e}")

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise Exception(f"Unexpected error: {e}")

    def get_source_atoms(
        self,
        source: str,
        id: str,
        sabs: Optional[str] = None,
        ttys: Optional[str] = None,
        language: Optional[str] = None,
        include_obsolete: bool = False,
        include_suppressible: bool = False,
        page_number: int = 1,
        page_size: int = 25,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """Retrieve atoms for a known source-asserted identifier with optional filters."""

        url = f"{self.base_url}/content/{self.version}/source/{source}/{id}/atoms"

        # Parameters for the query
        params = {
            "apiKey": self.api_key,
            "sabs": sabs,  # Comma-separated list of source vocabularies (e.g., "SNOMEDCT_US,ICD10CM")
            "ttys": ttys,  # Comma-separated list of term types (e.g., "PT,SY")
            "language": language,  # Specific language (e.g., "ENG", "SPA")
            "includeObsolete": str(
                include_obsolete
            ).lower(),  # Include obsolete atoms or not
            "includeSuppressible": str(
                include_suppressible
            ).lower(),  # Include suppressible atoms or not
            "pageNumber": page_number,  # Page number to fetch
            "pageSize": page_size,  # Number of results per page
        }

        # Filter out any None values from the parameters (as they are optional)
        params = {k: v for k, v in params.items() if v is not None}

        # Make the request
        response = requests.get(url, params=params)
        logger.info(f"Fetching source atoms for: {source}/{id}")

        if save_to_file:
            if file_path == None:
                file_path = f"source_atoms_{source}_{id}.txt"
            else:
                file_path = os.path.join(file_path, f"source_atoms_{source}_{id}.txt")
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_source_parents(
        self,
        source: str,
        id: str,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """Retrieve immediate parents of a known source-asserted identifier."""

        url = f"{self.base_url}/content/{self.version}/source/{source}/{id}/parents"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)

        if save_to_file:
            if file_path == None:
                file_path = f"source_parents_{source}_{id}.txt"
            else:
                file_path = os.path.join(file_path, f"source_parents_{source}_{id}.txt")
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_source_children(
        self,
        source: str,
        id: str,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """Retrieve immediate children of a known source-asserted identifier."""

        url = f"{self.base_url}/content/{self.version}/source/{source}/{id}/children"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)

        if save_to_file:
            if file_path == None:
                file_path = f"source_children_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"source_children_{source}_{id}.txt"
                )
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_source_ancestors(
        self,
        source: str,
        id: str,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """Retrieve all ancestors of a known source-asserted identifier."""

        url = f"{self.base_url}/content/{self.version}/source/{source}/{id}/ancestors"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)
        logger.info(f"Fetching ancestors for: {source}/{id}")

        if save_to_file:
            if file_path == None:
                file_path = f"source_ancestors_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"source_ancestors_{source}_{id}.txt"
                )
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_source_descendants(
        self,
        source: str,
        id: str,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """Retrieve all descendants of a known source-asserted identifier."""

        url = f"{self.base_url}/content/{self.version}/source/{source}/{id}/descendants"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)
        logger.info(f"Fetching descendants for: {source}/{id}")

        if save_to_file:
            if file_path == None:
                file_path = f"source_descendants_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"source_descendants_{source}_{id}.txt"
                )
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_source_attributes(
        self,
        source: str,
        id: str,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """Retrieve information about source-asserted attributes."""
        url = f"{self.base_url}/content/{self.version}/source/{source}/{id}/attributes"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)

        if save_to_file:
            if file_path == None:
                file_path = f"source_attributes_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"source_attributes_{source}_{id}.txt"
                )
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_source_relations(
        self,
        source: str,
        id: str,
        include_relation_labels: Optional[str] = None,
        include_additional_labels: Optional[str] = None,
        include_obsolete: bool = False,
        include_suppressible: bool = False,
        page_number: int = 1,
        page_size: int = 25,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """Retrieve relationships for a known source-asserted identifier with optional parameters."""

        url = f"{self.base_url}/content/{self.version}/source/{source}/{id}/relations"

        params = {
            "apiKey": self.api_key,
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
        logger.info(f"Fetching relations for concept: {source}/{id}")

        if save_to_file:
            if file_path == None:
                file_path = f"source_relations_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"source_relations_{source}_{id}.txt"
                )
            save_output_to_file(
                response=self._handle_response(response), file_path=file_path
            )

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_relations_by_url(
        self, relations_url: str, return_indented: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """Make a second request to the relations endpoint and retrieve related concepts."""
        params = {"apiKey": self.api_key}
        response = requests.get(relations_url, params=params)
        logger.info(f"Fetching relations from URL: {relations_url}")

        return handle_response_with_format(
            response=self._handle_response(response),
            format="json",
            return_indented=return_indented,
        )

    def get_concept_pathways(
        self,
        source,
        id,
        max_depth=2,
        return_indented=True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Retrieve full parent-child pathways from the root to the concept and its descendants iteratively.

        Parameters:
            - source: The source vocabulary (e.g., SNOMEDCT_US, LOINC)
            - id: The concept ID for which to fetch the pathways
            - max_depth: The maximum depth to explore (default is 2)
        """

        def fetch_parents_children(concept_id, pathways, cache):
            """Fetch parents and children for a concept and store them in cache."""
            # Check if we have already fetched this concept
            if concept_id in cache:
                return cache[concept_id]

            # Fetch parents and children using the source API methods
            parents_response = self.get_source_parents(source, concept_id)
            children_response = self.get_source_children(source, concept_id)
            parents = json.loads(parents_response).get("result", [])
            children = json.loads(children_response).get("result", [])

            # Cache the results to avoid redundant API calls
            cache[concept_id] = {"parents": parents, "children": children}
            logger.info(f"Cache updated: {cache}")

            # Add to pathways
            if parents:
                pathways.setdefault(f"concept_{concept_id}_parents", []).extend(
                    [parent.get("name") for parent in parents]
                )
            if children:
                pathways.setdefault(f"concept_{concept_id}_children", []).extend(
                    [child.get("name") for child in children]
                )

            return cache[concept_id]

        # Initialize structures
        cache = {}
        pathways = {}
        queue = [(id, 0)]  # (concept_id, depth)

        # Process concepts iteratively using a queue (Breadth-First Search)
        while queue:
            concept_id, depth = queue.pop(0)  # Dequeue the first element

            if depth > max_depth:
                logger.info(f"Reached maximum depth for concept: {concept_id}")
                continue

            # Fetch the parents and children
            concept_data = fetch_parents_children(concept_id, pathways, cache)
            parents = concept_data["parents"]
            children = concept_data["children"]

            # Enqueue parents and children for further exploration
            for parent in parents:
                queue.append((parent.get("ui"), depth + 1))
            for child in children:
                queue.append((child.get("ui"), depth + 1))

        if save_to_file:
            if file_path == None:
                file_path = f"concept_pathways_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"concept_pathways_{source}_{id}.txt"
                )
            save_output_to_file(response=pathways, file_path=file_path)

        if return_indented:
            return json.dumps(pathways, indent=4)
        else:
            pathways

    def get_related_concepts_by_relation_type(
        self,
        source,
        id,
        relation_type,
        return_indented=True,
        save_to_file: bool = False,
        file_path: str = None,
    ):
        """Retrieve related concepts based on the specified relationship type."""
        # Step 1: Fetch the source concept
        concept_response = self.get_source_concept(source, id)

        # Step 2: Check if 'relations' is an endpoint URL
        relations_url = (
            json.loads(concept_response).get("result", {}).get("relations", "")
        )
        if isinstance(relations_url, str) and relations_url.startswith("http"):
            # If it's a URL, make a second request to fetch relations
            relations_response = self.get_relations_by_url(relations_url)
            relations = json.loads(relations_response).get("result", [])
        else:
            logger.warning(f"No valid relations endpoint found for concept: {id}")
            return {relation_type: []}

        # Step 3: Filter relations based on the specified relationship type
        related_concepts = []
        for relation in relations:
            # Ensure that the relation is a dictionary and has the required fields
            if (
                isinstance(relation, dict)
                and relation.get("relationLabel", "").lower() == relation_type.lower()
            ):
                # Use 'relatedIdName' to extract the related concept's name
                related_concept_name = relation.get("relatedIdName", "Unknown Concept")
                related_concepts.append(related_concept_name)

        # Step 4: Return related concepts based on the relation type
        if not related_concepts:
            logger.warning(
                f"No related concepts found for relation type '{relation_type}' in concept: {id}"
            )
        else:
            logger.info(
                f"Found {len(related_concepts)} related concepts for relation type '{relation_type}'."
            )

        if save_to_file:
            if file_path == None:
                file_path = f"related_concepts_by_relation_type_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"related_concepts_by_relation_type_{source}_{id}.txt"
                )
            save_output_to_file(
                response={relation_type: related_concepts}, file_path=file_path
            )

        if return_indented:
            return json.dumps({relation_type: related_concepts}, indent=4)
        else:
            {relation_type: related_concepts}

    # https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/attribute_names.html
    def get_concept_attributes(self, source: str, id: str) -> dict:
        """Retrieve specific attributes of a source-asserted concept."""
        attributes_response = self.get_source_attributes(source, id)
        attributes = json.loads(attributes_response).get("result", [])
        attribute_dict = {
            attribute.get("name"): attribute.get("value")
            for attribute in attributes
            if attribute.get("name") and attribute.get("value")
        }
        return attribute_dict

    def compare_concepts(
        self,
        source,
        id1,
        id2,
        return_indented=True,
        save_to_file: bool = False,
        file_path: str = None,
    ):
        """Compare two concepts by examining their relationships, ancestors, and descendants."""
        concept_1_ancestors = json.loads(self.get_source_ancestors(source, id1)).get(
            "result", []
        )
        concept_2_ancestors = json.loads(self.get_source_ancestors(source, id2)).get(
            "result", []
        )
        concept_1_descendants = json.loads(
            self.get_source_descendants(source, id1)
        ).get("result", [])
        concept_2_descendants = json.loads(
            self.get_source_descendants(source, id2)
        ).get("result", [])
        comparison = {
            "concept_1": id1,
            "concept_2": id2,
            "shared_ancestors": [
                ancestor.get("name")
                for ancestor in concept_1_ancestors
                if ancestor in concept_2_ancestors
            ],
            "shared_descendants": [
                descendant.get("name")
                for descendant in concept_1_descendants
                if descendant in concept_2_descendants
            ],
            "unique_to_concept_1": {
                "ancestors": [
                    ancestor.get("name")
                    for ancestor in concept_1_ancestors
                    if ancestor not in concept_2_ancestors
                ],
                "descendants": [
                    descendant.get("name")
                    for descendant in concept_1_descendants
                    if descendant not in concept_2_descendants
                ],
            },
            "unique_to_concept_2": {
                "ancestors": [
                    ancestor.get("name")
                    for ancestor in concept_2_ancestors
                    if ancestor not in concept_1_ancestors
                ],
                "descendants": [
                    descendant.get("name")
                    for descendant in concept_2_descendants
                    if descendant not in concept_1_descendants
                ],
            },
        }

        if save_to_file:
            if file_path == None:
                file_path = f"compare_concepts_{source}_{id1}_{id2}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"compare_concepts_{source}_{id1}_{id2}.txt"
                )
            save_output_to_file(response=comparison, file_path=file_path)

        if return_indented:
            return json.dumps(comparison, indent=4)
        else:
            comparison

    def get_concept_coverage(
        self,
        source: str,
        id: str,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> dict:
        """Check in which medical systems the concept is present."""
        concept_response = self.get_source_concept(source, id)
        source_systems = (
            json.loads(concept_response).get("result", {}).get("rootSource", [])
        )

        if save_to_file:
            if file_path == None:
                file_path = f"concept_coverage_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"concept_coverage_{source}_{id}.txt"
                )
            save_output_to_file(
                response={"concept_id": id, "covered_in_sources": source_systems},
                file_path=file_path,
            )

        if return_indented:
            return json.dumps(
                {"concept_id": id, "covered_in_sources": source_systems}, indent=4
            )
        else:
            {"concept_id": id, "covered_in_sources": source_systems}

    def aggregate_children_by_attribute(
        self,
        source: str,
        id: str,
        attribute_name: str,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ):
        """Aggregate children of a concept based on a specific attribute."""
        children_response = self.get_source_children(source, id)
        children = json.loads(children_response).get("result", [])
        attribute_aggregation = {}

        for child in children:
            child_id = child.get("ui")
            child_attributes = self.get_concept_attributes(source, child_id)

            # Log the attributes of the child for user awareness
            logger.info(
                f"Child ID: {child_id}, Available Attributes: {child_attributes}"
            )

            # Check if the requested attribute exists, otherwise use "Unknown"
            attribute_value = child_attributes.get(attribute_name, "Unknown")
            attribute_aggregation.setdefault(attribute_value, []).append(
                child.get("name")
            )

        if save_to_file:
            if file_path == None:
                file_path = f"children_by_attribute_{source}_{id}.txt"
            else:
                file_path = os.path.join(
                    file_path, f"children_by_attribute_{source}_{id}.txt"
                )
            save_output_to_file(response=attribute_aggregation, file_path=file_path)

        if return_indented:
            return json.dumps(attribute_aggregation, indent=4)
        else:
            return attribute_aggregation

    # New function to get the family tree structure
    def get_family_tree(
        self,
        source: str,
        id: str,
        max_depth: int = 3,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ):
        """Retrieve a family tree structure with relationships organized in a hierarchy of ancestors and descendants."""

        def fetch_ancestors(concept_id, hierarchy, depth=0):
            """Recursively fetch ancestors and add them to the family tree."""
            if depth >= max_depth:
                return
            response = self.get_source_parents(source, concept_id)
            parents = json.loads(response).get("result", [])
            if not parents:
                logger.info(f"No more parents found for: {concept_id}")
                return
            for parent in parents:
                parent_name = parent.get("name")
                parent_id = parent.get("ui")
                if parent_name:
                    hierarchy.setdefault(f"level_{depth}_parents", []).append(
                        parent_name
                    )
                    fetch_ancestors(parent_id, hierarchy, depth + 1)

        def fetch_descendants(concept_id, hierarchy, depth=0):
            """Recursively fetch descendants and add them to the family tree."""
            if depth >= max_depth:
                return
            response = self.get_source_children(source, concept_id)
            children = json.loads(response).get("result", [])
            if not children:
                logger.info(f"No more children found for: {concept_id}")
                return
            for child in children:
                child_name = child.get("name")
                child_id = child.get("ui")
                if child_name:
                    hierarchy.setdefault(f"level_{depth}_children", []).append(
                        child_name
                    )
                    fetch_descendants(child_id, hierarchy, depth + 1)

        # Initialize family tree structure
        family_tree = {
            "concept_id": id,
            "concept_name": None,
            "ancestors": {},
            "descendants": {},
        }

        # Fetch source concept details to get the name
        source_concept = self.get_source_concept(source, id)
        family_tree["concept_name"] = (
            json.loads(source_concept).get("result", {}).get("name", "Unknown Concept")
        )

        # Fetch ancestors and descendants in family tree structure
        fetch_ancestors(id, family_tree["ancestors"])
        fetch_descendants(id, family_tree["descendants"])

        if save_to_file:
            if file_path == None:
                file_path = f"family_tree_{source}_{id}.txt"
            else:
                file_path = os.path.join(file_path, f"family_tree_{source}_{id}.txt")
            save_output_to_file(response=family_tree, file_path=file_path)

        if return_indented:
            return json.dumps(family_tree, indent=4)
        else:
            return family_tree

    def get_full_hierarchy_recursive(
        self,
        source: str,
        id: str,
        depth: int = 0,
        return_indented: bool = True,
        save_to_file: bool = False,
        file_path: str = None,
    ) -> str | Dict[str, Any]:
        """Recursively retrieve all ancestors and descendants until root/leaf, with logging.

        Args:
            source (str): The source vocabulary from which to retrieve data.
            id (str): The concept identifier.
            depth (int): The depth for recursion (default: 0).
            return_indented (bool): Whether to return indented JSON output (default: True).
            save_to_file (bool): Whether to save the output to a file (default: False).
            file_path (str): The file path to save the output if `save_to_file` is True (default: 'family_tree_output.txt').

        Returns:
            str | dict: The full hierarchy in indented JSON format or as a dictionary, depending on `return_indented`.
        """

        def fetch_ancestors_recursive(
            concept_id: str, hierarchy: Dict[str, Any], depth: int = 0
        ) -> None:
            """Recursively fetch ancestors."""
            logger.info(
                f"Fetching ancestors at depth {depth} for concept: {concept_id}"
            )
            response = self.get_source_ancestors(source, concept_id)
            ancestors = json.loads(response).get("result", [])
            if not ancestors:
                logger.info(f"No more ancestors found for: {concept_id}")
                return
            for ancestor in ancestors:
                ancestor_id = ancestor.get("ui")
                if ancestor_id and ancestor_id not in [
                    a.get("ui") for a in hierarchy["ancestors"]
                ]:
                    hierarchy["ancestors"].append(ancestor)
                    fetch_ancestors_recursive(ancestor_id, hierarchy, depth + 1)

        def fetch_descendants_recursive(
            concept_id: str, hierarchy: Dict[str, Any], depth: int = 0
        ) -> None:
            """Recursively fetch descendants."""
            logger.info(
                f"Fetching descendants at depth {depth} for concept: {concept_id}"
            )
            response = self.get_source_descendants(source, concept_id)
            descendants = json.loads(response).get("result", [])
            if not descendants:
                logger.info(f"No more descendants found for: {concept_id}")
                return
            for descendant in descendants:
                descendant_id = descendant.get("ui")
                if descendant_id and descendant_id not in [
                    d.get("ui") for d in hierarchy["descendants"]
                ]:
                    hierarchy["descendants"].append(descendant)
                    fetch_descendants_recursive(descendant_id, hierarchy, depth + 1)

        # Initialize hierarchy structure
        hierarchy = {"concept_id": id, "ancestors": [], "descendants": []}

        # Recursively fetch ancestors and descendants with logging
        fetch_ancestors_recursive(id, hierarchy, depth=depth)
        fetch_descendants_recursive(id, hierarchy, depth=depth)

        # Save to file if required
        if save_to_file:
            if file_path == None:
                file_path = f"full_hierarchy_{source}_{id}.txt"
            else:
                file_path = os.path.join(file_path, f"full_hierarchy_{source}_{id}.txt")
            save_output_to_file(response=hierarchy, file_path=file_path)

        # Return the hierarchy in the requested format
        if return_indented:
            return json.dumps(hierarchy, indent=4)
        else:
            return hierarchy

    # def print_available_relations(self):
    #     """Print available relationship labels."""
    #     logger.info("Available relation labels:")
    #     for code, description in RELATION_LABELS.items():
    #         print(f"{code}: {description}")
