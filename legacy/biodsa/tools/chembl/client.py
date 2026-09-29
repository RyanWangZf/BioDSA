"""Client for the ChEMBL Database API

This module provides a Python client for interacting with the ChEMBL Database API.
ChEMBL is a manually curated database of bioactive molecules with drug-like properties.
It brings together chemical, bioactivity and genomic data to aid the translation of 
genomic information into effective new drugs.

ChEMBL API Documentation: https://chembl.gitbook.io/chembl-interface-documentation/web-services
"""

import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


class ChEMBLClient:
    """Client for interacting with the ChEMBL Database API.
    
    This client provides methods for querying ChEMBL including compounds, targets,
    assays, bioactivities, and drug development information.
    """
    
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    
    def __init__(self, timeout: int = 30):
        """Initialize the ChEMBL client.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-ChEMBL-Client/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the ChEMBL API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters (optional)
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    # Compound Methods
    
    def search_compounds(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search ChEMBL database for compounds by name, synonym, or identifier.
        
        Args:
            query: Search query (compound name, synonym, or identifier)
            limit: Number of results to return (1-1000, default: 25)
            offset: Number of results to skip (default: 0)
            
        Returns:
            Dictionary containing search results
            
        Examples:
            >>> client = ChEMBLClient()
            >>> results = client.search_compounds("aspirin", limit=10)
            >>> print(results['molecules'])
        """
        return self._make_request(
            'molecule/search.json',
            params={'q': query, 'limit': limit, 'offset': offset}
        )
    
    def get_compound_by_id(self, chembl_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific compound by ChEMBL ID.
        
        Args:
            chembl_id: ChEMBL compound ID (e.g., "CHEMBL25")
            
        Returns:
            Dictionary containing compound information
            
        Examples:
            >>> client = ChEMBLClient()
            >>> compound = client.get_compound_by_id("CHEMBL25")
            >>> print(compound['molecule_chembl_id'])
        """
        return self._make_request(f'molecule/{chembl_id}.json')
    
    def search_by_inchi(
        self,
        inchi: str,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Search for compounds by InChI key or InChI string.
        
        Args:
            inchi: InChI key or InChI string
            limit: Number of results to return (default: 25)
            
        Returns:
            Dictionary containing search results
            
        Examples:
            >>> client = ChEMBLClient()
            >>> results = client.search_by_inchi("InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)")
        """
        return self._make_request(
            'molecule/search.json',
            params={'q': inchi, 'limit': limit}
        )
    
    def search_similar_compounds(
        self,
        smiles: str,
        similarity: int = 70,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Find chemically similar compounds using Tanimoto similarity.
        
        Args:
            smiles: SMILES string of the query molecule
            similarity: Similarity threshold percentage (0-100, default: 70)
            limit: Number of results to return (default: 25)
            
        Returns:
            Dictionary containing similar compounds
            
        Examples:
            >>> client = ChEMBLClient()
            >>> results = client.search_similar_compounds("CC(=O)Oc1ccccc1C(=O)O", similarity=70)
        """
        encoded_smiles = quote(smiles, safe='')
        return self._make_request(
            f'similarity/{encoded_smiles}/{similarity}.json',
            params={'limit': limit}
        )
    
    def search_substructure(
        self,
        smiles: str,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Find compounds containing specific substructures.
        
        Args:
            smiles: SMILES string of the substructure query
            limit: Number of results to return (default: 25)
            
        Returns:
            Dictionary containing compounds with the substructure
            
        Examples:
            >>> client = ChEMBLClient()
            >>> results = client.search_substructure("c1ccccc1", limit=10)
        """
        encoded_smiles = quote(smiles, safe='')
        return self._make_request(
            f'substructure/{encoded_smiles}.json',
            params={'limit': limit}
        )
    
    # Target Methods
    
    def search_targets(
        self,
        query: str,
        target_type: Optional[str] = None,
        organism: Optional[str] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Search for biological targets by name or type.
        
        Args:
            query: Target name or search query
            target_type: Target type filter (e.g., "SINGLE PROTEIN", "PROTEIN COMPLEX")
            organism: Organism filter
            limit: Number of results to return (default: 25)
            
        Returns:
            Dictionary containing target search results
            
        Examples:
            >>> client = ChEMBLClient()
            >>> results = client.search_targets("kinase", limit=10)
        """
        params = {'q': query, 'limit': limit}
        if target_type:
            params['target_type'] = target_type
        if organism:
            params['organism'] = organism
        
        return self._make_request('target/search.json', params=params)
    
    def get_target_by_id(self, chembl_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific target by ChEMBL target ID.
        
        Args:
            chembl_id: ChEMBL target ID (e.g., "CHEMBL2095173")
            
        Returns:
            Dictionary containing target information
            
        Examples:
            >>> client = ChEMBLClient()
            >>> target = client.get_target_by_id("CHEMBL2095173")
        """
        return self._make_request(f'target/{chembl_id}.json')
    
    def search_by_uniprot(
        self,
        uniprot_id: str,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Find ChEMBL targets by UniProt accession.
        
        Args:
            uniprot_id: UniProt accession number
            limit: Number of results to return (default: 25)
            
        Returns:
            Dictionary containing target results
            
        Examples:
            >>> client = ChEMBLClient()
            >>> results = client.search_by_uniprot("P00533")
        """
        return self._make_request(
            'target/search.json',
            params={'q': uniprot_id, 'limit': limit}
        )
    
    # Activity Methods
    
    def search_activities(
        self,
        target_chembl_id: Optional[str] = None,
        molecule_chembl_id: Optional[str] = None,
        assay_chembl_id: Optional[str] = None,
        activity_type: Optional[str] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Search bioactivity measurements and assay results.
        
        Args:
            target_chembl_id: ChEMBL target ID filter
            molecule_chembl_id: ChEMBL compound ID filter
            assay_chembl_id: ChEMBL assay ID filter
            activity_type: Activity type (e.g., "IC50", "Ki", "EC50")
            limit: Number of results to return (default: 25)
            
        Returns:
            Dictionary containing activity data
            
        Examples:
            >>> client = ChEMBLClient()
            >>> activities = client.search_activities(
            ...     target_chembl_id="CHEMBL2095173",
            ...     activity_type="IC50"
            ... )
        """
        params = {'limit': limit}
        if target_chembl_id:
            params['target_chembl_id'] = target_chembl_id
        if molecule_chembl_id:
            params['molecule_chembl_id'] = molecule_chembl_id
        if assay_chembl_id:
            params['assay_chembl_id'] = assay_chembl_id
        if activity_type:
            params['standard_type'] = activity_type
        
        return self._make_request('activity.json', params=params)
    
    def get_assay_by_id(self, chembl_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific assay by ChEMBL assay ID.
        
        Args:
            chembl_id: ChEMBL assay ID (e.g., "CHEMBL1217643")
            
        Returns:
            Dictionary containing assay information
            
        Examples:
            >>> client = ChEMBLClient()
            >>> assay = client.get_assay_by_id("CHEMBL1217643")
        """
        return self._make_request(f'assay/{chembl_id}.json')
    
    # Drug Methods
    
    def get_drug_indications(
        self,
        molecule_chembl_id: Optional[str] = None,
        indication: Optional[str] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Search for therapeutic indications and disease areas.
        
        Args:
            molecule_chembl_id: ChEMBL compound ID filter
            indication: Disease or indication search term
            limit: Number of results to return (default: 25)
            
        Returns:
            Dictionary containing drug indication data
            
        Examples:
            >>> client = ChEMBLClient()
            >>> indications = client.get_drug_indications(indication="cancer")
        """
        params = {'limit': limit}
        if molecule_chembl_id:
            params['molecule_chembl_id'] = molecule_chembl_id
        if indication:
            params['q'] = indication
        
        return self._make_request('drug_indication.json', params=params)
    
    def get_mechanisms(
        self,
        molecule_chembl_id: Optional[str] = None,
        target_chembl_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get mechanism of action and target interaction data.
        
        Args:
            molecule_chembl_id: ChEMBL compound ID filter
            target_chembl_id: ChEMBL target ID filter
            limit: Number of results to return (default: 50)
            
        Returns:
            Dictionary containing mechanism data
            
        Examples:
            >>> client = ChEMBLClient()
            >>> mechanisms = client.get_mechanisms(molecule_chembl_id="CHEMBL25")
        """
        params = {'limit': limit}
        if molecule_chembl_id:
            params['molecule_chembl_id'] = molecule_chembl_id
        if target_chembl_id:
            params['target_chembl_id'] = target_chembl_id
        
        return self._make_request('mechanism.json', params=params)
    
    # Batch Operations
    
    def batch_compound_lookup(
        self,
        chembl_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Process multiple ChEMBL IDs efficiently.
        
        Args:
            chembl_ids: List of ChEMBL compound IDs (1-50)
            
        Returns:
            List of compound information dictionaries
            
        Examples:
            >>> client = ChEMBLClient()
            >>> compounds = client.batch_compound_lookup(["CHEMBL25", "CHEMBL59"])
        """
        results = []
        for chembl_id in chembl_ids[:50]:  # Limit to 50
            try:
                result = self.get_compound_by_id(chembl_id)
                results.append({
                    'chembl_id': chembl_id,
                    'data': result,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'chembl_id': chembl_id,
                    'error': str(e),
                    'success': False
                })
        return results
    
    # Advanced Search
    
    def advanced_compound_search(
        self,
        min_mw: Optional[float] = None,
        max_mw: Optional[float] = None,
        min_logp: Optional[float] = None,
        max_logp: Optional[float] = None,
        max_hbd: Optional[int] = None,
        max_hba: Optional[int] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """Complex queries with multiple chemical and biological filters.
        
        Args:
            min_mw: Minimum molecular weight (Da)
            max_mw: Maximum molecular weight (Da)
            min_logp: Minimum LogP value
            max_logp: Maximum LogP value
            max_hbd: Maximum hydrogen bond donors
            max_hba: Maximum hydrogen bond acceptors
            limit: Number of results to return (default: 25)
            
        Returns:
            Dictionary containing filtered compounds
            
        Examples:
            >>> client = ChEMBLClient()
            >>> results = client.advanced_compound_search(
            ...     min_mw=200,
            ...     max_mw=500,
            ...     max_hbd=5
            ... )
        """
        filters = []
        if min_mw is not None:
            filters.append(f'molecule_properties__mw_freebase__gte={min_mw}')
        if max_mw is not None:
            filters.append(f'molecule_properties__mw_freebase__lte={max_mw}')
        if min_logp is not None:
            filters.append(f'molecule_properties__alogp__gte={min_logp}')
        if max_logp is not None:
            filters.append(f'molecule_properties__alogp__lte={max_logp}')
        if max_hbd is not None:
            filters.append(f'molecule_properties__hbd__lte={max_hbd}')
        if max_hba is not None:
            filters.append(f'molecule_properties__hba__lte={max_hba}')
        
        filter_string = '&'.join(filters)
        endpoint = f'molecule.json?{filter_string}&limit={limit}'
        
        return self._make_request(endpoint)

