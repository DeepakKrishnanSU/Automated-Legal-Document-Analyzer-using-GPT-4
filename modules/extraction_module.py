"""
Extraction Module
-----------------
Course: 24CS2506 - Building Applications using GPT-4 (Experiment 5)
Handles text extraction from diverse document formats (.txt, .pdf)
using pypdf and standard file readers with robust fallback encodings.
"""

import os
from typing import Dict, Any
import pypdf


class ExtractionModule:
    """Provides methods to extract raw text and metadata from files."""

    SUPPORTED_EXTENSIONS = [".txt", ".pdf"]

    @staticmethod
    def extract_from_txt(file_path: str) -> Dict[str, Any]:
        """
        Extract text from a plain text (.txt) file with multi-encoding fallback.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")

        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = ""
        used_encoding = None

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                used_encoding = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if used_encoding is None:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            used_encoding = "utf-8 (lossy fallback)"

        char_count = len(content)
        word_count = len(content.split())
        est_pages = max(1, round(word_count / 300))

        return {
            "source_name": os.path.basename(file_path),
            "file_path": os.path.abspath(file_path),
            "file_type": "txt",
            "raw_text": content,
            "page_count": est_pages,
            "char_count": char_count,
            "word_count": word_count,
            "encoding": used_encoding,
            "error": None
        }

    @staticmethod
    def extract_from_pdf(file_path: str) -> Dict[str, Any]:
        """
        Extract text from a PDF file using pypdf.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        extracted_pages = []
        try:
            reader = pypdf.PdfReader(file_path)
            total_pages = len(reader.pages)

            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                extracted_pages.append(page_text)

            full_text = "\n\n--- Page Break ---\n\n".join(extracted_pages).strip()
            char_count = len(full_text)
            word_count = len(full_text.split())

            return {
                "source_name": os.path.basename(file_path),
                "file_path": os.path.abspath(file_path),
                "file_type": "pdf",
                "raw_text": full_text,
                "page_count": total_pages,
                "char_count": char_count,
                "word_count": word_count,
                "encoding": "pdf-stream",
                "error": None
            }
        except Exception as e:
            return {
                "source_name": os.path.basename(file_path),
                "file_path": os.path.abspath(file_path),
                "file_type": "pdf",
                "raw_text": "",
                "page_count": 0,
                "char_count": 0,
                "word_count": 0,
                "encoding": None,
                "error": f"Failed to extract PDF: {str(e)}"
            }

    @classmethod
    def extract_from_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Automatically detect file type and extract text.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Specified file does not exist: {file_path}")

        _, ext = os.path.splitext(file_path.lower())

        if ext == ".txt":
            return cls.extract_from_txt(file_path)
        elif ext == ".pdf":
            return cls.extract_from_pdf(file_path)
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. Supported formats: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            )

    @staticmethod
    def create_doc_from_raw_text(text: str, source_label: str = "Manual Keyboard Input") -> Dict[str, Any]:
        """
        Wraps manually typed or pasted legal text into a standardized document dictionary.
        """
        char_count = len(text)
        word_count = len(text.split())
        est_pages = max(1, round(word_count / 300))

        return {
            "source_name": source_label,
            "file_path": None,
            "file_type": "manual",
            "raw_text": text,
            "page_count": est_pages,
            "char_count": char_count,
            "word_count": word_count,
            "encoding": "utf-8",
            "error": None
        }
