"""provide embedding function
"""
import os
import pdb
import shutil
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings

def get_embedding_function(model=None):
    if model is None:
        model = "openai-small"
    if model in ["openai", "openai-small"]:
        azure_deployment = "text-embedding-small"
        embeddings =  AzureOpenAIEmbeddings(azure_deployment=azure_deployment)
    elif model == "openai-large":
        azure_deployment = "text-embedding-large"
        embeddings =  AzureOpenAIEmbeddings(azure_deployment=azure_deployment)
    else:
        return None
    return embeddings

def build_chromadb_index_from_docs(
    docs,
    persist_directory,
    embedding_model=None,
    ):
    """Input langchain documents and build a chromadb index from them.

    Args:
        docs (list): list of langchain documents
        persist_directory (str): directory to save the chromadb index
        embedding_model (str): embedding model to use, default to "openai-small"
            - "openai": use the OpenAI embeddings from azure: text-embedding-3
            - "openai-small": use the OpenAI embeddings from azure: text-embedding-3-small
            - "openai-large": use the OpenAI embeddings from azure: text-embedding-3-large
    """
    embedding_function = get_embedding_function(embedding_model)

    if os.path.exists(persist_directory):
        shutil.rmtree(persist_directory)
        os.makedirs(persist_directory)
    else:
        os.makedirs(persist_directory)

    # build chromadb from documents
    # langchain >= 0.2.0
    from langchain_community.vectorstores import Chroma
    db = Chroma.from_documents(
        docs, embedding_function, 
        persist_directory=persist_directory,
        ids = [doc.metadata["doc_id"] for doc in docs], # need to specify the ids for the documents when retrieving them
        )
    
    # load the chromadb from the disk
    db = Chroma(persist_directory=persist_directory, embedding_function=embedding_function)
    return db