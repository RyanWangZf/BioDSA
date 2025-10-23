from typing import List, Dict
from datetime import datetime

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.sandbox.execution import ExecutionResults

class DeepEvidenceExecutionResults(ExecutionResults):
    """Execution results for the deep evidence agent."""
    def __init__(self,
        message_history: List[Dict[str, str]],
        code_execution_results: List[Dict[str, str]],
        final_response: str,
        sandbox: ExecutionSandboxWrapper = None,
        total_input_tokens: int = 0,
        total_output_tokens: int = 0
    ):
        super().__init__(message_history, code_execution_results, final_response, sandbox)
        self.total_input_tokens = total_input_tokens
        self.total_output_tokens = total_output_tokens

    def _build_query_section(self, story: list, context: dict):
        """
        Build the user query section. Override to customize query display.

        Args:
            story: List of reportlab flowables to append to
            context: Dictionary containing styles, artifact info, and other context
        """
        from reportlab.platypus import Spacer, Paragraph, Table, TableStyle

        styles = context['styles']
        colors = context['colors']
        inch = context['inch']

        # Metadata table
        metadata = [
            ['Report Generated:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ['Total Iterations:', str(len(self.message_history))],
            ['Code Executions:', str(len(self.code_execution_results))],
            ['Artifacts Generated:', str(len(context['artifact_files']))],
            ['Total Input Token Usage:', str(self.total_input_tokens)],
            ['Total Output Token Usage:', str(self.total_output_tokens)],
        ]

        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7F8C8D')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))

        # User query
        story.append(Paragraph("User Query", styles['heading']))
        story.append(Spacer(1, 0.1*inch))

        # Extract user query
        user_query = self._get_user_query()

        if user_query:
            for line in user_query.split('\n'):
                if line.strip():
                    story.append(Paragraph(self._escape_html(line), styles['body']))
        else:
            story.append(Paragraph("<i>No user query found</i>", styles['body']))

