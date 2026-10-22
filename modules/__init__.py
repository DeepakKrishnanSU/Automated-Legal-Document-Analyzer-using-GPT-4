"""
Automated Legal Document Analyzer Modules
Course: 24CS2506 - Building Applications using GPT-4 (Experiment 5)
"""

from modules.input_module import InputModule
from modules.extraction_module import ExtractionModule
from modules.preprocessing_module import PreprocessingModule
from modules.prompt_module import PromptModule
from modules.summary_module import SummaryModule

__all__ = [
    "InputModule",
    "ExtractionModule",
    "PreprocessingModule",
    "PromptModule",
    "SummaryModule",
]

__version__ = "1.0.0"
