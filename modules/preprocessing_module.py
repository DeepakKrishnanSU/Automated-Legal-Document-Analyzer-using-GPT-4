"""
Preprocessing Module
--------------------
Course: 24CS2506 - Building Applications using GPT-4 (Experiment 5)
Implements Part B (Q3): Document Preprocessing.
- Removes unnecessary spaces and unwanted control characters
- Normalizes unicode quotation marks, dashes, and whitespace
- Identifies contract sections/clauses using pattern matching
- Splits documents into manageable chunks
- Analyzes document metrics and section breakdown using Pandas
"""

import re
from typing import Dict, Any, List
import pandas as pd


class PreprocessingModule:
    """Preprocesses raw legal text, extracts sections, and creates chunks."""

    SECTION_REGEX = re.compile(
        r"(?m)^(?:(?:ARTICLE|SECTION|CLAUSE)\s+[\dA-ZIVX]+[:.\s\-]*|[0-9]{1,2}\.[\s\t]+|[A-Z][A-Z\s,/\-]{3,40}:?\s*$)",
        re.MULTILINE
    )

    @classmethod
    def clean_text(cls, text: str) -> str:
        """
        Removes unnecessary spaces, normalizes quotes/dashes,
        and eliminates unprintable characters.
        """
        if not text:
            return ""

        # Normalize unicode quotes and dashes
        text = text.replace("“", '"').replace("”", '"')
        text = text.replace("‘", "'").replace("’", "'")
        text = text.replace("–", "-").replace("—", "-")
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove null characters and non-printable control characters (except newline, tab)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Replace excessive horizontal whitespace with a single space
        text = re.sub(r"[ \t]+", " ", text)

        # Replace 3 or more consecutive newlines with 2 newlines (preserve paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Clean trailing spaces on lines
        cleaned_lines = [line.strip() for line in text.split("\n")]
        return "\n".join(cleaned_lines).strip()

    @classmethod
    def identify_sections(cls, text: str) -> List[Dict[str, Any]]:
        """
        Detects contract sections and clauses based on common legal numbering and headers.
        """
        lines = text.split("\n")
        sections = []
        current_title = "Preamble / Recitals"
        current_lines = []

        for line in lines:
            stripped = line.strip()
            if cls.SECTION_REGEX.match(stripped) and len(stripped) < 80:
                if current_lines:
                    sections.append({
                        "title": current_title,
                        "content": "\n".join(current_lines).strip(),
                        "word_count": len(" ".join(current_lines).split()),
                        "char_count": len("\n".join(current_lines).strip())
                    })
                    current_lines = []
                current_title = stripped
            else:
                if stripped:
                    current_lines.append(stripped)

        if current_lines:
            sections.append({
                "title": current_title,
                "content": "\n".join(current_lines).strip(),
                "word_count": len(" ".join(current_lines).split()),
                "char_count": len("\n".join(current_lines).strip())
            })

        return sections

    @classmethod
    def divide_into_chunks(cls, text: str, chunk_size: int = 1500, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Divides long documents into overlapping text chunks with sentence boundaries.
        """
        if len(text) <= chunk_size:
            return [{
                "chunk_id": 1,
                "text": text,
                "char_count": len(text),
                "word_count": len(text.split())
            }]

        chunks = []
        start = 0
        text_len = len(text)
        chunk_id = 1

        while start < text_len:
            end = min(start + chunk_size, text_len)

            # Try to break at paragraph or period boundary if not at the absolute end
            if end < text_len:
                boundary = text.rfind("\n\n", start, end)
                if boundary == -1 or boundary <= start:
                    boundary = text.rfind(". ", start, end)
                if boundary != -1 and boundary > start + (chunk_size // 2):
                    end = boundary + 1

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_content,
                    "char_count": len(chunk_content),
                    "word_count": len(chunk_content.split())
                })
                chunk_id += 1

            if end >= text_len:
                break
            start = max(end - overlap, start + 1)

        return chunks

    @classmethod
    def create_section_dataframe(cls, sections: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Builds a structured Pandas DataFrame summarizing detected contract sections.
        """
        if not sections:
            return pd.DataFrame(columns=["Section_ID", "Title", "Words", "Characters", "Snippet"])

        rows = []
        for idx, sec in enumerate(sections, 1):
            snippet = (sec["content"][:60] + "...") if len(sec["content"]) > 60 else sec["content"]
            rows.append({
                "Section_ID": idx,
                "Title": sec["title"],
                "Words": sec["word_count"],
                "Characters": sec["char_count"],
                "Snippet": snippet.replace("\n", " ")
            })
        return pd.DataFrame(rows)

    @classmethod
    def preprocess_document(cls, doc_data: Dict[str, Any], max_chunk_chars: int = 2000) -> Dict[str, Any]:
        """
        Full preprocessing pipeline executing cleaning, section identification,
        chunking, and metrics calculation using Pandas.
        """
        raw_text = doc_data.get("raw_text", "")
        cleaned = cls.clean_text(raw_text)
        sections = cls.identify_sections(cleaned)
        chunks = cls.divide_into_chunks(cleaned, chunk_size=max_chunk_chars)
        df_sections = cls.create_section_dataframe(sections)

        raw_words = len(raw_text.split())
        cleaned_words = len(cleaned.split())
        raw_chars = len(raw_text)
        cleaned_chars = len(cleaned)

        reduction_pct = 0.0
        if raw_chars > 0:
            reduction_pct = round(((raw_chars - cleaned_chars) / raw_chars) * 100, 2)

        return {
            "source_name": doc_data.get("source_name", "Unknown"),
            "raw_text": raw_text,
            "cleaned_text": cleaned,
            "sections": sections,
            "section_df": df_sections,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "stats": {
                "raw_chars": raw_chars,
                "cleaned_chars": cleaned_chars,
                "raw_words": raw_words,
                "cleaned_words": cleaned_words,
                "reduction_pct": reduction_pct,
                "section_count": len(sections)
            }
        }

    @classmethod
    def display_preprocessing_summary(cls, preprocessed_data: Dict[str, Any]) -> None:
        """
        Neatly prints the preprocessing results and Pandas summary table.
        """
        stats = preprocessed_data["stats"]
        df: pd.DataFrame = preprocessed_data["section_df"]

        border = "=" * 68
        subborder = "-" * 68

        print("\n" + border)
        print("          PREPROCESSING & SECTION ANALYSIS (Part B - Q3)    ")
        print(border)
        print(f" Original Characters : {stats['raw_chars']:,}  -->  Cleaned: {stats['cleaned_chars']:,} ({stats['reduction_pct']}% cleaned)")
        print(f" Original Words      : {stats['raw_words']:,}  -->  Cleaned: {stats['cleaned_words']:,}")
        print(f" Identified Sections : {stats['section_count']}")
        print(f" Total Chunks        : {preprocessed_data['chunk_count']}")
        print(subborder)
        print(" DETECTED CONTRACT SECTIONS SUMMARY (via Pandas):")
        print(subborder)
        if not df.empty:
            print(df.to_string(index=False, columns=["Section_ID", "Title", "Words", "Snippet"]))
        else:
            print("   No distinct formal section headings detected.")
        print(border + "\n")
