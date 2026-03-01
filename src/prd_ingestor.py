"""
prd_ingestor.py - Ingest Product Requirement Documents from PDF, DOCX, or TXT.
Returns plain text content for downstream LLM processing.
"""

import os
from typing import Optional


def ingest_prd(file_path: str) -> str:
    """
    Read a PRD file and return its text content.
    Supports: .txt, .md, .pdf, .docx
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PRD file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".txt", ".md"):
        return _read_text(file_path)
    elif ext == ".pdf":
        return _read_pdf(file_path)
    elif ext == ".docx":
        return _read_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use .txt, .md, .pdf, or .docx")


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_pdf(path: str) -> str:
    """Extract text from PDF using PyPDF2 or pdfplumber (whichever available)."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts)
    except ImportError:
        pass

    try:
        import PyPDF2
        text_parts = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts)
    except ImportError:
        raise ImportError(
            "PDF support requires 'pdfplumber' or 'PyPDF2'. "
            "Install with: pip install pdfplumber"
        )


def _read_docx(path: str) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
        doc = docx.Document(path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except ImportError:
        raise ImportError(
            "DOCX support requires 'python-docx'. "
            "Install with: pip install python-docx"
        )
