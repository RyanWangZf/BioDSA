"""
Multimodal tool wrappers for reading images and PDFs.

These tools encode visual content so that LLMs with vision capabilities can
process them.  They return ``MultimodalToolResult`` objects which the calling
agent's tool-node should convert to multimodal ``ToolMessage`` content blocks
via ``BaseAgent._build_tool_message``.

Usage in an agent's tool node::

    from biodsa.tool_wrappers.multimodal_tools import MultimodalToolResult

    out = tool._run(**args)
    if isinstance(out, MultimodalToolResult):
        content = out.to_langchain_content()
        return {"messages": [ToolMessage(content=content, ...)]}
"""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Type

from PIL import Image
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


# ------------------------------------------------------------------ #
# Multimodal result wrapper
# ------------------------------------------------------------------ #


@dataclass
class MultimodalToolResult:
    """
    A tool result that carries both text and images.

    The ``to_langchain_content()`` method returns a list of LangChain
    standard content blocks (``{"type": "text", ...}``,
    ``{"type": "image", ...}``) suitable for use as ``ToolMessage.content``.
    This format is automatically translated by langchain-openai,
    langchain-anthropic, and langchain-google-genai.
    """

    text: str = ""
    images: List[Dict[str, str]] = field(default_factory=list)
    # Each image dict: {"base64": "<data>", "mime_type": "image/jpeg"}

    def to_langchain_content(self) -> list:
        """Build a list of LangChain standard content blocks."""
        blocks: list = []
        if self.text:
            blocks.append({"type": "text", "text": self.text})
        for img in self.images:
            blocks.append({
                "type": "image",
                "base64": img["base64"],
                "mime_type": img["mime_type"],
            })
        return blocks or [{"type": "text", "text": "(empty result)"}]


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

_SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif",
}

_EXT_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
}

# Maximum dimension (px) for any side.  Larger images are resized to save
# tokens and stay within API limits.
_MAX_IMAGE_DIM = 2048
# JPEG quality for compression
_JPEG_QUALITY = 85


def _encode_image(
    image_path: Path,
    max_dim: int = _MAX_IMAGE_DIM,
    jpeg_quality: int = _JPEG_QUALITY,
) -> Dict[str, str]:
    """
    Read an image from disk, optionally resize, and return a dict with
    base64-encoded data and MIME type.

    Always re-encodes as JPEG (for compression) unless the image has
    transparency (RGBA/LA/PA), in which case PNG is used.
    """
    img = Image.open(image_path)

    # Resize if too large
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Choose output format
    has_alpha = img.mode in ("RGBA", "LA", "PA")
    if has_alpha:
        out_format = "PNG"
        mime = "image/png"
    else:
        # Convert to RGB for JPEG
        if img.mode != "RGB":
            img = img.convert("RGB")
        out_format = "JPEG"
        mime = "image/jpeg"

    buf = io.BytesIO()
    img.save(buf, format=out_format, quality=jpeg_quality)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return {"base64": b64, "mime_type": mime}


