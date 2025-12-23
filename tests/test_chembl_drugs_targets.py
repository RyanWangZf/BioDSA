"""
Test script for ChEMBL drug and target tools.

This script demonstrates the usage of the new drug and target tools
for the ChEMBL Database API.
"""

import sys
from biodsa.tools.chembl import (
    # Drug tools
    get_drug_indications,
    get_drug_mechanisms,
    get_drug_clinical_data,
    search_drugs_by_indication,
    # Target tools
    search_targets,
    get_target_details,
    search_by_uniprot,
    get_target_bioactivities,
    get_compounds_for_target,
)


def test_drug_tools():
    """Test drug-specific tools."""
    print("=" * 80)
    print("TESTING DRUG TOOLS")
    print("=" * 80)
    
    # Test 1: Get drug indications for aspirin
    print("\n1. Testing get_drug_indications() for aspirin (CHEMBL25)...")
    try:
        df, output = get_drug_indications(molecule_chembl_id="CHEMBL25", limit=5)
        print(output)
        print(f"Found {len(df)} indications")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Search by indication
    print("\n2. Testing get_drug_indications() by searching for 'pain'...")
    try:
        df, output = get_drug_indications(indication="pain", limit=5)
        print(output)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Get drug mechanisms for aspirin
    print("\n3. Testing get_drug_mechanisms() for aspirin...")
    try:
        df, output = get_drug_mechanisms(molecule_chembl_id="CHEMBL25")
        print(output)
        print(f"Found {len(df)} mechanisms")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Get comprehensive clinical data
    print("\n4. Testing get_drug_clinical_data() for aspirin...")
    try:
        data, output = get_drug_clinical_data("CHEMBL25")
        print(output)
        print(f"\nData keys: {list(data.keys())}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Search drugs by indication
    print("\n5. Testing search_drugs_by_indication() for 'cancer'...")
    try:
        df, output = search_drugs_by_indication("cancer", min_phase=3, limit=5)
        print(output)
    except Exception as e:
        print(f"Error: {e}")


def test_target_tools():
    """Test target-specific tools."""
    print("\n" + "=" * 80)
    print("TESTING TARGET TOOLS")
    print("=" * 80)
    
    # Test 1: Search for targets
    print("\n1. Testing search_targets() for 'kinase'...")
    try:
        df, output = search_targets("kinase", limit=5)
        print(output)
        
        # Save first target ID for later tests
        if not df.empty:
            target_id = df.iloc[0]['target_chembl_id']
            print(f"\nUsing target {target_id} for subsequent tests...")
            return target_id
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    return None


def test_target_details(target_id):
    """Test target details and bioactivity tools."""
    if not target_id:
        print("\nSkipping target detail tests (no target ID)")
        return
    
    # Test 2: Get target details
    print(f"\n2. Testing get_target_details() for {target_id}...")
    try:
        details, output = get_target_details(target_id)
        print(output)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Get bioactivities
    print(f"\n3. Testing get_target_bioactivities() for {target_id}...")
    try:
        df, output = get_target_bioactivities(
            target_id,
            activity_type="IC50",
            limit=10
        )
        print(output)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Get compounds for target
    print(f"\n4. Testing get_compounds_for_target() for {target_id}...")
    try:
        df, output = get_compounds_for_target(
            target_id,
            activity_threshold=1000,  # IC50 < 1000nM
            activity_type="IC50",
            limit=10
        )
        print(output)
    except Exception as e:
        print(f"Error: {e}")


def test_uniprot_search():
    """Test UniProt-based target search."""
    print("\n5. Testing search_by_uniprot() for EGFR (P00533)...")
    try:
        df, output = search_by_uniprot("P00533", limit=5)
        print(output)
    except Exception as e:
        print(f"Error: {e}")


def test_drug_discovery_workflow():
    """Test a complete drug discovery workflow."""
    print("\n" + "=" * 80)
    print("TESTING DRUG DISCOVERY WORKFLOW")
    print("=" * 80)
    
    print("\n1. Finding targets related to 'COX-2'...")
    try:
        # Search for COX-2 target
        targets_df, output = search_targets("COX-2", limit=1)
        print(f"Found {len(targets_df)} target(s)")
        
        if not targets_df.empty:
            target_id = targets_df.iloc[0]['target_chembl_id']
            target_name = targets_df.iloc[0]['pref_name']
            print(f"Target: {target_name} ({target_id})")
            
            # Get active compounds
            print(f"\n2. Finding active compounds for {target_name}...")
            compounds_df, output = get_compounds_for_target(
                target_id,
                activity_threshold=100,
                activity_type="IC50",
                limit=5
            )
            print(output)
            
            # Get drugs targeting this target
            print(f"\n3. Finding drugs that target {target_name}...")
            drugs_df, output = get_drug_mechanisms(target_chembl_id=target_id)
            print(output)
    
    except Exception as e:
        print(f"Error in workflow: {e}")


def main():
    """Run all tests."""
    print("ChEMBL Drug and Target Tools Test Suite")
    print("=" * 80)
    
    try:
        # Test drug tools
        test_drug_tools()
        
        # Test target tools
        target_id = test_target_tools()
        test_target_details(target_id)
        test_uniprot_search()
        
        # Test integrated workflow
        test_drug_discovery_workflow()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED")
        print("=" * 80)
    
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

