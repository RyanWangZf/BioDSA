"""
Provide execution results from the agent and provide the way to download the artifacts from the sandbox.
"""

from typing import List, Dict, Optional
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
import json
import os
import tempfile
from datetime import datetime

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

    def to_json(self, output_path: str=None) -> str:
        """
        Convert the execution results to a JSON file
        
        Args:
            output_path: Local path where the JSON file should be saved
        """
        json_data = {
                    'message_history': self.message_history,
                    'code_execution_results': self.code_execution_results,
                    'final_response': self.final_response
                }
        if output_path is not None:
            with open(output_path, 'w') as f:
                json.dump(json_data, f)
        return json_data


    def download_artifacts(self, output_dir: str) -> List[str]:
        """
        Download the artifacts from the sandbox to local machine
        
        Args:
            output_dir: Local directory path where artifacts should be downloaded

        Returns:
            List[str]: List of downloaded file names
        """
        return self.sandbox.download_artifacts(output_dir=output_dir)

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
    
    # ========== PDF Style Configuration (Override in subclasses) ==========
    
    def _get_pdf_styles(self) -> dict:
        """
        Get PDF styles configuration. Override this method to customize styles.
        
        Returns:
            Dictionary of style names to ParagraphStyle objects
        """
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        
        styles = getSampleStyleSheet()
        
        return {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2C3E50'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'heading': ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#34495E'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            ),
            'subheading': ParagraphStyle(
                'CustomSubHeading',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#7F8C8D'),
                spaceAfter=6,
                fontName='Helvetica-Bold'
            ),
            'body': ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=6
            ),
            'code': ParagraphStyle(
                'CustomCode',
                parent=styles['Code'],
                fontSize=8,
                fontName='Courier',
                textColor=colors.HexColor('#2C3E50'),
                backColor=colors.HexColor('#ECF0F1'),
                leftIndent=10,
                rightIndent=10,
                spaceAfter=6,
                spaceBefore=6,
                leading=11
            )
        }
    
    # ========== PDF Section Builders (Override in subclasses) ==========
    
    def _build_header_section(self, story: list, context: dict):
        """
        Build the header section with logo and title. Override to customize header.
        
        Args:
            story: List of reportlab flowables to append to
            context: Dictionary containing styles, artifact info, and other context
        """
        from reportlab.platypus import Spacer, Paragraph, Image, Table
        from PIL import Image as PILImage
        
        # Add logo with proper aspect ratio positioned on the left
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  'figs', 'keiji_logo_stacked_horizontal.png')
        
        story.append(Spacer(1, 0.2*context['inch']))
        
        if os.path.exists(logo_path):
            try:
                # Get actual image dimensions to preserve aspect ratio
                pil_img = PILImage.open(logo_path)
                img_width, img_height = pil_img.size
                aspect_ratio = img_height / img_width
                
                # Set desired width (smaller for left alignment)
                desired_width = 1.4 * context['inch']
                desired_height = desired_width * aspect_ratio
                
                # Create left-aligned clickable logo
                clickable_logo = self._create_clickable_image(
                    logo_path, 
                    "https://keiji.ai/",
                    width=desired_width,
                    height=desired_height,
                    align='LEFT'
                )
                
                story.append(clickable_logo)
                story.append(Spacer(1, 0.3*context['inch']))
            except Exception as e:
                print(f"Warning: Could not load Keiji AI logo: {e}")
                story.append(Spacer(1, 0.3*context['inch']))
        else:
            story.append(Spacer(1, 0.3*context['inch']))
        
        # Add title (centered)
        story.append(Paragraph("BioDSA Analysis Report", context['styles']['title']))
        story.append(Spacer(1, 0.15*context['inch']))
    
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
            ['Artifacts Generated:', str(len(context['artifact_files']))]
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
    
    def _build_exploration_section(self, story: list, context: dict):
        """
        Build the agent exploration process section. Override to customize exploration display.
        
        Args:
            story: List of reportlab flowables to append to
            context: Dictionary containing styles, artifact info, and other context
        """
        from reportlab.platypus import Spacer, Paragraph
        
        styles = context['styles']
        inch = context['inch']
        
        story.append(Paragraph("Agent Exploration Process", styles['heading']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            "The following shows the agent's reasoning and exploration process. "
            "Code blocks are truncated for readability - full implementations are in the Supplementary Materials section.",
            styles['body']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        execution_counter = 0
        
        for i, msg in enumerate(self.message_history, 1):
            role = msg.get('role', 'unknown').lower()
            content = msg.get('content', '')
            
            # Skip user messages
            if role in ['user', 'human']:
                continue
            
            # Message header
            story.append(Paragraph(f"<b>Step {i}: {role.upper()}</b>", styles['subheading']))
            
            # Process content
            processed_content = self._process_message_with_truncated_code(
                content, execution_counter + 1, styles['code'], styles['body']
            )
            
            # Check if contains code
            if '```' in content or any(kw in content for kw in ['import ', 'def ', 'plt.', 'pd.']):
                execution_counter += 1
            
            # Add content
            for element in processed_content:
                story.append(element)
            
            story.append(Spacer(1, 0.15*inch))
    
    def _build_results_section(self, story: list, context: dict):
        """
        Build the results and analysis section. Override to customize results display.
        
        Args:
            story: List of reportlab flowables to append to
            context: Dictionary containing styles, artifact info, and other context
        """
        from reportlab.platypus import Spacer, Paragraph, Image
        
        styles = context['styles']
        inch = context['inch']
        artifact_files = context['artifact_files']
        artifact_dir = context['artifact_dir']
        
        story.append(Paragraph("Results and Analysis", styles['heading']))
        story.append(Spacer(1, 0.1*inch))
        
        # Final response
        story.append(Paragraph("Summary", styles['subheading']))
        for line in self.final_response.split('\n'):
            if line.strip():
                story.append(Paragraph(self._escape_html(line), styles['body']))
        story.append(Spacer(1, 0.3*inch))
        
        # Artifacts
        if artifact_files and artifact_dir:
            story.append(Paragraph("Generated Visualizations", styles['subheading']))
            story.append(Spacer(1, 0.1*inch))
            
            for artifact_file in artifact_files:
                artifact_path = os.path.join(artifact_dir, artifact_file)
                
                if not os.path.exists(artifact_path):
                    continue
                
                image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')
                if artifact_file.lower().endswith(image_extensions):
                    story.append(Paragraph(f"<b>{artifact_file}</b>", styles['body']))
                    
                    try:
                        img = Image(artifact_path)
                        img.drawHeight = min(img.drawHeight, 5*inch)
                        img.drawWidth = min(img.drawWidth, 6.5*inch)
                        
                        aspect = img.drawHeight / float(img.drawWidth)
                        if img.drawWidth > 6.5*inch:
                            img.drawWidth = 6.5*inch
                            img.drawHeight = img.drawWidth * aspect
                        if img.drawHeight > 5*inch:
                            img.drawHeight = 5*inch
                            img.drawWidth = img.drawHeight / aspect
                        
                        story.append(img)
                        story.append(Spacer(1, 0.3*inch))
                    except Exception as e:
                        story.append(Paragraph(f"<i>Error loading image: {e}</i>", styles['body']))
    
    def _build_supplementary_section(self, story: list, context: dict):
        """
        Build the supplementary materials section. Override to customize supplementary display.
        
        Args:
            story: List of reportlab flowables to append to
            context: Dictionary containing styles, artifact info, and other context
        """
        from reportlab.platypus import Spacer, Paragraph, Preformatted
        
        styles = context['styles']
        inch = context['inch']
        
        story.append(Paragraph("Supplementary Materials", styles['heading']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            "This section contains detailed code implementations and execution results.",
            styles['body']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        for i, result in enumerate(self.code_execution_results, 1):
            execution_elements = []
            
            # Header
            execution_elements.append(Paragraph(f"<b>Code Execution #{i}</b>", styles['subheading']))
            execution_elements.append(Spacer(1, 0.05*inch))
            
            # Check for tool call input (JSON data) - display before code
            json_fields = ['tool_input', 'input', 'arguments', 'tool_args', 'function_args', 'parameters']
            for field in json_fields:
                if field in result and result[field]:
                    execution_elements.append(Paragraph(f"<b>Tool Input ({field}):</b>", styles['body']))
                    json_elements = self._format_json_box(result[field], styles)
                    for elem in json_elements:
                        execution_elements.append(elem)
                    execution_elements.append(Spacer(1, 0.1*inch))
                    break  # Only show first matching field
            
            # Code
            code_value = result.get('code', '')
            if code_value:
                execution_elements.append(Paragraph("<b>Code:</b>", styles['body']))
                
                code_text = str(code_value)
                code_lines = code_text.split('\n')
                if len(code_lines) > 100:
                    code_text = '\n'.join(code_lines[:100]) + "\n\n... [code truncated - too long]"
                
                code_block = Preformatted(code_text, style=styles['code'], maxLineLength=85)
                execution_elements.append(code_block)
                execution_elements.append(Spacer(1, 0.1*inch))
            
            # Output
            output_value = result.get('output', '')
            if output_value:
                execution_elements.append(Paragraph("<b>Output:</b>", styles['body']))
                
                output_str = str(output_value)
                if len(output_str) > 1000:
                    output_str = output_str[:1000] + "\n... [output truncated]"
                
                output_block = Preformatted(output_str, style=styles['code'], maxLineLength=85)
                execution_elements.append(output_block)
                execution_elements.append(Spacer(1, 0.1*inch))
            
            # Check for tool call output (JSON data)
            if 'tool_output' in result and result['tool_output']:
                execution_elements.append(Paragraph("<b>Tool Output (JSON):</b>", styles['body']))
                json_elements = self._format_json_box(result['tool_output'], styles)
                for elem in json_elements:
                    execution_elements.append(elem)
                execution_elements.append(Spacer(1, 0.1*inch))
            
            # Metrics
            metrics = []
            if 'exit_code' in result:
                metrics.append(f"Exit Code: {result['exit_code']}")
            if 'running_time' in result:
                metrics.append(f"Runtime: {result['running_time']:.2f}s")
            if 'peak_memory_mb' in result:
                metrics.append(f"Memory: {result['peak_memory_mb']:.1f}MB")
            
            if metrics:
                execution_elements.append(
                    Paragraph("<b>Metrics:</b> " + " | ".join(metrics), styles['body'])
                )
            
            execution_elements.append(Spacer(1, 0.25*inch))
            
            for elem in execution_elements:
                story.append(elem)
    
    #========== Helper Methods ==========
    
    def _get_user_query(self) -> str:
        """
        Extract user query from message history. Override to customize query extraction.
        
        Returns:
            User query string
        """
        for msg in self.message_history:
            if msg.get('role', '').lower() in ['user', 'human']:
                return msg.get('content', '')
        return ""
    
    def _create_clickable_image(self, image_path: str, url: str, width, height, align='CENTER'):
        """
        Create a clickable image flowable with hyperlink.
        
        Args:
            image_path: Path to the image file
            url: URL to link to when image is clicked
            width: Width of the image
            height: Height of the image
            align: Alignment of the image ('LEFT', 'CENTER', 'RIGHT')
            
        Returns:
            Custom flowable with clickable image
        """
        from reportlab.platypus.flowables import Flowable
        
        class ClickableImage(Flowable):
            def __init__(self, image_path, url, width, height, align):
                Flowable.__init__(self)
                self.image_path = image_path
                self.url = url
                self._width = width
                self._height = height
                self.hAlign = align
                
            def draw(self):
                # Calculate position based on alignment
                page_width = self.canv._pagesize[0]
                
                if self.hAlign == 'CENTER':
                    x_offset = (page_width - self._width) / 2
                elif self.hAlign == 'RIGHT':
                    x_offset = page_width - self._width - self.canv._x
                else:  # LEFT
                    x_offset = 0
                
                # Save canvas state
                self.canv.saveState()
                
                # Draw the image
                self.canv.drawImage(
                    self.image_path,
                    x_offset,
                    0,
                    width=self._width,
                    height=self._height,
                    preserveAspectRatio=True,
                    mask='auto'  # Handle transparency
                )
                
                # Add hyperlink annotation (full image area)
                self.canv.linkURL(
                    self.url,
                    (x_offset, 0, x_offset + self._width, self._height),
                    relative=1
                )
                
                # Restore canvas state
                self.canv.restoreState()
            
            def wrap(self, availWidth, availHeight):
                # Return the size needed (width, height)
                return (self._width, self._height)
        
        return ClickableImage(image_path, url, width, height, align)
    
    def _process_message_with_truncated_code(self, text: str, execution_num: int, code_style, body_style) -> list:
        """
        Process message content, truncating code blocks and adding references to supplementary materials.
        
        Args:
            text: Message text that may contain code blocks
            execution_num: Current execution number for cross-referencing
            code_style: ReportLab style for code blocks
            body_style: ReportLab style for body text
            
        Returns:
            List of reportlab elements (Paragraphs, Preformatted, etc.)
        """
        from reportlab.platypus import Paragraph, Preformatted, Spacer
        from reportlab.lib.units import inch
        
        if not isinstance(text, str):
            return [Paragraph("<i>No content</i>", body_style)]
        
        elements = []
        lines = text.split('\n')
        current_text = []
        in_code_block = False
        code_block_lines = []
        code_language = ""
        max_code_preview_lines = 5  # Show first 5 lines of code
        
        for line in lines:
            # Detect code block markers
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Starting a code block
                    in_code_block = True
                    code_language = line.strip()[3:].strip() or "python"
                    code_block_lines = []
                    
                    # Add any accumulated text before the code block
                    if current_text:
                        text_content = '\n'.join(current_text).strip()
                        if text_content:
                            for text_line in current_text:
                                if text_line.strip():
                                    elements.append(Paragraph(self._escape_html(text_line), body_style))
                        current_text = []
                else:
                    # Ending a code block
                    in_code_block = False
                    
                    # Add truncated code block
                    if code_block_lines:
                        # Show preview of first few lines
                        preview_lines = code_block_lines[:max_code_preview_lines]
                        preview_text = '\n'.join(preview_lines)
                        
                        if len(code_block_lines) > max_code_preview_lines:
                            preview_text += f"\n\n... ({len(code_block_lines) - max_code_preview_lines} more lines)"
                            reference_text = f"<i>→ See Code Execution #{execution_num} in Supplementary Materials for full implementation</i>"
                        else:
                            reference_text = f"<i>→ Full code in Supplementary Materials (Code Execution #{execution_num})</i>"
                        
                        # Add code preview
                        code_block = Preformatted(
                            preview_text,
                            style=code_style,
                            maxLineLength=80
                        )
                        elements.append(code_block)
                        elements.append(Paragraph(reference_text, body_style))
                        elements.append(Spacer(1, 0.05*inch))
                    
                    code_block_lines = []
                continue
            
            # Inside code block - collect lines
            if in_code_block:
                code_block_lines.append(line)
            else:
                # Regular text line
                current_text.append(line)
        
        # Add any remaining text
        if current_text:
            text_content = '\n'.join(current_text).strip()
            if text_content:
                # Truncate if too long
                if len(text_content) > 600:
                    text_content = text_content[:600] + "... [truncated]"
                
                for text_line in current_text[:20]:  # Max 20 lines of text
                    if text_line.strip():
                        elements.append(Paragraph(self._escape_html(text_line), body_style))
        
        # If no elements were created, add a default message
        if not elements:
            elements.append(Paragraph(
                f"<i>Action executed - see Code Execution #{execution_num} in Supplementary Materials</i>",
                body_style
            ))
        
        return elements
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters for reportlab.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        if not isinstance(text, str):
            text = str(text)
        
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        
        return text
    
    def _format_json_box(self, data, styles) -> list:
        """
        Format JSON/dict data in a styled code box.
        
        Args:
            data: Dictionary or JSON-serializable data
            styles: Dictionary of PDF styles
            
        Returns:
            List of reportlab flowables for the JSON box
        """
        from reportlab.platypus import Paragraph, Preformatted, Spacer
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        import json
        
        elements = []
        
        # Create a special style for JSON with distinct background
        json_style = ParagraphStyle(
            'JSONBox',
            parent=styles['code'],
            fontSize=8,
            fontName='Courier',
            textColor=colors.HexColor('#1E3A8A'),  # Dark blue
            backColor=colors.HexColor('#EFF6FF'),  # Light blue background
            leftIndent=15,
            rightIndent=15,
            spaceBefore=4,
            spaceAfter=4,
            leading=11,
            borderColor=colors.HexColor('#93C5FD'),  # Border color
            borderWidth=1,
            borderPadding=8
        )
        
        # Convert to formatted JSON string
        try:
            if isinstance(data, str):
                # Try to parse if it's a JSON string
                try:
                    data = json.loads(data)
                except:
                    pass
            
            if isinstance(data, (dict, list)):
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                json_str = str(data)
        except Exception as e:
            json_str = str(data)
        
        # Truncate if too long
        lines = json_str.split('\n')
        if len(lines) > 50:
            json_str = '\n'.join(lines[:50]) + "\n... [truncated]"
        
        # Add JSON in formatted box
        json_block = Preformatted(json_str, style=json_style, maxLineLength=80)
        elements.append(json_block)
        
        return elements
