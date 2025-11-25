"""Client for the KEGG REST API

This module provides a Python client for interacting with the KEGG REST API.
It implements comprehensive tools for pathway, gene, compound, disease, drug,
and other biological database queries.

KEGG REST API Documentation: https://www.kegg.jp/kegg/rest/keggapi.html
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

import requests


class KEGGClient:
    """Client for interacting with the KEGG REST API.
    
    This client provides methods for querying various KEGG databases including
    pathways, genes, compounds, reactions, enzymes, diseases, drugs, modules,
    orthology, glycans, and BRITE hierarchies.
    """
    
    BASE_URL = "https://rest.kegg.jp"
    
    def __init__(self, timeout: int = 30):
        """Initialize the KEGG client.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioDSA-KEGG-Client/1.0'
        })
    
    def _make_request(self, endpoint: str) -> str:
        """Make a request to the KEGG API.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Response text
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text
    
    def _parse_kegg_entry(self, text: str) -> Dict[str, Any]:
        """Parse a KEGG entry in flat file format.
        
        Args:
            text: KEGG entry text
            
        Returns:
            Parsed entry as a dictionary
        """
        entry = {}
        current_field = None
        current_value = []
        
        for line in text.split('\n'):
            if not line.strip():
                continue
                
            # Check if this is a new field (starts with non-whitespace)
            if line[0] != ' ':
                # Save previous field
                if current_field:
                    entry[current_field] = '\n'.join(current_value).strip()
                
                # Parse new field
                parts = line.split(None, 1)
                current_field = parts[0]
                current_value = [parts[1]] if len(parts) > 1 else []
            else:
                # Continuation of current field
                if current_field:
                    current_value.append(line.strip())
        
        # Save last field
        if current_field:
            entry[current_field] = '\n'.join(current_value).strip()
        
        return entry
    
    def _parse_kegg_list(self, text: str) -> List[Dict[str, str]]:
        """Parse KEGG list format (ID\\tDescription).
        
        Args:
            text: KEGG list text
            
        Returns:
            List of entries with 'id' and 'description' keys
        """
        results = []
        for line in text.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                results.append({
                    'id': parts[0].strip(),
                    'description': parts[1].strip()
                })
            else:
                results.append({
                    'id': parts[0].strip(),
                    'description': ''
                })
        return results
    
    def _parse_kegg_link(self, text: str) -> List[Dict[str, str]]:
        """Parse KEGG link format (ID1\\tID2).
        
        Args:
            text: KEGG link text
            
        Returns:
            List of link pairs
        """
        results = []
        for line in text.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) == 2:
                results.append({
                    'source': parts[0].strip(),
                    'target': parts[1].strip()
                })
        return results
    
    # Database Information & Statistics
    
    def get_database_info(self, database: str) -> Dict[str, Any]:
        """Get release information and statistics for any KEGG database.
        
        Args:
            database: Database name (kegg, pathway, brite, module, ko, genes,
                     genome, compound, glycan, reaction, rclass, enzyme, network,
                     variant, disease, drug, dgroup, or organism code)
        
        Returns:
            Database information including release and statistics
        """
        text = self._make_request(f"info/{database}")
        return {
            'database': database,
            'info': text.strip()
        }
    
    def list_organisms(self, limit: int = 100) -> List[Dict[str, str]]:
        """Get all KEGG organisms with codes and names.
        
        Args:
            limit: Maximum number of organisms to return (default: 100)
        
        Returns:
            List of organisms with codes and names
        """
        text = self._make_request("list/organism")
        organisms = self._parse_kegg_list(text)
        return organisms[:limit]
    
    # Pathway Analysis
    
    def search_pathways(
        self,
        query: str,
        organism_code: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search pathways by keywords or pathway names.
        
        Args:
            query: Search query (pathway name, keywords, or description)
            organism_code: Organism code to filter results (optional, e.g., hsa, mmu, eco)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching pathways
        """
        database = f"{organism_code}_pathway" if organism_code else "pathway"
        text = self._make_request(f"find/{database}/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_pathway_info(
        self,
        pathway_id: str,
        format: str = 'json'
    ) -> Union[Dict[str, Any], str]:
        """Get detailed information for a specific pathway.
        
        Args:
            pathway_id: Pathway ID (e.g., map00010, hsa00010, ko00010)
            format: Output format (json, kgml, image, conf - default: json)
        
        Returns:
            Pathway information in requested format
        """
        if format == 'json':
            text = self._make_request(f"get/{pathway_id}")
            return self._parse_kegg_entry(text)
        elif format == 'kgml':
            return self._make_request(f"get/{pathway_id}/kgml")
        elif format == 'image':
            return f"{self.BASE_URL}/get/{pathway_id}/image"
        elif format == 'conf':
            return self._make_request(f"get/{pathway_id}/conf")
        else:
            raise ValueError(f"Invalid format: {format}")
    
    def get_pathway_genes(self, pathway_id: str) -> List[Dict[str, str]]:
        """Get all genes involved in a specific pathway.
        
        Args:
            pathway_id: Pathway ID (e.g., hsa00010, mmu00010)
        
        Returns:
            List of genes in the pathway
        """
        # Extract organism code from pathway_id
        match = re.match(r'^([a-z]+)\d+$', pathway_id)
        if not match:
            raise ValueError(f"Invalid pathway ID format: {pathway_id}")
        
        org_code = match.group(1)
        text = self._make_request(f"link/{org_code}/{pathway_id}")
        return self._parse_kegg_link(text)
    
    # Gene Analysis
    
    def search_genes(
        self,
        query: str,
        organism_code: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search genes by name, symbol, or keywords.
        
        Args:
            query: Search query (gene name, symbol, or keywords)
            organism_code: Organism code to filter results (optional, e.g., hsa, mmu)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching genes
        """
        database = organism_code if organism_code else "genes"
        text = self._make_request(f"find/{database}/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_gene_info(
        self,
        gene_id: str,
        include_sequences: bool = False
    ) -> Dict[str, Any]:
        """Get detailed information for a specific gene.
        
        Args:
            gene_id: Gene ID (e.g., hsa:1956, mmu:11651, eco:b0008)
            include_sequences: Include amino acid and nucleotide sequences (default: False)
        
        Returns:
            Gene information including pathways and orthology
        """
        text = self._make_request(f"get/{gene_id}")
        gene_info = self._parse_kegg_entry(text)
        
        if include_sequences:
            try:
                aaseq = self._make_request(f"get/{gene_id}/aaseq")
                gene_info['amino_acid_sequence'] = aaseq.strip()
            except:
                pass
            
            try:
                ntseq = self._make_request(f"get/{gene_id}/ntseq")
                gene_info['nucleotide_sequence'] = ntseq.strip()
            except:
                pass
        
        return gene_info
    
    # Compound Analysis
    
    def search_compounds(
        self,
        query: str,
        search_type: str = 'name',
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search compounds by name, formula, or chemical structure.
        
        Args:
            query: Search query (compound name, formula, or identifier)
            search_type: Type of search (name, formula, exact_mass, mol_weight - default: name)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching compounds
        """
        if search_type == 'formula':
            text = self._make_request(f"find/compound/{quote(query)}/formula")
        elif search_type == 'exact_mass':
            text = self._make_request(f"find/compound/{quote(query)}/exact_mass")
        elif search_type == 'mol_weight':
            text = self._make_request(f"find/compound/{quote(query)}/mol_weight")
        else:
            text = self._make_request(f"find/compound/{quote(query)}")
        
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_compound_info(self, compound_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific compound.
        
        Args:
            compound_id: Compound ID (e.g., C00002, C00031, cpd:C00002)
        
        Returns:
            Compound information including structure and reactions
        """
        # Clean compound ID
        compound_id = compound_id.replace('cpd:', '')
        text = self._make_request(f"get/{compound_id}")
        return self._parse_kegg_entry(text)
    
    # Reaction & Enzyme Analysis
    
    def search_reactions(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search biochemical reactions by keywords or reaction components.
        
        Args:
            query: Search query (reaction name, enzyme, or compound)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching reactions
        """
        text = self._make_request(f"find/reaction/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_reaction_info(self, reaction_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific reaction.
        
        Args:
            reaction_id: Reaction ID (e.g., R00001, R00002)
        
        Returns:
            Reaction information including equation and enzymes
        """
        text = self._make_request(f"get/{reaction_id}")
        return self._parse_kegg_entry(text)
    
    def search_enzymes(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search enzymes by EC number or enzyme name.
        
        Args:
            query: Search query (EC number or enzyme name)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching enzymes
        """
        text = self._make_request(f"find/enzyme/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_enzyme_info(self, ec_number: str) -> Dict[str, Any]:
        """Get detailed enzyme information by EC number.
        
        Args:
            ec_number: EC number (e.g., ec:1.1.1.1 or 1.1.1.1)
        
        Returns:
            Enzyme information including reactions and pathways
        """
        # Clean EC number
        ec_number = ec_number.replace('ec:', '')
        text = self._make_request(f"get/ec:{ec_number}")
        return self._parse_kegg_entry(text)
    
    # Disease & Drug Analysis
    
    def search_diseases(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search human diseases by name or keywords.
        
        Args:
            query: Search query (disease name or keywords)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching diseases
        """
        text = self._make_request(f"find/disease/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_disease_info(self, disease_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific disease.
        
        Args:
            disease_id: Disease ID (e.g., H00001, H00002)
        
        Returns:
            Disease information including associated genes and pathways
        """
        text = self._make_request(f"get/{disease_id}")
        return self._parse_kegg_entry(text)
    
    def search_drugs(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search drugs by name, target, or indication.
        
        Args:
            query: Search query (drug name, target, or indication)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching drugs
        """
        text = self._make_request(f"find/drug/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_drug_info(self, drug_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific drug.
        
        Args:
            drug_id: Drug ID (e.g., D00001, D00002)
        
        Returns:
            Drug information including targets, pathways, metabolism, and interactions.
            Additional parsed fields:
            - target_gene_ids: List of HSA gene IDs (e.g., ['hsa:5142', 'hsa:7068'])
            - target_ko_ids: List of KO IDs (e.g., ['K13293', 'K08362'])
            - pathways: List of (pathway_id, pathway_name) tuples from TARGET section
            - metabolism: List of metabolism information text
            - metabolism_enzymes: List of dicts with enzyme, hsa_ids, ko_ids
            - disease: List of disease names (extracted from EFFICACY field if present)
            - disease_id: List of disease IDs in format 'ds:h01299' (extracted from EFFICACY field if present)
            - efficacy: List of efficacy information (cleaned, without embedded DISEASE text)
        """
        
        text = self._make_request(f"get/{drug_id}")
        parsed = self._parse_kegg_entry(text)
        
        # Add additional parsed fields
        parsed["target_gene_ids"] = []
        parsed["target_ko_ids"] = []
        parsed["pathways"] = []
        parsed["metabolism"] = []
        parsed["metabolism_enzymes"] = []
        parsed["disease"] = []
        parsed["disease_id"] = []
        parsed["efficacy"] = []
        
        # Parse TARGET section for HSA and KO IDs
        if "TARGET" in parsed:
            target_text = parsed["TARGET"]
            
            # Extract all HSA IDs (gene IDs) from [HSA:...] brackets
            hsa_bracket_matches = re.findall(r'\[HSA:([^\]]+)\]', target_text)
            for hsa_bracket in hsa_bracket_matches:
                hsa_ids = hsa_bracket.split()
                for hsa_id in hsa_ids:
                    parsed["target_gene_ids"].append(f"hsa:{hsa_id}")
            
            # Extract all KO IDs from [KO:...] brackets
            ko_bracket_matches = re.findall(r'\[KO:([^\]]+)\]', target_text)
            for ko_bracket in ko_bracket_matches:
                ko_ids = ko_bracket.split()
                parsed["target_ko_ids"].extend(ko_ids)
        
        # Parse PATHWAY section (found within TARGET field after "PATHWAY" keyword)
        if "TARGET" in parsed:
            target_text = parsed["TARGET"]
            # Split by "PATHWAY" keyword to extract pathway section
            if "PATHWAY" in target_text:
                pathway_section = target_text.split("PATHWAY", 1)[1]
                for line in pathway_section.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Match format: hsa00010  Glycolysis / Gluconeogenesis
                    # or: hsa04024(5142)  cAMP signaling pathway
                    pathway_match = re.match(r'(hsa\d+)(?:\([0-9+]+\))?\s+(.+?)$', line)
                    if pathway_match:
                        pathway_id = f"path:{pathway_match.group(1)}"
                        pathway_name = pathway_match.group(2).strip()
                        parsed["pathways"].append((pathway_id, pathway_name))
        
        # Parse METABOLISM section
        # Format: 'Enzyme: CYP3A [HSA:1576 1577 1551]; UGT [KO:K00699]'
        if "METABOLISM" in parsed:
            metabolism_text = parsed["METABOLISM"].strip()
            if metabolism_text:
                # Store full text
                parsed["metabolism"].append(metabolism_text)
                
                # Extract enzyme names and IDs
                # Split by semicolon or newline
                enzyme_parts = re.split(r'[;\n]', metabolism_text)
                for part in enzyme_parts:
                    part = part.strip()
                    if not part:
                        continue
                    
                    # Extract enzyme name (before brackets)
                    enzyme_name_match = re.match(r'^(?:Enzyme:\s*)?([A-Z0-9]+(?:[A-Z0-9/]+)?)', part)
                    if enzyme_name_match:
                        enzyme_name = enzyme_name_match.group(1).strip()
                        
                        # Extract HSA IDs
                        enzyme_hsa_ids = []
                        hsa_matches = re.findall(r'\[HSA:([^\]]+)\]', part)
                        for hsa_match in hsa_matches:
                            enzyme_hsa_ids.extend([f"hsa:{hid.strip()}" for hid in hsa_match.split()])
                        
                        # Extract KO IDs
                        enzyme_ko_ids = []
                        ko_matches = re.findall(r'\[KO:([^\]]+)\]', part)
                        for ko_match in ko_matches:
                            enzyme_ko_ids.extend([kid.strip() for kid in ko_match.split()])
                        
                        if enzyme_hsa_ids or enzyme_ko_ids:
                            parsed["metabolism_enzymes"].append({
                                "enzyme": enzyme_name,
                                "hsa_ids": enzyme_hsa_ids,
                                "ko_ids": enzyme_ko_ids
                            })
        

        # Parse EFFICACY section (may contain embedded DISEASE information)
        # Format: 'Antifibrotic, Anti-inflammatory, Phosphodiesterase IV inhibitor\nDISEASE   Idiopathic pulmonary fibrosis [DS:H01299]'
        if "EFFICACY" in parsed:
            efficacy_text = parsed["EFFICACY"].strip()
            if efficacy_text:
                # Check if DISEASE is embedded in EFFICACY field
                if "DISEASE" in efficacy_text:
                    # Split by DISEASE keyword
                    parts = efficacy_text.split("DISEASE", 1)
                    
                    # Store efficacy part (before DISEASE)
                    efficacy_part = parts[0].strip()
                    if efficacy_part:
                        parsed["efficacy"].append(efficacy_part)
                    
                    # Parse disease part (after DISEASE keyword)
                    if len(parts) > 1:
                        disease_part = parts[1].strip()
                        
                        # Extract disease names and IDs
                        # Format: "Idiopathic pulmonary fibrosis [DS:H01299]"
                        # Can have multiple diseases on separate lines
                        for line in disease_part.split('\n'):
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Match pattern: disease_name [DS:disease_id]
                            disease_match = re.match(r'(.+?)\s*\[DS:([^\]]+)\]', line)
                            if disease_match:
                                disease_name = disease_match.group(1).strip()
                                disease_id = disease_match.group(2).strip().lower()
                                
                                if disease_name:
                                    parsed["disease"].append(disease_name)
                                if disease_id:
                                    parsed["disease_id"].append(f"ds:{disease_id}")
                else:
                    # No DISEASE keyword, store entire text as efficacy
                    parsed["efficacy"].append(efficacy_text)
        
        return parsed

    
    def get_drug_interactions(self, drug_ids: List[str]) -> List[Dict[str, Any]]:
        """Find adverse drug-drug interactions.
        
        Args:
            drug_ids: Drug IDs to check for interactions (1-10)
        
        Returns:
            List of drug interactions
        """
        if len(drug_ids) < 1 or len(drug_ids) > 10:
            raise ValueError("drug_ids must contain 1-10 drug IDs")
        
        interactions = []
        for drug_id in drug_ids:
            try:
                text = self._make_request(f"link/drug/{drug_id}")
                links = self._parse_kegg_link(text)
                
                # Filter for drug-drug interactions
                for link in links:
                    if link['target'].startswith('dr:'):
                        interactions.append({
                            'drug1': drug_id,
                            'drug2': link['target'],
                            'type': 'interaction'
                        })
            except:
                continue
        
        return interactions
    
    # Module & Orthology Analysis
    
    def search_modules(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search KEGG modules by name or function.
        
        Args:
            query: Search query (module name or function)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching modules
        """
        text = self._make_request(f"find/module/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_module_info(self, module_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific module.
        
        Args:
            module_id: Module ID (e.g., M00001, M00002)
        
        Returns:
            Module information including definition and reactions
        """
        text = self._make_request(f"get/{module_id}")
        return self._parse_kegg_entry(text)
    
    def search_ko_entries(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search KEGG Orthology entries by function or gene name.
        
        Args:
            query: Search query (function or gene name)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching KO entries
        """
        text = self._make_request(f"find/ko/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_ko_info(self, ko_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific KO entry.
        
        Args:
            ko_id: KO ID (e.g., K00001, K00002)
        
        Returns:
            KO information including genes and pathways
        """
        text = self._make_request(f"get/{ko_id}")
        return self._parse_kegg_entry(text)
    
    # Glycan Analysis
    
    def search_glycans(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search glycan structures by name or composition.
        
        Args:
            query: Search query (glycan name or composition)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching glycans
        """
        text = self._make_request(f"find/glycan/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_glycan_info(self, glycan_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific glycan.
        
        Args:
            glycan_id: Glycan ID (e.g., G00001, G00002)
        
        Returns:
            Glycan information including structure and reactions
        """
        text = self._make_request(f"get/{glycan_id}")
        return self._parse_kegg_entry(text)
    
    # BRITE Hierarchy Analysis
    
    def search_brite(
        self,
        query: str,
        hierarchy_type: str = 'br',
        max_results: int = 50
    ) -> List[Dict[str, str]]:
        """Search BRITE functional hierarchies.
        
        Args:
            query: Search query (function or category)
            hierarchy_type: Type of BRITE hierarchy (br, ko, jp - default: br)
            max_results: Maximum number of results (1-1000, default: 50)
        
        Returns:
            List of matching BRITE entries
        """
        text = self._make_request(f"find/brite/{quote(query)}")
        results = self._parse_kegg_list(text)
        return results[:max_results]
    
    def get_brite_info(
        self,
        brite_id: str,
        format: str = 'json'
    ) -> Union[Dict[str, Any], str]:
        """Get detailed information for a specific BRITE entry.
        
        Args:
            brite_id: BRITE ID (e.g., br:br08301, ko:K00001)
            format: Output format (json, htext - default: json)
        
        Returns:
            BRITE information in requested format
        """
        if format == 'json':
            text = self._make_request(f"get/{brite_id}/json")
            import json
            return json.loads(text)
        elif format == 'htext':
            return self._make_request(f"get/{brite_id}")
        else:
            raise ValueError(f"Invalid format: {format}")
    
    # Advanced Analysis Tools
    
    def get_pathway_compounds(self, pathway_id: str) -> List[Dict[str, str]]:
        """Get all compounds involved in a specific pathway.
        
        Args:
            pathway_id: Pathway ID (e.g., map00010, hsa00010)
        
        Returns:
            List of compounds in the pathway
        """
        text = self._make_request(f"link/compound/{pathway_id}")
        return self._parse_kegg_link(text)
    
    def get_pathway_reactions(self, pathway_id: str) -> List[Dict[str, str]]:
        """Get all reactions involved in a specific pathway.
        
        Args:
            pathway_id: Pathway ID (e.g., map00010, rn00010)
        
        Returns:
            List of reactions in the pathway
        """
        text = self._make_request(f"link/reaction/{pathway_id}")
        return self._parse_kegg_link(text)
    
    def get_compound_reactions(self, compound_id: str) -> List[Dict[str, str]]:
        """Get all reactions involving a specific compound.
        
        Args:
            compound_id: Compound ID (e.g., C00002, C00031)
        
        Returns:
            List of reactions involving the compound
        """
        text = self._make_request(f"link/reaction/compound/{compound_id}")
        return self._parse_kegg_link(text)
    
    def get_gene_orthologs(
        self,
        gene_id: str,
        target_organisms: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Find orthologous genes across organisms.
        
        Args:
            gene_id: Gene ID (e.g., hsa:1956)
            target_organisms: Target organism codes (optional, e.g., ['mmu', 'rno', 'dme'])
        
        Returns:
            List of orthologous genes
        """
        # First get the KO (orthology) for this gene
        text = self._make_request(f"link/ko/{gene_id}")
        ko_links = self._parse_kegg_link(text)
        
        if not ko_links:
            return []
        
        # Get genes for each KO
        orthologs = []
        for ko_link in ko_links:
            ko_id = ko_link['target']
            
            if target_organisms:
                for org in target_organisms:
                    try:
                        text = self._make_request(f"link/{org}/{ko_id}")
                        genes = self._parse_kegg_link(text)
                        orthologs.extend(genes)
                    except:
                        continue
            else:
                try:
                    text = self._make_request(f"link/genes/{ko_id}")
                    genes = self._parse_kegg_link(text)
                    orthologs.extend(genes)
                except:
                    continue
        
        return orthologs
    
    def batch_entry_lookup(
        self,
        entry_ids: List[str],
        operation: str = 'info'
    ) -> List[Dict[str, Any]]:
        """Process multiple KEGG entries efficiently.
        
        Args:
            entry_ids: KEGG entry IDs (1-50)
            operation: Operation to perform (info, sequence, pathway, link - default: info)
        
        Returns:
            List of entry information
        """
        if len(entry_ids) < 1 or len(entry_ids) > 50:
            raise ValueError("entry_ids must contain 1-50 entries")
        
        results = []
        
        if operation == 'info':
            # Batch get request
            ids_str = '+'.join(entry_ids)
            text = self._make_request(f"get/{ids_str}")
            
            # Split by /// delimiter
            entries = text.split('///')
            for entry in entries:
                if entry.strip():
                    results.append(self._parse_kegg_entry(entry.strip()))
        
        elif operation == 'sequence':
            for entry_id in entry_ids:
                try:
                    seq = self._make_request(f"get/{entry_id}/aaseq")
                    results.append({
                        'id': entry_id,
                        'sequence': seq.strip()
                    })
                except:
                    results.append({
                        'id': entry_id,
                        'sequence': None,
                        'error': 'Failed to fetch sequence'
                    })
        
        elif operation in ['pathway', 'link']:
            for entry_id in entry_ids:
                try:
                    text = self._make_request(f"link/pathway/{entry_id}")
                    links = self._parse_kegg_link(text)
                    results.append({
                        'id': entry_id,
                        'links': links
                    })
                except:
                    results.append({
                        'id': entry_id,
                        'links': [],
                        'error': 'Failed to fetch links'
                    })
        
        return results
    
    # Cross-References & Integration
    
    def convert_identifiers(
        self,
        source_db: str,
        target_db: str,
        identifiers: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """Convert between KEGG and external database identifiers.
        
        Args:
            source_db: Source database (e.g., hsa, ncbi-geneid, uniprot)
            target_db: Target database (e.g., hsa, ncbi-geneid, uniprot)
            identifiers: Identifiers to convert (optional, for batch conversion)
        
        Returns:
            List of converted identifiers
        """
        if identifiers:
            results = []
            for identifier in identifiers:
                try:
                    text = self._make_request(f"conv/{target_db}/{source_db}:{identifier}")
                    links = self._parse_kegg_link(text)
                    results.extend(links)
                except:
                    continue
            return results
        else:
            text = self._make_request(f"conv/{target_db}/{source_db}")
            return self._parse_kegg_link(text)
    
    def find_related_entries(
        self,
        source_db: str,
        target_db: str,
        source_entries: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """Find related entries across KEGG databases using cross-references.
        
        Args:
            source_db: Source database (e.g., pathway, compound, gene)
            target_db: Target database (e.g., pathway, compound, gene)
            source_entries: Source entries to find links for (optional)
        
        Returns:
            List of related entries
        """
        if source_entries:
            results = []
            for entry in source_entries:
                try:
                    text = self._make_request(f"link/{target_db}/{entry}")
                    links = self._parse_kegg_link(text)
                    results.extend(links)
                except:
                    continue
            return results
        else:
            text = self._make_request(f"link/{target_db}/{source_db}")
            return self._parse_kegg_link(text)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()
