"""
Abstract interface for AI clients in Towers of Hanoi testing.

This module defines the contract that all AI clients (real and mock) must implement.
"""

from abc import ABC, abstractmethod

# Try absolute import first, fallback to relative
try:
    from src.schemas import HanoiMoveResponse
except ImportError:
    from ..schemas import HanoiMoveResponse


class AIClientInterface(ABC):
    """
    Abstract interface for AI clients that can suggest Towers of Hanoi moves.
    
    This interface ensures consistent behavior between real AI clients (OpenAI)
    and mock clients for testing purposes.
    """
    
    @abstractmethod
    def get_next_move(self, game_state_description: str) -> HanoiMoveResponse:
        """
        Get the next move suggestion from the AI client.
        
        Args:
            game_state_description: Description of the current game state
            
        Returns:
            HanoiMoveResponse with the suggested move and reasoning
            
        Raises:
            Exception: If move generation fails
        """
        pass