def _encode_pdf_page_as_image(
    pdf_path: Path,
    page_no: int,
    dpi: int = 150,
    jpeg_quality: int = _JPEG_QUALITY,
) -> Dict[str, str]:
    """Render one PDF page as a JPEG image and return base64 + mime_type."""
    import pymupdf  # lazy import to avoid hard dep at module level

    doc = pymupdf.open(str(pdf_path))
    page = doc[page_no]
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    # Convert pixmap to PIL Image, then to JPEG bytes
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    # Resize if overly large
    w, h = img.size
    if max(w, h) > _MAX_IMAGE_DIM:
        scale = _MAX_IMAGE_DIM / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    doc.close()
    return {"base64": b64, "mime_type": "image/jpeg"}


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract full text from all pages of a PDF using PyMuPDF."""
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    parts = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            parts.append(f"--- Page {i + 1} ---\n{text}")
    doc.close()
    return "\n\n".join(parts)


# ------------------------------------------------------------------ #
# ReadImageTool
# ------------------------------------------------------------------ #


class ReadImageInput(BaseModel):
    image_path: str = Field(
        description=(
            "Path to the image file (relative to workspace). "
            "Supported: jpg, jpeg, png, gif, webp, bmp, tiff."
        )
    )


class ReadImageTool(BaseTool):
    """
    Read an image file and encode it for LLM vision processing.

    Returns a ``MultimodalToolResult`` so the agent can see the image
    in the next turn.  Works with OpenAI, Anthropic, and Google models
    via LangChain's standard image content blocks.
    """

    name: str = "read_image"
    description: str = (
        "Read an image file from the workspace and make it visible to the LLM. "
        "Pass the relative path to the image. The image will be encoded and "
        "included in the next model turn so you can describe or analyse it. "
        "Supported formats: jpg, png, gif, webp, bmp, tiff."
    )
    args_schema: Type[BaseModel] = ReadImageInput
    data_root: Path = None

    def __init__(self, data_root: Path, **kwargs):
        super().__init__(**kwargs)
        self.data_root = Path(data_root).resolve()

    def _run(self, image_path: str) -> MultimodalToolResult:  # type: ignore[override]
        image_path = image_path.strip().strip("/")
        if ".." in image_path:
            return MultimodalToolResult(
                text=f"Error: '..' not allowed in path: {image_path}"
            )

        full_path = self.data_root / image_path
        if not full_path.exists():
            return MultimodalToolResult(
                text=f"Error: file not found: {image_path}"
            )

        ext = full_path.suffix.lower()
        if ext not in _SUPPORTED_IMAGE_EXTENSIONS:
            return MultimodalToolResult(
                text=(
                    f"Error: unsupported image format '{ext}'. "
                    f"Supported: {', '.join(sorted(_SUPPORTED_IMAGE_EXTENSIONS))}"
                )
            )

        try:
            img_data = _encode_image(full_path)
            # Get dimensions for the text summary
            img = Image.open(full_path)
            w, h = img.size
            size_kb = full_path.stat().st_size / 1024
            return MultimodalToolResult(
                text=(
                    f"Image loaded: {image_path} "
                    f"({w}×{h} px, {size_kb:.0f} KB). "
                    f"The image is included below for your analysis."
                ),
                images=[img_data],
            )
        except Exception as e:
            return MultimodalToolResult(
                text=f"Error reading image {image_path}: {e}"
            )


# ------------------------------------------------------------------ #
# ReadPdfTool
# ------------------------------------------------------------------ #

# Page threshold: PDFs with more pages than this are processed as text
_PDF_PAGE_THRESHOLD = 20


class ReadPdfInput(BaseModel):
    pdf_path: str = Field(
        description=(
            "Path to the PDF file (relative to workspace)."
        )
    )
    page_range: Optional[str] = Field(
        default=None,
        description=(
            "Optional page range to read, e.g. '1-5' or '3,7,10'. "
            "If omitted, all pages are processed. For long PDFs (>20 pages) "
            "only text extraction is used regardless."
        ),
    )
    search_query: Optional[str] = Field(
        default=None,
        description=(
            "Optional search query for long PDFs. When the PDF is processed "
            "as text (>20 pages), only paragraphs matching this query (and "
            "surrounding context) are returned. Use regex patterns."
        ),
    )


class ReadPdfTool(BaseTool):
    """
    Read a PDF file for LLM processing.

    - **Short PDFs** (≤20 pages): each page is rendered as an image and
      returned as multimodal content so the LLM can see figures, tables,
      and layout.
    - **Long PDFs** (>20 pages): full text is extracted with PyMuPDF.
      Use the optional ``search_query`` parameter to filter relevant
      sections (regex match on extracted text). The agent should use an
      agentic search pattern — first get an overview, then search for
      specific sections.
    """

    name: str = "read_pdf"
    description: str = (
        "Read a PDF file from the workspace. Short PDFs (≤20 pages) are "
        "converted to images so the LLM can see figures and layout. Long "
        "PDFs (>20 pages) are converted to text; use the search_query "
        "parameter (regex) to find relevant sections instead of reading "
        "everything. Supports page_range to limit which pages to read."
    )
    args_schema: Type[BaseModel] = ReadPdfInput
    data_root: Path = None
    page_threshold: int = _PDF_PAGE_THRESHOLD

    def __init__(
        self,
        data_root: Path,
        page_threshold: int = _PDF_PAGE_THRESHOLD,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.data_root = Path(data_root).resolve()
        self.page_threshold = page_threshold

    def _run(  # type: ignore[override]
        self,
        pdf_path: str,
        page_range: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> MultimodalToolResult:
        pdf_path = pdf_path.strip().strip("/")
        if ".." in pdf_path:
            return MultimodalToolResult(
                text=f"Error: '..' not allowed in path: {pdf_path}"
            )

        full_path = self.data_root / pdf_path
        if not full_path.exists():
            return MultimodalToolResult(
                text=f"Error: file not found: {pdf_path}"
            )
        if full_path.suffix.lower() != ".pdf":
            return MultimodalToolResult(
                text=f"Error: not a PDF file: {pdf_path}"
            )

        try:
            import pymupdf
            doc = pymupdf.open(str(full_path))
            total_pages = len(doc)
            doc.close()
        except Exception as e:
            return MultimodalToolResult(text=f"Error opening PDF: {e}")

        # Parse page_range into a list of 0-based indices
        pages = self._parse_page_range(page_range, total_pages)

        # Decide strategy based on page count
        effective_pages = len(pages) if pages is not None else total_pages
        use_images = effective_pages <= self.page_threshold

        if use_images:
            return self._read_as_images(full_path, pages, total_pages)
        else:
            return self._read_as_text(
                full_path, pages, total_pages, search_query
            )

    # --- Image mode (short PDFs) ---

    def _read_as_images(
        self,
        pdf_path: Path,
        pages: Optional[List[int]],
        total_pages: int,
    ) -> MultimodalToolResult:
        """Render selected PDF pages as images."""
        if pages is None:
            pages = list(range(total_pages))

        images: List[Dict[str, str]] = []
        errors: List[str] = []
        for pg in pages:
            try:
                img_data = _encode_pdf_page_as_image(pdf_path, pg)
                images.append(img_data)
            except Exception as e:
                errors.append(f"Page {pg + 1}: {e}")

        text = (
            f"PDF loaded as images: {pdf_path.name} "
            f"({len(images)}/{total_pages} pages). "
            f"Each page is included below as an image."
        )
        if errors:
            text += f"\nErrors: {'; '.join(errors)}"

        return MultimodalToolResult(text=text, images=images)

    # --- Text mode (long PDFs) ---

    def _read_as_text(
        self,
        pdf_path: Path,
        pages: Optional[List[int]],
        total_pages: int,
        search_query: Optional[str] = None,
    ) -> MultimodalToolResult:
        """Extract text from PDF, optionally filtering by search_query."""
        import pymupdf
        import re as re_module

        doc = pymupdf.open(str(pdf_path))
        if pages is None:
            pages = list(range(total_pages))

        page_texts: List[str] = []
        for pg in pages:
            text = doc[pg].get_text("text")
            if text.strip():
                page_texts.append(f"--- Page {pg + 1} ---\n{text}")
        doc.close()

        full_text = "\n\n".join(page_texts)

        if search_query:
            # Filter to paragraphs matching the query + surrounding context
            matches = self._search_in_text(full_text, search_query)
            if matches:
                text_out = (
                    f"PDF text search results for '{search_query}' in "
                    f"{pdf_path.name} ({total_pages} pages):\n\n"
                    + "\n\n---\n\n".join(matches)
                )
            else:
                text_out = (
                    f"No matches for '{search_query}' in {pdf_path.name} "
                    f"({total_pages} pages). Try a different search query.\n\n"
                    f"Available page headers (first 100 chars each):\n"
                    + "\n".join(
                        pt[:120] + "..." for pt in page_texts[:30]
                    )
                )
        else:
            # Return full text (truncated if very large)
            max_chars = 200_000  # ~50K tokens
            if len(full_text) > max_chars:
                text_out = (
                    f"PDF text extracted: {pdf_path.name} ({total_pages} "
                    f"pages, {len(full_text)} chars — truncated to "
                    f"{max_chars} chars).\n\n"
                    f"TIP: Use the search_query parameter to find specific "
                    f"sections instead of reading the full text.\n\n"
                    + full_text[:max_chars]
                    + "\n\n... [TRUNCATED] ..."
                )
            else:
                text_out = (
                    f"PDF text extracted: {pdf_path.name} ({total_pages} "
                    f"pages, {len(full_text)} chars).\n\n"
                    + full_text
                )

        return MultimodalToolResult(text=text_out)

    @staticmethod
    def _search_in_text(
        full_text: str,
        query: str,
        context_chars: int = 500,
    ) -> List[str]:
        """
        Search for regex *query* in *full_text* and return matching
        snippets with surrounding context.
        """
        import re as re_module

        try:
            pattern = re_module.compile(query, re_module.IGNORECASE)
        except re_module.error:
            # Fall back to literal search if regex is invalid
            pattern = re_module.compile(re_module.escape(query), re_module.IGNORECASE)

        matches: List[str] = []
        seen_ranges: List[tuple] = []
        for m in pattern.finditer(full_text):
            start = max(0, m.start() - context_chars)
            end = min(len(full_text), m.end() + context_chars)
            # Avoid overlapping snippets
            if seen_ranges and start < seen_ranges[-1][1]:
                # Extend previous range
                seen_ranges[-1] = (seen_ranges[-1][0], end)
                matches[-1] = full_text[seen_ranges[-1][0]:end]
            else:
                seen_ranges.append((start, end))
                snippet = full_text[start:end]
                matches.append(snippet)
            if len(matches) >= 20:
                break
        return matches

    @staticmethod
    def _parse_page_range(
        page_range: Optional[str],
        total_pages: int,
    ) -> Optional[List[int]]:
        """
        Parse a page range string like '1-5' or '3,7,10' into a sorted
        list of 0-based page indices.  Returns None if no range given.
        """
        if not page_range:
            return None
        pages: set = set()
        for part in page_range.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    a_int = max(1, int(a.strip()))
                    b_int = min(total_pages, int(b.strip()))
                    for p in range(a_int, b_int + 1):
                        pages.add(p - 1)  # 0-based
                except ValueError:
                    continue
            else:
                try:
                    p = int(part)
                    if 1 <= p <= total_pages:
                        pages.add(p - 1)
                except ValueError:
                    continue
        return sorted(pages) if pages else None
