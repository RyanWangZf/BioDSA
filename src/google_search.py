from langchain_google_community import VertexAISearchRetriever
import os

def query_google_search(
    query: str,
    top_k: int = 10,
    ):
    """A function to query the Google search engine stored in Google Vertex AI.
    """
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
    LOCATION_ID = "global"  # Set to your data store location
    DATA_STORE_ID = os.environ.get("GOOGLE_DATA_STORE_ID")
    retriever = VertexAISearchRetriever(
        project_id=PROJECT_ID,
        location_id=LOCATION_ID,
        data_store_id=DATA_STORE_ID,
        max_documents=top_k,
        engine_data_type=2,
        query_expansion_condition=2, # enable query expansion by the API
    )
    result = retriever.invoke(input=query)
    return result