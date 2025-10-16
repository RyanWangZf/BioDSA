"""
Provide execution results from the agent and provide the way to download the artifacts from the sandbox.
"""

from typing import List, Dict
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
import json

class ExecutionResults:
    def __init__(self, 
        message_history: List[Dict[str, str]], 
        code_execution_results: List[Dict[str, str]], 
        final_response: str,
        sandbox: ExecutionSandboxWrapper = None
    ):
        self.sandbox = sandbox
        self.message_history = message_history
        self.code_execution_results = code_execution_results
        self.final_response = final_response

    def __str__(self):
        """Pretty print the execution results with better formatting"""
        lines = []
        lines.append("=" * 80)
        lines.append("EXECUTION RESULTS")
        lines.append("=" * 80)
        
        # Message History Section
        lines.append(f"\n📝 Message History ({len(self.message_history)} messages):")
        lines.append("-" * 80)
        for i, msg in enumerate(self.message_history, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            # Truncate long content
            content_preview = content[:200] + "..." if len(content) > 200 else content
            lines.append(f"  [{i}] {role.upper()}:")
            lines.append(f"      {content_preview}")
            if i < len(self.message_history):
                lines.append("")
        
        # Code Execution Results Section
        lines.append("\n" + "-" * 80)
        lines.append(f"⚙️  Code Execution Results ({len(self.code_execution_results)} executions):")
        lines.append("-" * 80)
        for i, result in enumerate(self.code_execution_results, 1):
            lines.append(f"  Execution #{i}:")
            for key, value in result.items():
                if isinstance(value, str):
                    value_preview = value[:150] + "..." if len(value) > 150 else value
                    lines.append(f"    {key}: {value_preview}")
                else:
                    lines.append(f"    {key}: {value}")
            if i < len(self.code_execution_results):
                lines.append("")
        
        # Final Response Section
        lines.append("\n" + "-" * 80)
        lines.append("✅ Final Response:")
        lines.append("-" * 80)
        # Format final response with indentation
        response_lines = self.final_response.split('\n')
        for line in response_lines:
            lines.append(f"  {line}")
        
        lines.append("\n" + "=" * 80)
        
        return '\n'.join(lines)
    
    def __repr__(self):
        """Concise representation for debugging"""
        return f"ExecutionResults(messages={len(self.message_history)}, executions={len(self.code_execution_results)}, has_sandbox={self.sandbox is not None})"

    def to_json(self, output_path: str) -> str:
        """
        Convert the execution results to a JSON file
        
        Args:
            output_path: Local path where the JSON file should be saved
        """
        with open(output_path, 'w') as f:
            json.dump({
                'message_history': self.message_history,
                'code_execution_results': self.code_execution_results,
                'final_response': self.final_response
            }, f)

    def download_artifacts(self, output_dir: str) -> List[str]:
        """
        Download the artifacts from the sandbox to local machine
        
        Args:
            output_dir: Local directory path where artifacts should be downloaded

        Returns:
            List[str]: List of downloaded file names
        """
        return self.sandbox.download_artifacts(output_dir=output_dir)

    def to_pdf(self, output_path: str):
        """
        Convert the execution results to a PDF file
        
        Args:
            output_path: Local path where the PDF file should be saved
        """
        pass
