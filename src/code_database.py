import pdb
import re
import glob
import json
import os
import shutil
import sys
sys.path.append(os.getcwd())

from .embeddings import build_chromadb_index_from_docs
from .embeddings import get_embedding_function

CODE_EMBEDDING_MODEL = "openai-small"

def load_code_snippet_index(persist_directory):
    """Load the code snippet index from the disk.

    Args:
        persist_directory (str): directory to save the code snippet index
    """
    # langchain < 0.2.0
    # from langchain.embeddings.openai import OpenAIEmbeddings
    # from langchain.vectorstores import Chroma
    # langchain >= 0.2.0
    from langchain_community.vectorstores import Chroma
    embedding_function = get_embedding_function(CODE_EMBEDDING_MODEL)
    db = Chroma(persist_directory=persist_directory, embedding_function=embedding_function)
    return db


def build_code_snippet_index(codebase_docs, persist_directory):
    """Build the code snippet index from the code database and save it to the disk.
    https://python.langchain.com/docs/integrations/vectorstores/chroma 

    Args:
        persist_directory (str): directory to save the code snippet index
    """
    from langchain.docstore.document import Document

    # load all the code snippets with their data story tags
    codedocs = []
    for filename in glob.glob(os.path.join(codebase_docs, "*.json")):
        codedoc = json.load(open(filename, "r"))
        snippets = codedoc["snippets"]
        for snippet in snippets:
            codedocs.append(
            Document(
                page_content=snippet["desc"], 
                metadata={
                    "doc_id": snippet["doc_id"],
                    "data_story": snippet["data_story"],
                    "code": snippet["code"],
                    "dependency": snippet.get("dependency", []),
                    "imported": snippet.get("imported", []),
                }
                ))

    # encode the documents with OpenAIembedder
    db = build_chromadb_index_from_docs(
        codedocs,
        persist_directory,
        embedding_model = CODE_EMBEDDING_MODEL
    )


def build_code_knowledge_bases_from_directory(input_dir, task):
    """Parse all the .py files under the input dir,
    build chunks of code snippets and save them to the disk.

    Example:
    >> task = "EDA"
    >> input_dir = "/home/ZF/OpenRWE_Experiments/DemoGeneExpression/basic_eda"
    >> build_code_knowledge_bases(input_dir, task)
    """
    from langchain_community.document_loaders.generic import GenericLoader
    from langchain_community.document_loaders.parsers import LanguageParser
    from langchain_text_splitters import Language
    src_input_dir = input_dir
    output_dir = os.path.join(input_dir, "chunks")
    if os.path.exists(output_dir):
        print(f"Warning: {output_dir} already exists. The existing files will be overwritten.")
        shutil.rmtree(output_dir)
        os.makedirs(output_dir)
    else:
        os.makedirs(output_dir)
    loader = GenericLoader.from_filesystem(
        src_input_dir,
        glob="**/*",
        suffixes=[".py"],
        parser=LanguageParser(language=Language.PYTHON, parser_threshold=100),
    )
    docs = loader.load()

    for i, doc in enumerate(docs):
        metadata = doc.metadata
        source = metadata["source"].split("/")[-1].split(".")[0]
        content = doc.page_content
        if metadata["content_type"] == "function_classes":
            name = f"{task}_{source}_{i}"
            # no need to chunk the content
            chunk_metadata = {
                "metadataAttributes": {
                    "doc_id": name,
                    "source": source,
                    "task": task,
                    "type": "function_classes",
                    }
                }
            with open(os.path.join(output_dir, name + ".txt"), "w") as f:
                f.write(content)
            with open(os.path.join(output_dir, name + ".txt.metadata.json"), "w") as f:
                f.write(json.dumps(chunk_metadata, indent=4))
        else:
            chunks = re.split(r'# In\[\d+\]:', content)
            for j, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                # save the chunk into a new document
                name = f"{task}_{source}_{i}_{j}"
                chunk_content = chunk.strip()
                chunk_metadata = {
                    "metadataAttributes": {
                        "doc_id": name,
                        "source": source,
                        "task": task,
                        "type": "code_snippet",
                        }
                    }
                with open(os.path.join(output_dir, name + ".txt"), "w") as f:
                    f.write(chunk_content)
                with open(os.path.join(output_dir, name + ".txt.metadata.json"), "w") as f:
                    f.write(json.dumps(chunk_metadata, indent=4))


def build_codebase_index_from_directory(
    input_dir,
    persist_directory,
    ):
    """Build the code snippet index from the codebase and save it to the disk.

    Args:
        input_dir (str): directory to the input codebase, where each code snippet is stored as name.txt, and
            the metadata is stored as name.txt.metadata.json
            The metadata's structure refers to the requirement of AWS Bedrock knowledge base.
            It's structure is
            ```
            {
                "metadataAttributes": {
                    "doc_id": "unique_id",
                     ... other metadata
                }
            }
            ```
        persist_directory (str): directory to save the code snippet index
    """
    from langchain.docstore.document import Document
    # load all the code snippets with their data story tags
    codedocs = []
    for filename in glob.glob(os.path.join(input_dir, "*.txt")):
        with open(filename, "r") as f:
            content = f.read()
        metadata_filename = filename + ".metadata.json"
        if not os.path.exists(metadata_filename):
            metadata = {}
        else:
            metadata = json.load(open(metadata_filename, "r"))
            metadata = metadata.get("metadataAttributes", {})
        codedocs.append(
            Document(
                page_content=content,
                metadata=metadata
            ))
    

    # encode the documents with OpenAIembedder
    db = build_chromadb_index_from_docs(
        codedocs,
        persist_directory,
        embedding_model = CODE_EMBEDDING_MODEL
    )
    return db

if __name__ == "__main__":
    # build the code snippet index
    # build_code_snippet_index(
    #     codebase_docs="/srv/local/data/TrialMindAPIs/PatientDataScience/codebase_docs",
    #     persist_directory="/srv/local/data/TrialMindAPIs/PatientDataScience/code_snippet_chromadb",
    # )
    pass
