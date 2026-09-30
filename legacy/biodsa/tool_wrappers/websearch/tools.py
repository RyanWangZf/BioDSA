"""
Web Search Tool
"""
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import os

from .agentic import web_search
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper

__all__ = [
    "WebSearchTool",
    "WebSearchToolInput",
]

# =====================================================
# Tool: Web Search with Claude
# =====================================================
class WebSearchToolInput(BaseModel):
    """Input schema for WebSearchTool."""
    query: str = Field(
        ...,
        description=(
"""
A clear and concise query to inform the target of the web search.

Example:
- "What are the latest treatments for diabetes?"
- "CRISPR gene editing applications 2024"
- "How does mRNA vaccine work?"
"""
        )
    )


class WebSearchTool(BaseTool):
    """
    Tool to perform web search using Claude with web search capabilities.
    
    This tool uses Claude's built-in web search functionality to find current information
    from the internet and return answers with proper citations. The tool automatically:
    - Performs web searches to find relevant information
    - Synthesizes information from multiple sources
    - Provides citations with URLs and quoted text excerpts
    - Returns both raw search results and a formatted response
    
    Use cases:
    - Find current information not available in training data
    - Get latest research, news, or developments
    - Verify facts with source citations
    - Answer questions requiring up-to-date information
    """
    name: str = "web_search"
    description: str = (
        "Pass a query to a web search sub-agent that will perform a web search to find current information from the internet. "
        "The sub-agent will return an answer to your question with proper citations including URLs and text excerpts. "
    )
    args_schema: Type[BaseModel] = WebSearchToolInput
    api_key: Optional[str] = None
    model_name: str = "claude-haiku-4-5-20251001"
    max_search_uses: int = 3
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-haiku-4-5-20251001",
        max_search_uses: int = 3,
        sandbox: ExecutionSandboxWrapper = None
    ):
        """
        Initialize the web search tool.
        
        Args:
            api_key: Anthropic API key (if None, will load from ANTHROPIC_API_KEY environment variable)
            model_name: Claude model to use (default: claude-haiku-4-5-20251001)
            max_search_uses: Maximum number of web searches allowed per query (default: 3)
            sandbox: Optional sandbox for code execution
        """
        super().__init__()
        # Try to get API key from environment if not provided
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. Either pass it as 'api_key' parameter "
                "or set it as 'ANTHROPIC_API_KEY' environment variable."
            )
        self.model_name = model_name
        self.max_search_uses = max_search_uses
        self.sandbox = sandbox
    
    def _run(self, query: str) -> str:
        """
        Execute the web search tool.
        
        Args:
            query: The search query or question
            
        Returns:
            Formatted string containing:
            - Raw search results (page_age, title, url)
            - Claude's synthesized response with inline citations
            - References section with full citation details
        """
        try:
            # Perform web search locally
            search_results, formatted_response = web_search(
                query=query,
                model_name=self.model_name,
                api_key=self.api_key,
                max_search_uses=self.max_search_uses,
            )
            
            # Format output
            output_parts = []
            output_parts.append("=" * 80)
            output_parts.append(f"Web Search Results for: '{query}'")
            output_parts.append("=" * 80)
            
            # Add raw search results if available
            if search_results:
                output_parts.append("\n📊 Raw Search Results:")
                output_parts.append("-" * 80)
                for idx, result in enumerate(search_results, 1):
                    output_parts.append(f"{idx}. {result}")
                output_parts.append("")
            
            # Add formatted response with citations
            output_parts.append("📝 Answer with Citations:")
            output_parts.append("-" * 80)
            output_parts.append(formatted_response)
            output_parts.append("=" * 80)
            
            return "\n".join(output_parts)
            
        except Exception as e:
            return f"Error executing web search: {str(e)}"


if __name__ == "__main__":
    # Example usage
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the tool
    web_search_tool = WebSearchTool(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model_name="claude-haiku-4-5-20251001",
        max_search_uses=3
    )
    
    # Example query
    query = "What are the latest developments in CRISPR gene editing for cancer treatment in 2024?"
    
    print("Testing WebSearchTool...")
    print(f"Query: {query}\n")
    
    # Run the tool
    result = web_search_tool._run(query)
    print(result)