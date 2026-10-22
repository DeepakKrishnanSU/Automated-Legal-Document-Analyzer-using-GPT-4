"""
Prompt Module
-------------
Course: 24CS2506 - Building Applications using GPT-4 (Experiment 5)
Implements Part C (Q4): GPT-4 Prompt Construction.
Constructs a structured prompt instructing the model to analyze the legal document,
with strict zero-hallucination guardrails and formatted output requirements.
"""

from typing import Dict, Any


class PromptModule:
    """Builds structured legal analysis prompts for GPT-4 / Ollama."""

    SYSTEM_ROLE = (
        "You are an expert legal document analysis assistant. "
        "Your task is to analyze contracts, extract critical information, "
        "and produce structured legal summaries. "
        "You adhere to strict factual accuracy based solely on the provided contract."
    )

    ANTI_HALLUCINATION_GUARDRAIL = (
        "CRITICAL CONSTRAINT:\n"
        "- Do NOT invent, assume, or extrapolate facts or details.\n"
        "- If any piece of information is not explicitly mentioned or cannot be inferred with certainty from the text, "
        'you MUST explicitly write: "Not mentioned in the document."\n'
        "- Rely exclusively on the provided contract text."
    )

    TARGET_OUTPUT_FORMAT = """LEGAL DOCUMENT ANALYSIS
--------------------------------

Document Type:
[e.g., Non-Disclosure Agreement / Employment Agreement / Service Agreement / etc.]

Parties:
[List all parties involved, including disclosers, recipients, employers, contractors, etc.]

Purpose:
[Concise description of the objective, scope, or background of the agreement]

Duration:
[Term of the contract, renewal terms, and survival clauses if any]

Key Obligations:
• [Obligation 1]
• [Obligation 2]
• [Additional obligations...]

Payment Terms:
[Financial terms, salary, rates, retainer, payment schedule, penalties, or 'No monetary payment required']

Termination Conditions:
[Notice periods, termination for convenience, termination for cause/breach, post-termination duties]

Important Dates:
• Effective / Start Date: [Date]
• Expiration / Milestone Dates: [Dates if mentioned]
• Notice Periods / Deadlines: [Periods if mentioned]

Potentially Important Clauses:
• [Clause name]: [Brief 1-sentence significance]
• [Clause name]: [Brief 1-sentence significance]
• [Additional clauses...]

Summary:
[A clear, concise 2-4 sentence executive abstract of the entire legal document]"""

    @classmethod
    def build_legal_analysis_prompt(cls, legal_text: str, document_title: str = "Legal Document") -> Dict[str, str]:
        """
        Constructs the comprehensive legal document analysis prompt fulfilling Part C (Q4).
        """
        user_prompt = f"""You are analyzing the legal document: "{document_title}".

Please examine the text below carefully and extract the requested legal details.

{cls.ANTI_HALLUCINATION_GUARDRAIL}

### REQUIRED OUTPUT FORMAT:
You MUST structure your entire response using the exact headings and structure below:

{cls.TARGET_OUTPUT_FORMAT}

==================================================
LEGAL CONTRACT TEXT FOR ANALYSIS:
==================================================
{legal_text}
==================================================

Generate your complete structured analysis below according to the required format:"""

        return {
            "system_prompt": cls.SYSTEM_ROLE,
            "user_prompt": user_prompt,
            "full_prompt": f"SYSTEM:\n{cls.SYSTEM_ROLE}\n\nUSER:\n{user_prompt}"
        }

    @classmethod
    def build_chunk_prompt(cls, chunk_text: str, chunk_id: int, total_chunks: int) -> Dict[str, str]:
        """
        Constructs a prompt for analyzing an individual chunk of a multi-part long contract.
        """
        user_prompt = f"""You are analyzing Chunk {chunk_id} of {total_chunks} of a long legal document.

{cls.ANTI_HALLUCINATION_GUARDRAIL}

Extract any explicit references to parties, obligations, payments, termination, dates, or key clauses from this chunk:

--- CHUNK TEXT ---
{chunk_text}
--- END CHUNK ---

Provide bullet points of all legal facts found in this chunk:"""

        return {
            "system_prompt": cls.SYSTEM_ROLE,
            "user_prompt": user_prompt,
            "full_prompt": f"SYSTEM:\n{cls.SYSTEM_ROLE}\n\nUSER:\n{user_prompt}"
        }

    @classmethod
    def display_prompt(cls, prompt_dict: Dict[str, str], max_preview_chars: int = 700) -> None:
        """
        Neatly prints the constructed prompt for demonstration and record screenshot capture.
        """
        border = "=" * 68
        subborder = "-" * 68

        user_content = prompt_dict["user_prompt"]
        preview = user_content[:max_preview_chars].strip()
        if len(user_content) > max_preview_chars:
            preview += "\n... [Full Contract Text Injected Here] ..."

        print("\n" + border)
        print("          PROMPT GENERATION MODULE (Part C - Q4)            ")
        print(border)
        print(" SYSTEM ROLE:")
        print(f"   {prompt_dict['system_prompt']}")
        print(subborder)
        print(" CONSTRUCTED USER PROMPT PREVIEW:")
        print(subborder)
        for line in preview.splitlines():
            print(f"   {line}")
        print(border + "\n")
