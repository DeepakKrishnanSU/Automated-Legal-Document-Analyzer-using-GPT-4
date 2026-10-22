"""
Input Module
------------
Course: 24CS2506 - Building Applications using GPT-4 (Experiment 5)
Handles legal document input (Part A - Q1) and neat document display (Part A - Q2).
Supports keyboard entry, TXT files, PDF files, and preset sample contracts.
"""

import os
from typing import Dict, Any, List
from modules.extraction_module import ExtractionModule


class InputModule:
    """Manages document ingestion and terminal presentation."""

    SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_contracts")

    @classmethod
    def list_sample_contracts(cls) -> List[str]:
        """Lists available sample contracts in sample_contracts directory."""
        if not os.path.exists(cls.SAMPLE_DIR):
            return []
        return [
            f for f in os.listdir(cls.SAMPLE_DIR)
            if f.endswith(".txt") or f.endswith(".pdf")
        ]

    @classmethod
    def load_document_from_path(cls, file_path: str) -> Dict[str, Any]:
        """Loads and extracts document from a given file path."""
        file_path = file_path.strip().strip('"').strip("'")
        if not os.path.isabs(file_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate = os.path.join(base_dir, file_path)
            if os.path.exists(candidate):
                file_path = candidate
        return ExtractionModule.extract_from_file(file_path)

    @classmethod
    def load_document_from_text(cls, text: str, label: str = "Manual Keyboard Input") -> Dict[str, Any]:
        """Wraps raw text input into the standard document dictionary."""
        return ExtractionModule.create_doc_from_raw_text(text, label)

    @classmethod
    def display_document_info(cls, doc_data: Dict[str, Any]) -> None:
        """
        Satisfies Part A - Q2: Displays document information neatly.
        """
        source = doc_data.get("source_name", "Unknown Source")
        doc_type = doc_data.get("file_type", "Unknown").upper()
        chars = doc_data.get("char_count", 0)
        words = doc_data.get("word_count", 0)
        pages = doc_data.get("page_count", 1)
        raw_text = doc_data.get("raw_text", "")

        preview = raw_text[:350].strip()
        if len(raw_text) > 350:
            preview += "\n... [Remaining content loaded into analyzer memory] ..."

        border = "=" * 64
        subborder = "-" * 64

        print("\n" + border)
        print("          LEGAL DOCUMENT INFORMATION (Part A - Q2)          ")
        print(border)
        print(f" Source Name       : {source}")
        print(f" File Format       : {doc_type}")
        print(f" Total Characters  : {chars:,}")
        print(f" Total Words       : {words:,}")
        print(f" Estimated Pages   : {pages}")
        print(subborder)
        print(" DOCUMENT PREVIEW:")
        print(subborder)
        for line in preview.splitlines():
            print(f"   {line}")
        print(border + "\n")

    @classmethod
    def prompt_user_input(cls) -> Dict[str, Any]:
        """
        Interactive CLI prompt to guide the user through selecting an input method.
        """
        print("\n" + "=" * 54)
        print("     SELECT LEGAL DOCUMENT INPUT METHOD (Part A - Q1)    ")
        print("=" * 54)
        print(" [1] Choose from sample contracts (sample_contracts/)")
        print(" [2] Enter local file path (.txt or .pdf)")
        print(" [3] Paste or type legal text directly via keyboard")
        print(" [4] Return to main menu")
        print("-" * 54)

        choice = input(" Enter your choice (1-4): ").strip()

        if choice == "1":
            samples = cls.list_sample_contracts()
            if not samples:
                print(" [!] No sample contracts found in sample_contracts/ directory.")
                return {}
            print("\n Available Sample Contracts:")
            for idx, s in enumerate(samples, 1):
                print(f"   [{idx}] {s}")
            s_choice = input(f" Select contract (1-{len(samples)}): ").strip()
            try:
                s_idx = int(s_choice) - 1
                if 0 <= s_idx < len(samples):
                    target_path = os.path.join(cls.SAMPLE_DIR, samples[s_idx])
                    doc = cls.load_document_from_path(target_path)
                    cls.display_document_info(doc)
                    return doc
                else:
                    print(" [!] Invalid selection.")
            except ValueError:
                print(" [!] Please enter a valid number.")

        elif choice == "2":
            path_input = input(" Enter path to .txt or .pdf file: ").strip()
            if not path_input:
                print(" [!] File path cannot be empty.")
                return {}
            try:
                doc = cls.load_document_from_path(path_input)
                cls.display_document_info(doc)
                return doc
            except Exception as e:
                print(f" [!] Error loading file: {e}")

        elif choice == "3":
            print("\n Enter/paste your legal contract below.")
            print(" (Type 'END_CONTRACT' on a new line when finished):")
            lines = []
            while True:
                line = input()
                if line.strip() == "END_CONTRACT":
                    break
                lines.append(line)
            full_text = "\n".join(lines).strip()
            if not full_text:
                print(" [!] Empty text entered.")
                return {}
            doc = cls.load_document_from_text(full_text)
            cls.display_document_info(doc)
            return doc

        elif choice == "4":
            return {}

        else:
            print(" [!] Invalid option selected.")

        return {}
