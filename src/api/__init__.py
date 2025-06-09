"""
API package for OpenAI interactions.
"""

# Try absolute import first, fallback to relative
try:
    from src.api.openai_client import HanoiAIClient
except ImportError:
    from .openai_client import HanoiAIClient

__all__ = ["HanoiAIClient"]
