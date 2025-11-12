"""
LLM Integration Module for CU Boulder Search

This module provides enhanced search functionality using local LLMs
through Ollama integration, with comprehensive result formatting
and source link extraction.

Components:
- setup_rag_system: Initialize RAG chain with embeddings and LLM
- format_sources: Format document sources for display
- prepare_context: Prepare context from retrieved documents
"""

from .enhanced_search import setup_rag_system, format_sources, prepare_context

__all__ = ['setup_rag_system', 'format_sources', 'prepare_context']
