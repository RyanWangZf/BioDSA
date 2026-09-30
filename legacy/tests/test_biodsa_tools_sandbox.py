"""
Test script to verify biodsa.tools can be used in the sandbox.

This script:
1. Creates a sandbox container
2. Installs biodsa.tools module
3. Executes a test script that uses biodsa.tools functions
4. Verifies the import and execution work correctly
"""

import os
import sys
import logging
import tempfile
import tarfile

# Add the BioDSA package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def install_biodsa_tools(sandbox: ExecutionSandboxWrapper):
    """Install biodsa.tools module in the sandbox."""
    logging.info("Installing biodsa.tools module in sandbox...")
    
    # Get the biodsa package directory
    current_file = os.path.abspath(__file__)
    repo_root = os.path.dirname(current_file)
    biodsa_package_dir = os.path.join(repo_root, "biodsa")
    tools_dir = os.path.join(biodsa_package_dir, "tools")
    
    if not os.path.exists(tools_dir):
        raise FileNotFoundError(f"biodsa/tools directory not found at {tools_dir}")
    
    # Create a tar.gz with minimal structure: biodsa/__init__.py and biodsa/tools/
    with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_tar:
        tar_path = tmp_tar.name
        
    try:
        with tarfile.open(tar_path, 'w:gz') as tar:
            # Add biodsa/__init__.py
            biodsa_init_path = os.path.join(biodsa_package_dir, "__init__.py")
            if os.path.exists(biodsa_init_path):
                tar.add(biodsa_init_path, arcname='biodsa/__init__.py')
            else:
                # Create empty __init__.py in memory
                init_info = tarfile.TarInfo(name='biodsa/__init__.py')
                init_info.size = 0
                tar.addfile(init_info, fileobj=None)
            
            # Add the entire biodsa/tools directory
            tar.add(tools_dir, arcname='biodsa/tools')
        
        # Upload tar to sandbox
        sandbox.upload_file(
            local_file_path=tar_path,
            target_file_path=f"{sandbox.workdir}/biodsa_tools.tar.gz"
        )
        logging.info("Uploaded biodsa.tools module to sandbox")
        
    finally:
        # Clean up temp file
        if os.path.exists(tar_path):
            os.unlink(tar_path)
    
    # Extract the tools
    extract_cmd = "tar -xzf biodsa_tools.tar.gz"
    exit_code, output = sandbox.container.exec_run(extract_cmd, workdir=sandbox.workdir)
    
    if exit_code != 0:
        raise Exception(f"Failed to extract biodsa.tools: {output.decode('utf-8')}")
    
    logging.info("Successfully extracted biodsa.tools module")
    
    # Add workdir to Python path using .pth file
    # Get site-packages path
    exit_code, output = sandbox.container.exec_run(
        'python -c "import site; print(site.getsitepackages()[0])"',
        workdir=sandbox.workdir
    )
    
    if exit_code != 0:
        raise Exception(f"Failed to find site-packages: {output.decode('utf-8')}")
    
    site_packages = output.decode('utf-8').strip()
    
    # Create .pth file to add workdir to sys.path
    pth_file_path = f"{site_packages}/biodsa_tools.pth"
    create_pth_cmd = f'echo "{sandbox.workdir}" > {pth_file_path}'
    
    exit_code, output = sandbox.container.exec_run(
        f'sh -c \'{create_pth_cmd}\'',
        workdir=sandbox.workdir
    )
    
    if exit_code != 0:
        raise Exception(f"Failed to create .pth file: {output.decode('utf-8')}")
    
    logging.info(f"Created .pth file at {pth_file_path}")
    logging.info(f"biodsa.tools module installed in sandbox at {sandbox.workdir}/biodsa")
    logging.info("You can now use 'from biodsa.tools import xxx' in your sandbox code")


