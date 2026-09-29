from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import os
import tempfile
import json
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.sandbox.execution import ExecutionResults
from biodsa.memory.memory_graph import visualize_graph
import warnings

class DeepEvidenceExecutionResults(ExecutionResults):
    """Execution results for the deep evidence agent."""
    def __init__(self,
        message_history: List[Dict[str, str]],
        code_execution_results: List[Dict[str, str]],
        final_response: str,
        sandbox: ExecutionSandboxWrapper = None,
        total_input_tokens: int = 0,
        total_output_tokens: int = 0,
        evidence_graph_data: Dict[str, Any] = {}
    ):
        super().__init__(message_history, code_execution_results, final_response, sandbox)
        self.total_input_tokens = total_input_tokens
        self.total_output_tokens = total_output_tokens
        self.evidence_graph_data = evidence_graph_data

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

    def to_json(self, output_path: str=None) -> str:
        """
        Convert the execution results to a JSON file
        
        Args:
            output_path: Local path where the JSON file should be saved
        """
        json_data = {
                    'total_input_tokens': self.total_input_tokens,
                    'total_output_tokens': self.total_output_tokens,
                    'evidence_graph_data': self.evidence_graph_data,
                    'message_history': self.message_history,
                    'code_execution_results': self.code_execution_results,
                    'final_response': self.final_response,
                }
        if output_path is not None:
            with open(output_path, 'w') as f:
                json.dump(json_data, f)
        return json_data


    def _render_evidence_graph(self, output_path: str, format: str = 'html') -> bool:
        """
        Render the evidence graph to an HTML interactive visualization or PDF.
        
        Args:
            output_path: Path where the graph should be saved
            format: Output format - 'html', 'pdf', or 'image' (legacy matplotlib)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.evidence_graph_data or not self.evidence_graph_data.get('entities'):
            return False
        
        # Use new D3.js interactive visualization for HTML/PDF
        if format in ['html', 'pdf']:
            try:
                from biodsa.agents.deepevidence.graph_visualization import (
                    generate_evidence_graph_html,
                    render_evidence_graph_to_pdf
                )
                
                # Generate HTML first
                html_path = output_path if format == 'html' else output_path.replace('.pdf', '.html')
                success = generate_evidence_graph_html(
                    evidence_graph_data=self.evidence_graph_data,
                    output_html_path=html_path,
                    title="Evidence Graph"
                )
                
                if not success:
                    return False
                
                # If PDF requested, convert HTML to PDF
                if format == 'pdf':
                    return render_evidence_graph_to_pdf(html_path, output_path)
                
                return True
                
            except ImportError as e:
                warnings.warn(f"Failed to import graph visualization module: {e}")
                return False
        
        # Fall back to legacy matplotlib visualization for 'image' format
        if format == 'image':
            return self._render_evidence_graph_legacy(output_path)
        
        return False
    
    def _render_evidence_graph_legacy(self, output_path: str) -> bool:
        """
        Legacy matplotlib-based graph rendering.
        
        Args:
            output_path: Path where the graph image should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.evidence_graph_data or not self.evidence_graph_data.get('entities'):
            return False
        
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            import networkx as nx
        except ImportError:
            warnings.warn(
                "matplotlib and networkx are required for graph visualization. "
                "Install them with: pip install matplotlib networkx"
            )
            return False
        
        try:
            # Create a directed graph
            G = nx.DiGraph()
            
            # Add nodes with attributes
            entities = self.evidence_graph_data.get('entities', [])
            for entity in entities:
                entity_name = entity.get('name', 'Unknown')
                entity_type = entity.get('entityType', 'UNKNOWN')
                observations = entity.get('observations', [])
                
                # Add node with type as attribute
                G.add_node(entity_name, 
                          entity_type=entity_type,
                          observations=observations)
            
            # Add edges
            relations = self.evidence_graph_data.get('relations', [])
            for relation in relations:
                from_node = relation.get('from', '')
                to_node = relation.get('to', '')
                rel_type = relation.get('relationType', 'RELATED')
                
                if from_node and to_node:
                    G.add_edge(from_node, to_node, relation=rel_type)
            
            # Create figure with large size for readability
            fig, ax = plt.subplots(figsize=(20, 16))
            
            # Define colors for different entity types
            entity_type_colors = {
                'PAPER': '#FFB6C1',        # Light pink
                'CHEMICAL': '#87CEEB',      # Sky blue
                'CELLLINE': '#98FB98',      # Pale green
                'GENE': '#FFD700',          # Gold
                'ResearchIntent': '#DDA0DD', # Plum
                'RESEARCH_QUESTION': '#DDA0DD', # Plum
                'Chemical': '#87CEEB',      # Sky blue
                'CellLine': '#98FB98',      # Pale green
                'Gene': '#FFD700',          # Gold
                'Paper': '#FFB6C1',         # Light pink
            }
            
            # Assign colors to nodes
            node_colors = []
            for node in G.nodes():
                entity_type = G.nodes[node].get('entity_type', 'UNKNOWN')
                node_colors.append(entity_type_colors.get(entity_type, '#D3D3D3'))
            
            # Use spring layout for better visualization
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, 
                                 node_color=node_colors,
                                 node_size=3000,
                                 alpha=0.9,
                                 ax=ax)
            
            # Draw edges with arrows
            nx.draw_networkx_edges(G, pos,
                                 edge_color='gray',
                                 alpha=0.5,
                                 arrows=True,
                                 arrowsize=15,
                                 arrowstyle='->',
                                 width=1.5,
                                 ax=ax)
            
            # Draw labels with smaller font for readability
            labels = {}
            for node in G.nodes():
                # Truncate long names
                label = node
                if len(label) > 30:
                    label = label[:27] + '...'
                labels[node] = label
            
            nx.draw_networkx_labels(G, pos, labels,
                                  font_size=8,
                                  font_weight='bold',
                                  ax=ax)
            
            # Add edge labels (relation types)
            edge_labels = nx.get_edge_attributes(G, 'relation')
            # Truncate edge labels
            edge_labels = {k: v[:15] + '...' if len(v) > 15 else v 
                          for k, v in edge_labels.items()}
            nx.draw_networkx_edge_labels(G, pos, edge_labels,
                                       font_size=6,
                                       font_color='darkblue',
                                       ax=ax)
            
            # Add legend for entity types
            from matplotlib.patches import Patch
            legend_elements = []
            used_types = set(G.nodes[node].get('entity_type', 'UNKNOWN') for node in G.nodes())
            for entity_type in sorted(used_types):
                color = entity_type_colors.get(entity_type, '#D3D3D3')
                legend_elements.append(Patch(facecolor=color, label=entity_type))
            
            ax.legend(handles=legend_elements, loc='upper left', 
                     fontsize=10, framealpha=0.9)
            
            # Add title and statistics
            num_entities = len(entities)
            num_relations = len(relations)
            ax.set_title(f'Evidence Graph\n({num_entities} entities, {num_relations} relations)',
                        fontsize=16, fontweight='bold', pad=20)
            
            ax.axis('off')
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            return True
            
        except Exception as e:
            warnings.warn(f"Failed to render evidence graph: {e}")
            return False
    
    def _build_supplementary_section(self, story: list, context: dict):
        """
        Build the supplementary materials section with evidence graph.
        Override parent to add evidence graph visualization.
        
        Args:
            story: List of reportlab flowables to append to
            context: Dictionary containing styles, artifact info, and other context
        """
        from reportlab.platypus import Spacer, Paragraph, Image, PageBreak
        
        styles = context['styles']
        inch = context['inch']
        
        story.append(Paragraph("Supplementary Materials", styles['heading']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            "This section contains the evidence graph visualization and detailed code implementations.",
            styles['body']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Add Evidence Graph if available
        if self.evidence_graph_data and self.evidence_graph_data.get('entities'):
            story.append(Paragraph("Evidence Graph Visualization", styles['subheading']))
            story.append(Spacer(1, 0.1*inch))
            
            # Count entities and relations
            num_entities = len(self.evidence_graph_data.get('entities', []))
            num_relations = len(self.evidence_graph_data.get('relations', []))
            
            story.append(Paragraph(
                f"The evidence graph contains <b>{num_entities} entities</b> and "
                f"<b>{num_relations} relations</b> discovered during the research process. "
                "The graph shows the relationships between papers, chemicals, cell lines, genes, "
                "and research questions.",
                styles['body']
            ))
            story.append(Spacer(1, 0.1*inch))
            
            # Render the graph to a temporary file
            temp_graph_path = None
            try:
                temp_graph_fd, temp_graph_path = tempfile.mkstemp(suffix='.png', prefix='evidence_graph_')
                os.close(temp_graph_fd)  # Close file descriptor
                
                # Use legacy image format for PDF embedding
                if self._render_evidence_graph(temp_graph_path, format='image'):
                    # Add the graph image to the PDF
                    try:
                        img = Image(temp_graph_path)
                        
                        # Scale to fit page while maintaining aspect ratio
                        max_width = 7*inch
                        max_height = 9*inch
                        
                        aspect = img.drawHeight / float(img.drawWidth)
                        if img.drawWidth > max_width:
                            img.drawWidth = max_width
                            img.drawHeight = img.drawWidth * aspect
                        if img.drawHeight > max_height:
                            img.drawHeight = max_height
                            img.drawWidth = img.drawHeight / aspect
                        
                        story.append(img)
                        story.append(Spacer(1, 0.3*inch))
                    except Exception as e:
                        story.append(Paragraph(
                            f"<i>Error loading graph image: {e}</i>",
                            styles['body']
                        ))
                else:
                    story.append(Paragraph(
                        "<i>Evidence graph visualization is not available. "
                        "Install matplotlib and networkx to enable graph rendering.</i>",
                        styles['body']
                    ))
            except Exception as e:
                story.append(Paragraph(
                    f"<i>Error rendering evidence graph: {e}</i>",
                    styles['body']
                ))
            finally:
                # Clean up temporary graph file
                if temp_graph_path and os.path.exists(temp_graph_path):
                    try:
                        os.unlink(temp_graph_path)
                    except:
                        pass
            
            story.append(PageBreak())
        
        # Call parent implementation for code execution results
        super()._build_supplementary_section(story, context)
    
    def to_pdf(self, output_dir: str, filename: Optional[str] = None, include_artifacts: bool = True, **kwargs) -> str:
            """
            Convert the execution results to a PDF file with embedded figures and execution details.
            
            This method uses a template pattern - subclasses can override specific sections by
            overriding the corresponding _build_*_section methods.
            
            Args:
                output_dir: Local directory path where the PDF file should be saved
                filename: Optional custom filename (without extension). Defaults to 'execution_report_<timestamp>.pdf'
                include_artifacts: Whether to download and embed artifacts (figures) in the PDF
                **kwargs: Additional arguments passed to section builders for customization
            
            Returns:
                str: Path to the generated PDF file
            """
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
                from reportlab.platypus import KeepTogether, Preformatted
                from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
            except ImportError:
                raise ImportError(
                    "reportlab is required for PDF generation. "
                    "Install it with: pip install reportlab"
                )
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"execution_report_{timestamp}"
            
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            output_path = os.path.join(output_dir, filename)
            
            # Download artifacts if requested
            artifact_files = []
            artifact_dir = None
            if include_artifacts and self.sandbox is not None:
                artifact_dir = tempfile.mkdtemp(prefix="biodsa_artifacts_")
                try:
                    artifact_files = self.download_artifacts(artifact_dir)
                except Exception as e:
                    print(f"Warning: Failed to download artifacts: {e}")
            
            # Create PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Container for PDF elements
            story = []
            
            # Get PDF styles (can be customized by subclasses)
            pdf_styles = self._get_pdf_styles()
            
            # Extract individual styles for convenience
            title_style = pdf_styles['title']
            heading_style = pdf_styles['heading']
            subheading_style = pdf_styles['subheading']
            body_style = pdf_styles['body']
            code_style = pdf_styles['code']
            
            # Build PDF sections using template methods (can be overridden by subclasses)
            context = {
                'artifact_files': artifact_files,
                'artifact_dir': artifact_dir,
                'styles': pdf_styles,
                'colors': colors,
                'inch': inch,
                **kwargs  # Pass through any additional context
            }
            
            # Header section (logo and title)
            self._build_header_section(story, context)
            
            # Section 1: User Query
            self._build_query_section(story, context)
            story.append(PageBreak())
            
            # Section 2: Agent Exploration Process
            self._build_exploration_section(story, context)
            story.append(PageBreak())
            
            # Section 3: Results and Analysis
            self._build_results_section(story, context)
            story.append(PageBreak())
            
            # Section 4: Supplementary Materials
            self._build_supplementary_section(story, context)
            
            # Build PDF
            doc.build(story)
            
            # Cleanup temporary artifact directory
            if artifact_dir and os.path.exists(artifact_dir):
                import shutil
                shutil.rmtree(artifact_dir, ignore_errors=True)
            
            return output_path
    
    def export_evidence_graph_html(self, output_path: str, title: str = "Evidence Graph") -> bool:
        """
        Export the evidence graph as an interactive HTML visualization.
        
        Args:
            output_path: Path where the HTML file should be saved
            title: Title for the graph visualization
            
        Returns:
            bool: True if successful, False otherwise
            
        Example:
            >>> results.export_evidence_graph_html("evidence_graph.html")
        """
        return self._render_evidence_graph(output_path, format='html')
    
    def export_evidence_graph_pdf(self, output_html_path: str, output_pdf_path: str) -> bool:
        """
        Export the evidence graph as a PDF (via HTML rendering).
        
        Requires playwright: pip install playwright && playwright install chromium
        
        Args:
            output_html_path: Path where the HTML file should be saved (intermediate)
            output_pdf_path: Path where the PDF file should be saved
            
        Returns:
            bool: True if successful, False otherwise
            
        Example:
            >>> results.export_evidence_graph_pdf("graph.html", "graph.pdf")
        """
        if self._render_evidence_graph(output_html_path, format='html'):
            try:
                from biodsa.agents.deepevidence.graph_visualization import render_evidence_graph_to_pdf
                return render_evidence_graph_to_pdf(output_html_path, output_pdf_path)
            except ImportError as e:
                warnings.warn(f"Failed to import PDF rendering: {e}")
                return False
        return False

