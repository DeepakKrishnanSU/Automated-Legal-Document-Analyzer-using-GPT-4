"""
================================================================================
Automated Legal Document Analyzer Using GPT-4 / Ollama
Course: 24CS2506 - Building Applications using GPT-4
Experiment 5
================================================================================
Core Application Entry Point (Part F - Q7)
Integrates:
- Part A: Input & Extraction Module (.txt, .pdf, keyboard, samples)
- Part B: Preprocessing Module (cleaning, normalization, section detection, Pandas summary)
- Part C: Prompt Generation Module (strict anti-hallucination guardrail)
- Part D: Legal Document Summarization (Ollama llama3.2 / qwen2.5 or OpenAI GPT-4)
- Part E: Report Export & Persistence (outputs/legal_analysis.txt)
- Part F: Complete Interactive Application (Console CLI & Web UI Server)
================================================================================
"""

import sys
import os
import json
import time
import argparse
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

# Ensure UTF-8 output encoding across Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules import (
    InputModule,
    ExtractionModule,
    PreprocessingModule,
    PromptModule,
    SummaryModule,
)


class ApplicationState:
    """Manages the current state of loaded documents and generated analyses."""

    def __init__(self):
        self.current_doc: Optional[Dict[str, Any]] = None
        self.preprocessed_data: Optional[Dict[str, Any]] = None
        self.prompt_data: Optional[Dict[str, str]] = None
        self.analysis_result: Optional[Dict[str, Any]] = None
        self.summary_engine = SummaryModule()

    def reset(self):
        self.current_doc = None
        self.preprocessed_data = None
        self.prompt_data = None
        self.analysis_result = None

    def has_document(self) -> bool:
        return self.current_doc is not None and bool(self.current_doc.get("raw_text"))

    def has_analysis(self) -> bool:
        return self.analysis_result is not None and bool(self.analysis_result.get("formatted_report"))


# Global shared state for CLI and Web Server
APP_STATE = ApplicationState()


# ==============================================================================
# CLI Interactive Interface (Part F - Q7)
# ==============================================================================

def print_banner():
    banner = """
======================================================================
  AUTOMATED LEGAL DOCUMENT ANALYZER (Experiment 5 - 24CS2506)
  Powered by Local LLM (Ollama) & Advanced Document Processing
======================================================================
"""
    print(banner)


def print_main_menu(state: ApplicationState):
    status_doc = state.current_doc["source_name"] if state.has_document() else "No document loaded"
    status_analysis = "Ready" if state.has_analysis() else "Not performed"

    print("-" * 70)
    print(f" Current Document : {status_doc}")
    print(f" Analysis Status  : {status_analysis}")
    print("-" * 70)
    print(" APPLICATION MENU (Part F - Q7):")
    print("  [1] Upload / Enter Legal Document (Part A - Q1 & Q2)")
    print("  [2] Analyze Document & Extract Sections (Part B - Q3)")
    print("  [3] Generate Summary & Legal Analysis (Part C & D - Q4 & Q5)")
    print("  [4] Save Report to File (Part E - Q6)")
    print("  [5] Launch Modern Web UI in Browser")
    print("  [6] Reset Application State")
    print("  [7] Exit Application")
    print("-" * 70)


def handle_upload_document(state: ApplicationState):
    """Step 1: Upload or enter legal document (Part A)."""
    doc = InputModule.prompt_user_input()
    if doc and doc.get("raw_text"):
        state.current_doc = doc
        # Automatically clear stale downstream analysis
        state.preprocessed_data = None
        state.prompt_data = None
        state.analysis_result = None
        print(f"\n [+] Successfully loaded document: '{doc['source_name']}'")
    else:
        print("\n [!] No document was loaded.")


def handle_preprocess_document(state: ApplicationState):
    """Step 2: Preprocess document and identify sections (Part B)."""
    if not state.has_document():
        print("\n [!] Please load a document first (Option 1).")
        return

    print("\n [*] Preprocessing document (cleaning whitespace, identifying clauses)...")
    preprocessed = PreprocessingModule.preprocess_document(state.current_doc)
    state.preprocessed_data = preprocessed

    # Construct the prompt immediately for inspection
    prompt_data = PromptModule.build_legal_analysis_prompt(
        preprocessed["cleaned_text"],
        state.current_doc.get("source_name", "Legal Contract")
    )
    state.prompt_data = prompt_data

    # Display results neatly
    PreprocessingModule.display_preprocessing_summary(preprocessed)
    print(" [+] Preprocessing complete. Sections detected and prompt constructed.")


