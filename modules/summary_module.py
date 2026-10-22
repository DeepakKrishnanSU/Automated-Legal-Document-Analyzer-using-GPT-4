"""
Summary Module
--------------
Course: 24CS2506 - Building Applications using GPT-4 (Experiment 5)
Implements:
- Part D (Q5): Legal Document Summarization & Structured Analysis via LLM
- Part E (Q6): Saving analysis report to file (e.g. outputs/legal_analysis.txt)
Supports local Ollama (llama3.2 / qwen2.5) as primary engine and optional OpenAI GPT-4.
"""

import os
import re
import time
from typing import Dict, Any, Tuple
import requests
from dotenv import load_dotenv

from modules.prompt_module import PromptModule

# Load environment configuration
load_dotenv(override=True)


class SummaryModule:
    """Manages LLM connection, contract summarization, structured extraction, and report saving."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def check_health(self) -> Tuple[bool, str]:
        """Verifies connectivity to the configured LLM backend."""
        if self.provider == "ollama":
            try:
                res = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    return True, f"Ollama is running at {self.ollama_host}. Available models: {', '.join(models)}"
                return False, f"Ollama returned HTTP status {res.status_code}"
            except Exception as e:
                return False, f"Could not reach Ollama at {self.ollama_host}: {str(e)}"
        elif self.provider == "openai":
            if not self.openai_key:
                return False, "OpenAI API key is missing in .env (OPENAI_API_KEY)"
            return True, f"OpenAI configured with model {self.openai_model}"
        return False, f"Unknown LLM provider '{self.provider}'"

    def _call_ollama(self, prompt_dict: Dict[str, str], timeout_sec: int = 180) -> str:
        """Sends prompt to local Ollama instance via REST API."""
        url = f"{self.ollama_host}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": prompt_dict["system_prompt"]},
                {"role": "user", "content": prompt_dict["user_prompt"]}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for strict factual accuracy
                "top_p": 0.9
            }
        }

        response = requests.post(url, json=payload, timeout=timeout_sec)
        if response.status_code != 200:
            raise RuntimeError(f"Ollama error ({response.status_code}): {response.text}")

        data = response.json()
        message = data.get("message", {})
        return message.get("content", "").strip()

    def _call_openai(self, prompt_dict: Dict[str, str]) -> str:
        """Sends prompt to OpenAI API (optional cloud fallback)."""
        try:
            import importlib
            openai_pkg = importlib.import_module("openai")
            client = openai_pkg.OpenAI(api_key=self.openai_key)
            completion = client.chat.completions.create(
                model=self.openai_model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": prompt_dict["system_prompt"]},
                    {"role": "user", "content": prompt_dict["user_prompt"]}
                ]
            )
            return completion.choices[0].message.content.strip()
        except ImportError:
            raise RuntimeError(
                "The 'openai' package is not installed. To use OpenAI GPT-4, run 'pip install openai'. "
                "Alternatively, keep LLM_PROVIDER=ollama (default) to run completely free and locally."
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")

    @staticmethod
    def parse_structured_sections(raw_llm_response: str) -> Dict[str, str]:
        """
        Parses headings from the LLM output into discrete structured fields.
        """
        headings = [
            "Document Type",
            "Parties",
            "Purpose",
            "Duration",
            "Key Obligations",
            "Payment Terms",
            "Termination Conditions",
            "Important Dates",
            "Potentially Important Clauses",
            "Summary"
        ]

        extracted = {}
        for h in headings:
            extracted[h] = "Not mentioned in the document."

        # Case-insensitive section splitter
        pattern = r"(?i)^(?:#{1,3}\s*)?(" + "|".join(re.escape(h) for h in headings) + r")(?:\s*:|\s*\n)"
        matches = list(re.finditer(pattern, raw_llm_response, re.MULTILINE))

        if not matches:
            # Fallback if standard format was slightly altered
            extracted["Summary"] = raw_llm_response
            return extracted

        for i in range(len(matches)):
            header_raw = matches[i].group(1)
            start_pos = matches[i].end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_llm_response)

            content = raw_llm_response[start_pos:end_pos].strip()

            # Match to standard key
            for standard_h in headings:
                if standard_h.lower() == header_raw.lower():
                    extracted[standard_h] = content
                    break

        return extracted

    def analyze_document(self, cleaned_text: str, document_title: str = "Legal Document") -> Dict[str, Any]:
        """
        Executes full analysis pipeline: prompt building, inference, structured parsing, timing.
        """
        prompt_dict = PromptModule.build_legal_analysis_prompt(cleaned_text, document_title)

        start_time = time.time()
        raw_response = ""
        model_name = ""

        if self.provider == "ollama":
            model_name = f"Ollama ({self.ollama_model})"
            raw_response = self._call_ollama(prompt_dict)
        elif self.provider == "openai":
            model_name = f"OpenAI ({self.openai_model})"
            raw_response = self._call_openai(prompt_dict)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        elapsed_seconds = round(time.time() - start_time, 2)
        parsed_fields = self.parse_structured_sections(raw_response)

        # Standard formatted report
        formatted_report = (
            f"LEGAL DOCUMENT ANALYSIS REPORT\n"
            f"Generated via: {model_name}\n"
            f"Execution Time: {elapsed_seconds} seconds\n"
            f"{'=' * 60}\n\n"
            f"{raw_response}\n\n"
            f"{'=' * 60}\n"
            f"Report generated automatically by Automated Legal Document Analyzer.\n"
        )

        return {
            "document_title": document_title,
            "provider": self.provider,
            "model_used": model_name,
            "execution_time_sec": elapsed_seconds,
            "raw_response": raw_response,
            "parsed_fields": parsed_fields,
            "formatted_report": formatted_report,
            "prompt_used": prompt_dict
        }

    @staticmethod
    def save_analysis_report(
        formatted_report: str,
        output_path: str = "outputs/legal_analysis.txt"
    ) -> str:
        """
        Implements Part E (Q6): Saves the generated analysis to a file.
        """
        # Resolve path relative to project root if relative
        if not os.path.isabs(output_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_path = os.path.join(base_dir, output_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_report)

        return os.path.abspath(output_path)

    @classmethod
    def display_analysis_result(cls, analysis_data: Dict[str, Any]) -> None:
        """
        Neatly prints the generated analysis for terminal users and report screenshot capture.
        """
        border = "=" * 68
        subborder = "-" * 68

        print("\n" + border)
        print("          LEGAL DOCUMENT SUMMARY & ANALYSIS (Part D - Q5)   ")
        print(border)
        print(f" Analyzed Document : {analysis_data.get('document_title', 'Contract')}")
        print(f" Engine Used       : {analysis_data.get('model_used', 'LLM')}")
        print(f" Inference Time    : {analysis_data.get('execution_time_sec', 0.0)} seconds")
        print(subborder)
        print(analysis_data.get("raw_response", ""))
        print(border + "\n")
