"""
API package for AI clients in Towers of Hanoi testing.
"""

# Try absolute import first, fallback to relative
try:
    from src.api.ai_client_interface import AIClientInterface
    from src.api.openai_client import HanoiAIClient
    from src.api.mock_ai_client import MockAIClient, MockMode
except ImportError:
    from .ai_client_interface import AIClientInterface
    from .openai_client import HanoiAIClient
    from .mock_ai_client import MockAIClient, MockMode

__all__ = ["AIClientInterface", "HanoiAIClient", "MockAIClient", "MockMode"]
