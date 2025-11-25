"""
PubChem API Client

This module provides a client for interacting with the PubChem REST API (PUG REST).
PubChem is a comprehensive database of chemical molecules and their activities.

API Documentation: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
"""

import requests
from typing import Dict, Any, Optional, List, Union
import time


class PubChemClient:
    """Client for the PubChem PUG REST API."""
    
    def __init__(self, base_url: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug", timeout: int = 30):
        """
        Initialize the PubChem API client.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-PubChem-Client/1.0.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request to the PubChem API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments
            
        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"PubChem API request failed: {str(e)}")
    
    # ===== Compound Search Methods =====
    
    def search_compounds(
        self,
        query: str,
        search_type: str = 'name',
        max_records: int = 100
    ) -> List[int]:
        """
        Search for compounds and return CIDs.
        
        Args:
            query: Search query
            search_type: Type of search (name, smiles, inchi, sdf, cid, formula)
            max_records: Maximum number of results
            
        Returns:
            List of PubChem CIDs
        """
        endpoint = f"/compound/{search_type}/{requests.utils.quote(query)}/cids/JSON"
        params = {'MaxRecords': max_records}
        
        response = self._make_request('GET', endpoint, params=params)
        data = response.json()
        
        if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
            return data['IdentifierList']['CID']
        return []
    
    def get_compound_info(self, cid: Union[int, str], output_format: str = 'json') -> Dict[str, Any]:
        """
        Get complete compound information by CID.
        
        Args:
            cid: PubChem Compound ID
            output_format: Output format (json, sdf, xml, etc.)
            
        Returns:
            Dictionary with compound information
        """
        format_suffix = 'JSON' if output_format.lower() == 'json' else output_format.upper()
        endpoint = f"/compound/cid/{cid}/{format_suffix}"
        
        response = self._make_request('GET', endpoint)
        
        if output_format.lower() == 'json':
            return response.json()
        else:
            return {'data': response.text}
    
    def get_compound_synonyms(self, cid: Union[int, str]) -> List[str]:
        """
        Get all names and synonyms for a compound.
        
        Args:
            cid: PubChem Compound ID
            
        Returns:
            List of synonyms
        """
        endpoint = f"/compound/cid/{cid}/synonyms/JSON"
        response = self._make_request('GET', endpoint)
        data = response.json()
        
        if 'InformationList' in data and 'Information' in data['InformationList']:
            info = data['InformationList']['Information'][0]
            return info.get('Synonym', [])
        return []
    
    def search_by_smiles(self, smiles: str) -> Optional[int]:
        """
        Search for a compound by SMILES string (exact match).
        
        Args:
            smiles: SMILES string
            
        Returns:
            PubChem CID if found, None otherwise
        """
        cids = self.search_compounds(smiles, search_type='smiles', max_records=1)
        return cids[0] if cids else None
    
    def search_by_inchi(self, inchi: str) -> Optional[int]:
        """
        Search for a compound by InChI string.
        
        Args:
            inchi: InChI string
            
        Returns:
            PubChem CID if found, None otherwise
        """
        cids = self.search_compounds(inchi, search_type='inchi', max_records=1)
        return cids[0] if cids else None
    
    def search_by_cas(self, cas_number: str) -> Optional[int]:
        """
        Search for a compound by CAS Registry Number.
        
        Args:
            cas_number: CAS number (e.g., "50-78-2")
            
        Returns:
            PubChem CID if found, None otherwise
        """
        cids = self.search_compounds(cas_number, search_type='name', max_records=1)
        return cids[0] if cids else None
    
    # ===== Structure Similarity Methods =====
    
    def search_similar_compounds(
        self,
        smiles: str,
        threshold: int = 90,
        max_records: int = 100
    ) -> List[int]:
        """
        Find chemically similar compounds using Tanimoto similarity.
        
        Args:
            smiles: SMILES string
            threshold: Similarity threshold (0-100)
            max_records: Maximum number of results
            
        Returns:
            List of similar compound CIDs
        """
        # Use fastsubstructure endpoint as similarity search endpoint may have changed
        # First, try to get the compound CID from SMILES
        try:
            cid = self.search_by_smiles(smiles)
            if cid:
                # Use the compound CID to find similar structures
                endpoint = f"/compound/similarity/cid/{cid}/cids/JSON"
                params = {
                    'Threshold': threshold,
                    'MaxRecords': max_records
                }
                response = self._make_request('GET', endpoint, params=params)
                result = response.json()
                
                if 'IdentifierList' in result and 'CID' in result['IdentifierList']:
                    return result['IdentifierList']['CID']
        except:
            pass
        
        return []
    
    def substructure_search(self, smiles: str, max_records: int = 100) -> List[int]:
        """
        Find compounds containing a specific substructure.
        
        Args:
            smiles: SMILES string of substructure
            max_records: Maximum number of results
            
        Returns:
            List of compound CIDs
        """
        endpoint = f"/compound/fastsubstructure/smiles/{requests.utils.quote(smiles)}/cids/JSON"
        params = {'MaxRecords': max_records}
        
        response = self._make_request('GET', endpoint, params=params)
        data = response.json()
        
        if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
            return data['IdentifierList']['CID']
        return []
    
    def superstructure_search(self, smiles: str, max_records: int = 100) -> List[int]:
        """
        Find larger compounds that contain the query structure.
        
        Args:
            smiles: SMILES string
            max_records: Maximum number of results
            
        Returns:
            List of compound CIDs
        """
        endpoint = f"/compound/fastsuperstructure/smiles/{requests.utils.quote(smiles)}/cids/JSON"
        params = {'MaxRecords': max_records}
        
        response = self._make_request('GET', endpoint, params=params)
        data = response.json()
        
        if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
            return data['IdentifierList']['CID']
        return []
    
    # ===== Property Methods =====
    
    def get_compound_properties(
        self,
        cid: Union[int, str],
        properties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get molecular properties for a compound.
        
        Args:
            cid: PubChem Compound ID
            properties: List of properties to retrieve
            
        Returns:
            Dictionary with properties
        """
        if properties is None:
            properties = [
                'MolecularWeight', 'XLogP', 'TPSA', 'HBondDonorCount',
                'HBondAcceptorCount', 'RotatableBondCount', 'Complexity',
                'HeavyAtomCount', 'Charge'
            ]
        
        prop_string = ','.join(properties)
        endpoint = f"/compound/cid/{cid}/property/{prop_string}/JSON"
        
        response = self._make_request('GET', endpoint)
        data = response.json()
        
        if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
            return data['PropertyTable']['Properties'][0]
        return {}
    
    def get_3d_conformers(self, cid: Union[int, str]) -> Dict[str, Any]:
        """
        Get 3D conformer data and structural information.
        
        Args:
            cid: PubChem Compound ID
            
        Returns:
            Dictionary with 3D conformer data
        """
        properties = ['Volume3D', 'ConformerCount3D']
        prop_string = ','.join(properties)
        endpoint = f"/compound/cid/{cid}/property/{prop_string}/JSON"
        
        response = self._make_request('GET', endpoint)
        data = response.json()
        
        if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
            return data['PropertyTable']['Properties'][0]
        return {}
    
    def analyze_stereochemistry(self, cid: Union[int, str]) -> Dict[str, Any]:
        """
        Analyze stereochemistry, chirality, and isomer information.
        
        Args:
            cid: PubChem Compound ID
            
        Returns:
            Dictionary with stereochemistry data
        """
        properties = [
            'AtomStereoCount', 'DefinedAtomStereoCount',
            'BondStereoCount', 'DefinedBondStereoCount',
            'IsomericSMILES'
        ]
        prop_string = ','.join(properties)
        endpoint = f"/compound/cid/{cid}/property/{prop_string}/JSON"
        
        response = self._make_request('GET', endpoint)
        data = response.json()
        
        if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
            return data['PropertyTable']['Properties'][0]
        return {}
    
    # ===== Bioassay Methods =====
    
    def get_assay_info(self, aid: int) -> Dict[str, Any]:
        """
        Get detailed information for a bioassay.
        
        Args:
            aid: PubChem Assay ID
            
        Returns:
            Dictionary with assay information
        """
        endpoint = f"/assay/aid/{aid}/JSON"
        response = self._make_request('GET', endpoint)
        return response.json()
    
    def get_compound_bioactivities(
        self,
        cid: Union[int, str],
        activity_outcome: str = 'all'
    ) -> List[int]:
        """
        Get all bioassay results for a compound.
        
        Args:
            cid: PubChem Compound ID
            activity_outcome: Filter by outcome (active, inactive, all)
            
        Returns:
            List of assay IDs
        """
        endpoint = f"/compound/cid/{cid}/aids/JSON"
        response = self._make_request('GET', endpoint)
        data = response.json()
        
        if 'InformationList' in data and 'Information' in data['InformationList']:
            info = data['InformationList']['Information'][0]
            return info.get('AID', [])
        return []
    
    # ===== Safety and Classification Methods =====
    
    def get_safety_data(self, cid: Union[int, str]) -> Dict[str, Any]:
        """
        Get GHS hazard classifications and safety information.
        
        Args:
            cid: PubChem Compound ID
            
        Returns:
            Dictionary with safety data
        """
        endpoint = f"/compound/cid/{cid}/classification/JSON"
        
        try:
            response = self._make_request('GET', endpoint)
            return response.json()
        except:
            return {'message': 'No classification data available'}
    
    # ===== Batch Operations =====
    
    def batch_compound_lookup(
        self,
        cids: List[int],
        operation: str = 'property'
    ) -> List[Dict[str, Any]]:
        """
        Process multiple compound IDs efficiently.
        
        Args:
            cids: List of PubChem CIDs (max 200)
            operation: Operation to perform (property, synonyms, etc.)
            
        Returns:
            List of results for each CID
        """
        if len(cids) > 200:
            raise ValueError("Maximum 200 CIDs allowed for batch lookup")
        
        results = []
        
        # Batch in groups of 10 for efficiency
        for i in range(0, min(len(cids), 50), 10):
            batch_cids = cids[i:i+10]
            cid_string = ','.join(str(cid) for cid in batch_cids)
            
            try:
                if operation == 'property':
                    endpoint = f"/compound/cid/{cid_string}/property/MolecularWeight,CanonicalSMILES,IUPACName/JSON"
                    response = self._make_request('GET', endpoint)
                    data = response.json()
                    
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        for prop in data['PropertyTable']['Properties']:
                            results.append({
                                'cid': prop.get('CID'),
                                'data': prop,
                                'success': True
                            })
                elif operation == 'synonyms':
                    for cid in batch_cids:
                        try:
                            synonyms = self.get_compound_synonyms(cid)
                            results.append({
                                'cid': cid,
                                'data': {'synonyms': synonyms},
                                'success': True
                            })
                        except Exception as e:
                            results.append({
                                'cid': cid,
                                'error': str(e),
                                'success': False
                            })
                
                # Small delay to be respectful
                time.sleep(0.2)
                
            except Exception as e:
                for cid in batch_cids:
                    results.append({
                        'cid': cid,
                        'error': str(e),
                        'success': False
                    })
        
        return results

