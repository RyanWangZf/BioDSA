"""Client for the Open Targets Platform API

This module provides a Python client for interacting with the Open Targets Platform API.
It implements tools for target-disease associations, target search, disease search, and
comprehensive entity information retrieval.

Open Targets Platform API Documentation: https://platform-docs.opentargets.org/data-access/graphql-api
"""

import logging
from typing import Any, Dict, List, Optional, Union

import requests

logger = logging.getLogger(__name__)


class OpenTargetsClient:
    """Client for interacting with the Open Targets Platform API.
    
    This client provides methods for querying the Open Targets Platform including
    targets (genes), diseases, drugs, and target-disease associations with
    supporting evidence.
    """
    
    REST_BASE_URL = "https://api.platform.opentargets.org/api/v4"
    GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"
    
    def __init__(self, timeout: int = 30):
        """Initialize the Open Targets client.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-OpenTargets-Client/1.0',
            'Content-Type': 'application/json'
        })
    
    def _make_rest_request(self, endpoint: str) -> Dict[str, Any]:
        """Make a REST API request to Open Targets.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.REST_BASE_URL}/{endpoint}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def _make_graphql_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GraphQL API request to Open Targets.
        
        Args:
            query: GraphQL query string
            variables: Query variables (optional)
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        payload = {
            'query': query,
            'variables': variables or {}
        }
        response = self.session.post(
            self.GRAPHQL_URL,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # Target Search Methods
    
    def search_targets(
        self,
        query: str,
        size: int = 25
    ) -> Dict[str, Any]:
        """Search for therapeutic targets by gene symbol, name, or description.
        
        Args:
            query: Search query (gene symbol, name, description)
            size: Number of results to return (1-500, default: 25)
            
        Returns:
            Dictionary containing search results with target information
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> results = client.search_targets("BRCA1", size=10)
            >>> print(results['data']['search']['hits'])
        """
        graphql_query = """
        query SearchTargets($queryString: String!) {
          search(queryString: $queryString, entityNames: ["target"]) {
            hits {
              id
              name
              description
              entity
            }
          }
        }
        """
        
        response = self._make_graphql_request(
            graphql_query,
            variables={'queryString': query}
        )
        
        # Limit results on client side
        hits = response.get('data', {}).get('search', {}).get('hits', [])
        limited_hits = hits[:size]
        
        return {
            'data': {
                'search': {
                    'hits': limited_hits,
                    'total': len(hits)
                }
            }
        }
    
    def search_diseases(
        self,
        query: str,
        size: int = 25
    ) -> Dict[str, Any]:
        """Search for diseases by name, synonym, or description.
        
        Args:
            query: Search query (disease name, synonym, description)
            size: Number of results to return (1-500, default: 25)
            
        Returns:
            Dictionary containing search results with disease information
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> results = client.search_diseases("lung cancer", size=10)
            >>> print(results['data']['search']['hits'])
        """
        graphql_query = """
        query SearchDiseases($queryString: String!) {
          search(queryString: $queryString, entityNames: ["disease"]) {
            hits {
              id
              name
              description
              entity
            }
          }
        }
        """
        
        response = self._make_graphql_request(
            graphql_query,
            variables={'queryString': query}
        )
        
        # Limit results on client side
        hits = response.get('data', {}).get('search', {}).get('hits', [])
        limited_hits = hits[:size]
        
        return {
            'data': {
                'search': {
                    'hits': limited_hits,
                    'total': len(hits)
                }
            }
        }
    
    # Target Details
    
    def get_target_details(self, target_id: str) -> Dict[str, Any]:
        """Get comprehensive target information.
        
        Args:
            target_id: Target Ensembl gene ID (e.g., "ENSG00000139618")
            
        Returns:
            Dictionary containing detailed target information
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> details = client.get_target_details("ENSG00000139618")
            >>> print(details['data']['target'])
        """
        graphql_query = """
        query GetTarget($ensemblId: String!) {
          target(ensemblId: $ensemblId) {
            id
            approvedName
            approvedSymbol
            biotype
            genomicLocation {
              chromosome
              start
              end
              strand
            }
            functionDescriptions
            pathways {
              pathway
              pathwayId
            }
            proteinIds {
              id
              source
            }
            synonyms {
              label
              source
            }
            tractability {
              label
              modality
              value
            }
          }
        }
        """
        
        return self._make_graphql_request(
            graphql_query,
            variables={'ensemblId': target_id}
        )
    
    # Disease Details
    
    def get_disease_details(self, disease_id: str) -> Dict[str, Any]:
        """Get comprehensive disease information.
        
        Args:
            disease_id: Disease EFO ID (e.g., "EFO_0000508")
            
        Returns:
            Dictionary containing detailed disease information
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> details = client.get_disease_details("EFO_0000508")
            >>> print(details['data']['disease'])
        """
        graphql_query = """
        query GetDisease($efoId: String!) {
          disease(efoId: $efoId) {
            id
            name
            description
            synonyms {
              terms
            }
            therapeuticAreas {
              id
              name
            }
            parents {
              id
              name
            }
            children {
              id
              name
            }
            ontology {
              isTherapeuticArea
              leaf
              sources {
                name
                url
              }
            }
          }
        }
        """
        
        return self._make_graphql_request(
            graphql_query,
            variables={'efoId': disease_id}
        )
    
    # Association Methods
    
    def get_target_associations(
        self,
        target_id: str,
        size: int = 25,
        min_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get diseases associated with a specific target.
        
        Args:
            target_id: Target Ensembl gene ID (e.g., "ENSG00000139618")
            size: Number of associations to return (default: 25)
            min_score: Minimum association score threshold (0-1, optional)
            
        Returns:
            Dictionary containing target-disease associations
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> assocs = client.get_target_associations("ENSG00000139618", size=10)
            >>> print(assocs['data']['target']['associatedDiseases'])
        """
        graphql_query = """
        query GetTargetAssociations($ensemblId: String!, $page: Pagination) {
          target(ensemblId: $ensemblId) {
            id
            approvedSymbol
            approvedName
            associatedDiseases(page: $page) {
              count
              rows {
                disease {
                  id
                  name
                }
                score
                datatypeScores {
                  id
                  score
                }
              }
            }
          }
        }
        """
        
        response = self._make_graphql_request(
            graphql_query,
            variables={
                'ensemblId': target_id,
                'page': {'size': size, 'index': 0}
            }
        )
        
        # Filter by score if specified
        if min_score is not None:
            associations = response.get('data', {}).get('target', {}).get('associatedDiseases', {})
            if associations:
                rows = associations.get('rows', [])
                filtered_rows = [row for row in rows if row.get('score', 0) >= min_score]
                associations['rows'] = filtered_rows
                associations['count'] = len(filtered_rows)
        
        return response
    
    def get_disease_associations(
        self,
        disease_id: str,
        size: int = 25,
        min_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get targets associated with a specific disease.
        
        Args:
            disease_id: Disease EFO ID (e.g., "EFO_0000508")
            size: Number of associations to return (default: 25)
            min_score: Minimum association score threshold (0-1, optional)
            
        Returns:
            Dictionary containing disease-target associations
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> assocs = client.get_disease_associations("EFO_0000508", size=10)
            >>> print(assocs['data']['disease']['associatedTargets'])
        """
        graphql_query = """
        query GetDiseaseAssociations($efoId: String!, $page: Pagination) {
          disease(efoId: $efoId) {
            id
            name
            associatedTargets(page: $page) {
              count
              rows {
                target {
                  id
                  approvedSymbol
                  approvedName
                }
                score
                datatypeScores {
                  id
                  score
                }
              }
            }
          }
        }
        """
        
        response = self._make_graphql_request(
            graphql_query,
            variables={
                'efoId': disease_id,
                'page': {'size': size, 'index': 0}
            }
        )
        
        # Filter by score if specified
        if min_score is not None:
            associations = response.get('data', {}).get('disease', {}).get('associatedTargets', {})
            if associations:
                rows = associations.get('rows', [])
                filtered_rows = [row for row in rows if row.get('score', 0) >= min_score]
                associations['rows'] = filtered_rows
                associations['count'] = len(filtered_rows)
        
        return response
    
    def get_disease_targets_summary(
        self,
        disease_id: str,
        size: int = 50,
        min_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get overview of all targets associated with a disease.
        
        Args:
            disease_id: Disease EFO ID (e.g., "EFO_0000508")
            size: Number of targets to return (default: 50)
            min_score: Minimum association score threshold (0-1, optional)
            
        Returns:
            Dictionary containing disease targets summary with top targets
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> summary = client.get_disease_targets_summary("EFO_0000508", size=20)
            >>> print(summary['topTargets'])
        """
        response = self.get_disease_associations(disease_id, size=size, min_score=min_score)
        
        disease_data = response.get('data', {}).get('disease', {})
        associations = disease_data.get('associatedTargets', {})
        
        # Create a summary with top targets
        summary = {
            'diseaseId': disease_id,
            'diseaseName': disease_data.get('name'),
            'totalTargets': associations.get('count', 0),
            'topTargets': [
                {
                    'targetId': assoc['target']['id'],
                    'targetSymbol': assoc['target']['approvedSymbol'],
                    'targetName': assoc['target']['approvedName'],
                    'associationScore': assoc['score'],
                    'datatypeScores': assoc.get('datatypeScores', [])
                }
                for assoc in associations.get('rows', [])[:10]
            ],
            'fullResults': response
        }
        
        return summary
    
    def get_target_disease_evidence(
        self,
        target_id: str,
        disease_id: str,
        size: int = 10
    ) -> Dict[str, Any]:
        """Get evidence linking a specific target to a specific disease.
        
        Args:
            target_id: Target Ensembl gene ID (e.g., "ENSG00000139618")
            disease_id: Disease EFO ID (e.g., "EFO_0000508")
            size: Number of evidence items to return (default: 10)
            
        Returns:
            Dictionary containing evidence linking target and disease
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> evidence = client.get_target_disease_evidence(
            ...     "ENSG00000139618",
            ...     "EFO_0000508",
            ...     size=5
            ... )
            >>> print(evidence['data']['disease']['evidences'])
        """
        graphql_query = """
        query GetTargetDiseaseEvidence($ensemblId: String!, $efoId: String!, $page: Pagination) {
          disease(efoId: $efoId) {
            id
            name
            evidences(ensemblIds: [$ensemblId], page: $page) {
              count
              rows {
                target {
                  id
                  approvedSymbol
                }
                disease {
                  id
                  name
                }
                score
                datasourceId
                datatypeId
              }
            }
          }
        }
        """
        
        return self._make_graphql_request(
            graphql_query,
            variables={
                'ensemblId': target_id,
                'efoId': disease_id,
                'page': {'size': size, 'index': 0}
            }
        )
    
    # Drug Methods
    
    def search_drugs(
        self,
        query: str,
        size: int = 25
    ) -> Dict[str, Any]:
        """Search for drugs by name or ChEMBL ID.
        
        Args:
            query: Search query (drug name or ChEMBL ID)
            size: Number of results to return (1-500, default: 25)
            
        Returns:
            Dictionary containing search results with drug information
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> results = client.search_drugs("aspirin", size=10)
            >>> print(results['data']['search']['hits'])
        """
        graphql_query = """
        query SearchDrugs($queryString: String!) {
          search(queryString: $queryString, entityNames: ["drug"]) {
            hits {
              id
              name
              description
              entity
            }
          }
        }
        """
        
        response = self._make_graphql_request(
            graphql_query,
            variables={'queryString': query}
        )
        
        # Limit results on client side
        hits = response.get('data', {}).get('search', {}).get('hits', [])
        limited_hits = hits[:size]
        
        return {
            'data': {
                'search': {
                    'hits': limited_hits,
                    'total': len(hits)
                }
            }
        }
    
    def get_drug_details(self, drug_id: str) -> Dict[str, Any]:
        """Get comprehensive drug information.
        
        Args:
            drug_id: Drug ChEMBL ID (e.g., "CHEMBL1234")
            
        Returns:
            Dictionary containing detailed drug information
            
        Examples:
            >>> client = OpenTargetsClient()
            >>> details = client.get_drug_details("CHEMBL1234")
            >>> print(details['data']['drug'])
        """
        graphql_query = """
        query GetDrug($chemblId: String!) {
          drug(chemblId: $chemblId) {
            id
            name
            description
            synonyms
            drugType
            maximumClinicalTrialPhase
            hasBeenWithdrawn
            linkedDiseases {
              count
            }
            linkedTargets {
              count
            }
          }
        }
        """
        
        return self._make_graphql_request(
            graphql_query,
            variables={'chemblId': drug_id}
        )