def test_pubmed_search():
    """Test using biodsa.tools.pubmed in the sandbox."""
    
    test_code = """
import sys
print("Python version:", sys.version)
print("Python path:", sys.path)
print()

# Test 1: Import biodsa.tools.pubmed
print("=" * 60)
print("Test 1: Importing biodsa.tools.pubmed.pubtator_api")
print("=" * 60)

try:
    from biodsa.tools.pubmed.pubtator_api import pubtator_api_search_papers
    print("✓ Successfully imported pubtator_api_search_papers")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print()

# Test 2: Search for papers
print("=" * 60)
print("Test 2: Searching PubMed for papers about 'EGFR mutation'")
print("=" * 60)

try:
    papers = pubtator_api_search_papers(
        query="EGFR mutation",
        limit=3
    )
    
    print(f"✓ Found {len(papers)} papers")
    print()
    
    for i, paper in enumerate(papers, 1):
        print(f"Paper {i}:")
        print(f"  PMID: {paper.get('pmid', 'N/A')}")
        print(f"  Title: {paper.get('title', 'N/A')[:100]}...")
        print()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    
except Exception as e:
    print(f"✗ Search failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    return test_code


def test_biothings_genes():
    """Test using biodsa.tools.biothings.genes in the sandbox."""
    
    test_code = """
import sys
print("Python version:", sys.version)
print()

# Test: Import and use biodsa.tools.biothings.genes
print("=" * 60)
print("Test: Searching for genes using biodsa.tools.biothings.genes")
print("=" * 60)

try:
    from biodsa.tools.biothings.genes import search_genes
    print("✓ Successfully imported search_genes")
    print()
    
    # Search for BRCA1 gene
    results = search_genes(query="BRCA1", limit=3)
    
    print(f"✓ Found {len(results)} gene results for 'BRCA1'")
    print()
    
    for i, gene in enumerate(results, 1):
        print(f"Gene {i}:")
        print(f"  Symbol: {gene.get('symbol', 'N/A')}")
        print(f"  Name: {gene.get('name', 'N/A')}")
        print(f"  Entrez ID: {gene.get('entrezgene', 'N/A')}")
        print()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    return test_code


def main():
    """Main test function."""
    
    print("\n" + "=" * 70)
    print("BioDSA Tools Sandbox Test")
    print("=" * 70 + "\n")
    
    sandbox = None
    
    try:
        # Step 1: Create sandbox
        logging.info("Step 1: Creating sandbox container...")
        sandbox = ExecutionSandboxWrapper()
        logging.info(f"✓ Sandbox created with container ID: {sandbox.container_id}")
        print()
        
        # Step 2: Install biodsa.tools
        logging.info("Step 2: Installing biodsa.tools module...")
        install_biodsa_tools(sandbox)
        print()
        
        # Step 3: Test PubMed search
        logging.info("Step 3: Testing biodsa.tools.pubmed (PubMed search)...")
        print("-" * 70)
        test_code_pubmed = test_pubmed_search()
        exit_code, output, artifacts, runtime, memory = sandbox.execute("python", test_code_pubmed)
        
        print(output)
        
        if exit_code != 0:
            logging.error(f"✗ PubMed test failed with exit code {exit_code}")
            return False
        
        logging.info(f"✓ PubMed test passed (runtime: {runtime:.2f}s, memory: {memory:.2f}MB)")
        print()
        
        # Step 4: Test BioThings genes
        logging.info("Step 4: Testing biodsa.tools.biothings.genes...")
        print("-" * 70)
        test_code_genes = test_biothings_genes()
        exit_code, output, artifacts, runtime, memory = sandbox.execute("python", test_code_genes)
        
        print(output)
        
        if exit_code != 0:
            logging.error(f"✗ BioThings test failed with exit code {exit_code}")
            return False
        
        logging.info(f"✓ BioThings test passed (runtime: {runtime:.2f}s, memory: {memory:.2f}MB)")
        print()
        
        # Success!
        print("\n" + "=" * 70)
        print("🎉 All tests passed successfully!")
        print("=" * 70 + "\n")
        
        return True
        
    except Exception as e:
        logging.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if sandbox is not None:
            logging.info("Cleaning up sandbox...")
            try:
                sandbox.stop()
                logging.info("✓ Sandbox stopped and cleaned up")
            except Exception as e:
                logging.warning(f"Error during cleanup: {e}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

