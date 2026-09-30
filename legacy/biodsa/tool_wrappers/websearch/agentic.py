from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
from typing import Tuple, List

def _parse_web_search_response(content):
    """
    Parse Claude API response content to extract search results and formatted citations.
    
    Returns:
        tuple: (search_results, formatted_response)
            - search_results: List of strings in format "page_age, title, url"
            - formatted_response: String with inline citations and references section
    """
    search_results = []
    text_parts = []
    citations_map = {}  # Map (URL, cited_text) to citation number
    citation_counter = 1
    all_citations = []  # List of (citation_num, url, title, cited_text)
    
    # Parse through content
    for item in content:
        # Extract web search results
        if isinstance(item, dict) and item.get("type") == "web_search_tool_result":
            tool_content = item.get("content", [])
            for result in tool_content:
                if isinstance(result, dict) and result.get("type") == "web_search_result":
                    page_age = result.get("page_age", "Unknown date")
                    title = result.get("title", "No title")
                    url = result.get("url", "No URL")
                    search_results.append(f"{page_age}, {title}, {url}")
        
        # Extract text and citations
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text", "")
            citations = item.get("citations", [])
            
            if citations:
                # Process citations for this text segment
                citation_refs = []
                for citation in citations:
                    url = citation.get("url", "")
                    title = citation.get("title", "No title")
                    cited_text = citation.get("cited_text", "No excerpt available")
                    
                    # Get or create citation number for this (URL, cited_text) pair
                    # Even same URL gets different citation numbers if cited text differs
                    citation_key = (url, cited_text)
                    if citation_key not in citations_map:
                        citations_map[citation_key] = citation_counter
                        all_citations.append((citation_counter, url, title, cited_text))
                        citation_counter += 1
                    
                    citation_refs.append(citations_map[citation_key])
                
                # Add text with citation markers
                if citation_refs:
                    citation_markers = ", ".join([f"[{num}]" for num in citation_refs])
                    text_parts.append(f"{text} {citation_markers}")
                else:
                    text_parts.append(text)
            else:
                text_parts.append(text)
    
    # Build formatted response
    formatted_text = "".join(text_parts)
    
    # Add references section if there are citations
    if all_citations:
        formatted_text += "\n\nReferences\n"
        for citation_num, url, title, cited_text in all_citations:
            formatted_text += f"[{citation_num}] {url}\n    {title}\n    \"{cited_text}\"\n\n"
    
    return search_results, formatted_text


def web_search(
    query: str,
    model_name: str = "claude-haiku-4-5-20251001",
    api_key: str = None,
    max_search_uses: int = 3,
) -> Tuple[List[str], str]:
    """
    Perform a web search using Claude with web search capabilities.
    
    Args:
        query: The search query/question to ask Claude
        model_name: Claude model to use (default: claude-haiku-4-5-20251001)
        api_key: Anthropic API key (if None, will load from environment)
        max_search_uses: Maximum number of web searches allowed (default: 3)
    
    Returns:
        tuple: (search_results, formatted_response)
            - search_results: List of strings in format "page_age, title, url"
            - formatted_response: String with inline citations and references section
    
    Example:
        >>> search_results, response = web_search("What is TypeScript 5.5?")
        >>> print(response)
        TypeScript 5.5 introduces new features... [1]
        
        References
        [1] https://example.com
            TypeScript Release Notes
            "TypeScript 5.5 was released..."
    """
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    
    # Use provided API key or get from environment
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Initialize model
    model = ChatAnthropic(
        model=model_name,
        api_key=api_key,
        # betas=["web-fetch-2025-09-10"],
    )
    
    # Configure tools
    tools = [
        {"type": "web_search_20250305", "name": "web_search", "max_uses": max_search_uses},
    ]
    model_with_tools = model.bind_tools(tools)
    
    # Invoke the model
    query = f"""
# Task
You are a helpful assistant that do web search and return the answer to the user's question.

# User's question
{query}
"""
    response = model_with_tools.invoke(query)
    content = response.content
    
    # Parse and return results
    return _parse_web_search_response(content)


if __name__ == "__main__":
    # Example usage
    query = "How do I update a web app to TypeScript 5.5? Make sure do web search and return me results."
    search_results, formatted_response = web_search(query)
    
    print("=" * 80)
    print("SEARCH RESULTS:")
    print("=" * 80)
    for i, result in enumerate(search_results, 1):
        print(f"{i}. {result}")
    
    print("\n" + "=" * 80)
    print("FORMATTED RESPONSE WITH CITATIONS:")
    print("=" * 80)
    print(formatted_response)