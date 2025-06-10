"""
OpenAI client and API interactions for Towers of Hanoi.
"""

import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Try absolute import first, fallback to relative
try:
    from src.schemas import HanoiMoveResponse
except ImportError:
    from ..schemas import HanoiMoveResponse


class HanoiAIClient:
    """
    Client for interacting with OpenAI API to get Towers of Hanoi moves.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, will load from environment.
        """
        # Load environment variables
        load_dotenv()
        
        # Use provided key or get from environment
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "o4-mini-2025-04-16"
    
    def get_next_move(self, game_state_description: str) -> HanoiMoveResponse:
        """
        Get the next move suggestion from OpenAI using structured outputs.
        
        Args:
            game_state_description: Description of the current game state
            
        Returns:
            HanoiMoveResponse with the suggested move and reasoning
        """
        system_prompt = """You are an expert at solving the Towers of Hanoi puzzle. 

Your task is to analyze the current game state and suggest the next optimal move.

RULES:
1. Only move one disk at a time
2. Only move the top disk from a tower
3. Never place a larger disk on top of a smaller disk
4. The goal is to move all disks to tower C

STRATEGY:
Think strategically about the optimal sequence of moves to solve the puzzle efficiently. Consider the recursive nature of the problem and plan several moves ahead to ensure you're working toward the optimal solution.

IMPORTANT: If you see previous game states in the context, avoid making moves that would return the game to a previous state. Cycling back to earlier configurations is a clear sign of inefficient problem-solving and should be avoided to maintain optimal progress.

RESPONSE:
Provide your next move suggestion along with clear reasoning explaining why this move is optimal for the current game state."""

        user_prompt = game_state_description

        try:
            response = self.client.responses.parse(
                model=self.model,
                reasoning={"effort": "medium"},
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                text_format=HanoiMoveResponse
            )
            
            parsed_move = response.output_parsed
            if parsed_move is None:
                raise RuntimeError("OpenAI did not return a valid move.")
            return parsed_move
            
        except Exception as e:
            raise RuntimeError(f"Failed to get move from OpenAI: {str(e)}")
    