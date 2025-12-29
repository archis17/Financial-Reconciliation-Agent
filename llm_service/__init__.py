"""
LLM Service Module.

This module provides LLM-based explanations for discrepancies.
Uses GPT-4o-mini for generating human-readable explanations.
"""

from .service import LLMExplanationService
from .prompts import PromptTemplates
from .models import ExplanationRequest, ExplanationResponse

__all__ = [
    "LLMExplanationService",
    "PromptTemplates",
    "ExplanationRequest",
    "ExplanationResponse",
]