def handle_generate_summary(state: ApplicationState):
    """Step 3: Generate summary and structured extraction via LLM (Part C & D)."""
    if not state.has_document():
        print("\n [!] Please load a document first (Option 1).")
        return

    if state.preprocessed_data is None:
        print("\n [*] Automatically running preprocessing first...")
        handle_preprocess_document(state)

    # Show prompt preview (Part C - Q4)
    print("\n [*] Reviewing prompt before LLM inference (Part C - Q4)...")
    PromptModule.display_prompt(state.prompt_data, max_preview_chars=500)

    # Check health of LLM
    healthy, msg = state.summary_engine.check_health()
    if not healthy:
        print(f"\n [!] LLM Backend Warning: {msg}")
        print(" [!] Please ensure Ollama is running ('ollama serve' or start Ollama app).")
        proceed = input(" Do you want to attempt inference anyway? (y/N): ").strip().lower()
        if proceed != "y":
            return

    print(f"\n [*] Sending document to LLM for structured legal analysis...")
    print(f" [*] Model: {state.summary_engine.ollama_model} (Provider: {state.summary_engine.provider})")
    print(" [*] Please wait a few seconds for inference to complete...")

    try:
        analysis = state.summary_engine.analyze_document(
            state.preprocessed_data["cleaned_text"],
            state.current_doc.get("source_name", "Legal Contract")
        )
        state.analysis_result = analysis
        SummaryModule.display_analysis_result(analysis)
        print(f" [+] Legal analysis successfully completed in {analysis['execution_time_sec']}s!")
    except Exception as e:
        print(f"\n [!] Error during LLM summarization: {e}")


def handle_save_report(state: ApplicationState):
    """Step 4: Save analysis report to file (Part E - Q6)."""
    if not state.has_analysis():
        print("\n [!] No analysis has been generated yet. Please run Option 3 first.")
        return

    default_output = os.path.join(BASE_DIR, "outputs", "legal_analysis.txt")
    print(f"\n [*] Default output path: {default_output}")
    custom_path = input(" Press ENTER to use default path, or enter custom path: ").strip()
    target_path = custom_path if custom_path else default_output

    try:
        saved_file = SummaryModule.save_analysis_report(
            state.analysis_result["formatted_report"],
            target_path
        )
        print(f"\n [+] Legal analysis report successfully saved to:\n     {saved_file}")
    except Exception as e:
        print(f"\n [!] Failed to save report: {e}")


def run_cli_loop():
    """Main interactive terminal loop satisfying Part F (Q7)."""
    print_banner()

    # Initial backend check
    healthy, msg = APP_STATE.summary_engine.check_health()
    if healthy:
        print(f" [+] LLM Backend Status: Active ({msg})")
    else:
        print(f" [!] LLM Backend Notice: {msg}")

    while True:
        try:
            print_main_menu(APP_STATE)
            choice = input(" Select an option (1-7): ").strip()

            if choice == "1":
                handle_upload_document(APP_STATE)
            elif choice == "2":
                handle_preprocess_document(APP_STATE)
            elif choice == "3":
                handle_generate_summary(APP_STATE)
            elif choice == "4":
                handle_save_report(APP_STATE)
            elif choice == "5":
                print("\n [*] Launching Web UI server...")
                launch_web_server(port=8080, open_browser=True)
            elif choice == "6":
                APP_STATE.reset()
                print("\n [+] Application state has been reset.")
            elif choice == "7":
                print("\n Thank you for using Automated Legal Document Analyzer. Exiting.\n")
                sys.exit(0)
            else:
                print("\n [!] Invalid selection. Please enter a number between 1 and 7.")

            input("\n Press ENTER to return to menu...")
        except KeyboardInterrupt:
            print("\n\n Program interrupted by user. Exiting.")
            sys.exit(0)


# ==============================================================================
# Web Application Server & REST API
# ==============================================================================

class LegalAnalyzerHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Serves the frontend static files and handles JSON API requests."""

    def __init__(self, *args, **kwargs):
        frontend_dir = os.path.join(BASE_DIR, "frontend")
        super().__init__(*args, directory=frontend_dir, **kwargs)

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            healthy, msg = APP_STATE.summary_engine.check_health()
            self._send_json({
                "healthy": healthy,
                "message": msg,
                "provider": APP_STATE.summary_engine.provider,
                "model": APP_STATE.summary_engine.ollama_model,
                "has_document": APP_STATE.has_document(),
                "document_name": APP_STATE.current_doc.get("source_name") if APP_STATE.has_document() else None,
                "has_analysis": APP_STATE.has_analysis()
            })
            return

        elif path == "/api/samples":
            samples = InputModule.list_sample_contracts()
            self._send_json({"samples": samples})
            return

        # Serve frontend static files
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if path == "/api/load-sample":
            sample_name = payload.get("sample_name", "")
            target_path = os.path.join(BASE_DIR, "sample_contracts", sample_name)
            try:
                doc = ExtractionModule.extract_from_file(target_path)
                APP_STATE.current_doc = doc
                APP_STATE.preprocessed_data = None
                APP_STATE.analysis_result = None
                self._send_json({"success": True, "document": doc})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        elif path == "/api/load-text":
            raw_text = payload.get("text", "")
            title = payload.get("title", "Manual Input Contract")
            if not raw_text.strip():
                self._send_json({"success": False, "error": "Empty text provided"}, status=400)
                return
            doc = ExtractionModule.create_doc_from_raw_text(raw_text, title)
            APP_STATE.current_doc = doc
            APP_STATE.preprocessed_data = None
            APP_STATE.analysis_result = None
            self._send_json({"success": True, "document": doc})
            return

        elif path == "/api/preprocess":
            if not APP_STATE.has_document():
                self._send_json({"success": False, "error": "No document loaded"}, status=400)
                return

            try:
                preprocessed = PreprocessingModule.preprocess_document(APP_STATE.current_doc)
                APP_STATE.preprocessed_data = preprocessed
                prompt_data = PromptModule.build_legal_analysis_prompt(
                    preprocessed["cleaned_text"],
                    APP_STATE.current_doc.get("source_name", "Contract")
                )
                APP_STATE.prompt_data = prompt_data

                sections_list = [
                    {"id": s["Section_ID"], "title": s["Title"], "words": s["Words"], "snippet": s["Snippet"]}
                    for _, s in preprocessed["section_df"].iterrows()
                ]

                self._send_json({
                    "success": True,
                    "stats": preprocessed["stats"],
                    "sections": sections_list,
                    "chunk_count": preprocessed["chunk_count"],
                    "cleaned_text": preprocessed["cleaned_text"],
                    "prompt": prompt_data
                })
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        elif path == "/api/analyze":
            if not APP_STATE.has_document():
                self._send_json({"success": False, "error": "No document loaded"}, status=400)
                return

            if APP_STATE.preprocessed_data is None:
                APP_STATE.preprocessed_data = PreprocessingModule.preprocess_document(APP_STATE.current_doc)
                APP_STATE.prompt_data = PromptModule.build_legal_analysis_prompt(
                    APP_STATE.preprocessed_data["cleaned_text"],
                    APP_STATE.current_doc.get("source_name", "Contract")
                )

            try:
                result = APP_STATE.summary_engine.analyze_document(
                    APP_STATE.preprocessed_data["cleaned_text"],
                    APP_STATE.current_doc.get("source_name", "Contract")
                )
                APP_STATE.analysis_result = result
                self._send_json({"success": True, "analysis": result})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        elif path == "/api/save-report":
            if not APP_STATE.has_analysis():
                self._send_json({"success": False, "error": "No analysis available to save"}, status=400)
                return

            custom_path = payload.get("path", "")
            target_path = custom_path if custom_path else os.path.join(BASE_DIR, "outputs", "legal_analysis.txt")
            try:
                saved = SummaryModule.save_analysis_report(
                    APP_STATE.analysis_result["formatted_report"],
                    target_path
                )
                self._send_json({"success": True, "saved_path": saved})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        self.send_error(404, "Endpoint not found")


def launch_web_server(port: int = 8080, open_browser: bool = True):
    """Starts the built-in HTTP server to serve the frontend web dashboard."""
    server_address = ("127.0.0.1", port)
    try:
        httpd = HTTPServer(server_address, LegalAnalyzerHTTPRequestHandler)
        url = f"http://localhost:{port}"
        print(f"\n [+] Web Dashboard server running at: {url}")
        print(" [*] Press Ctrl+C in this terminal to stop the web server.\n")

        if open_browser:
            webbrowser.open(url)

        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n [!] Web server stopped.")
    except Exception as e:
        print(f"\n [!] Failed to start web server on port {port}: {e}")


# ==============================================================================
# Entry Point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Automated Legal Document Analyzer Using GPT-4 / Ollama (Experiment 5)"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Directly launch the modern Web UI dashboard"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to use for the Web UI server (default: 8080)"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Directly run CLI analysis on a specific document file"
    )

    args = parser.parse_args()

    if args.web:
        launch_web_server(port=args.port, open_browser=True)
    elif args.file:
        print_banner()
        print(f" [*] Processing document from command line: {args.file}")
        doc = InputModule.load_document_from_path(args.file)
        InputModule.display_document_info(doc)
        preprocessed = PreprocessingModule.preprocess_document(doc)
        PreprocessingModule.display_preprocessing_summary(preprocessed)
        prompt_data = PromptModule.build_legal_analysis_prompt(preprocessed["cleaned_text"], doc["source_name"])
        PromptModule.display_prompt(prompt_data)
        sm = SummaryModule()
        result = sm.analyze_document(preprocessed["cleaned_text"], doc["source_name"])
        SummaryModule.display_analysis_result(result)
        saved = SummaryModule.save_analysis_report(result["formatted_report"])
        print(f" [+] Analysis finished and saved to: {saved}")
    else:
        run_cli_loop()


if __name__ == "__main__":
    main()
