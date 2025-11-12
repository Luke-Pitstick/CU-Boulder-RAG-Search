"""
LLM Integration Module for CU Boulder Search

This module provides enhanced search functionality using local LLMs
through Ollama integration, with comprehensive result formatting
and source link extraction.

Components:
- EnhancedSearch: Main search class with LLM integration
- ResultFormatter: Multiple output format support
- SearchSession: Session management and history
"""

from .enhanced_search import EnhancedSearch
from .result_formatter import ResultFormatter, SearchSession

__all__ = ['EnhancedSearch', 'ResultFormatter', 'SearchSession']
