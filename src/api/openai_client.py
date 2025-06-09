"""
OpenAI client and API interactions for Towers of Hanoi.
"""

import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Try absolute import first, fallback to relative
try:
    from src.schemas import HanoiMoveResponse, HanoiGameState
except ImportError:
    from ..schemas import HanoiMoveResponse, HanoiGameState


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
        self.model = "gpt-4o-2024-08-06"  # Model that supports structured outputs
    
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
Always follow the rules:
1. Only move one disk at a time
2. Only move the top disk from a tower
3. Never place a larger disk on top of a smaller disk
4. The goal is to move all disks to tower C

Think strategically about the optimal sequence of moves to solve the puzzle efficiently."""

        user_prompt = f"""Analyze this Towers of Hanoi game state and suggest the next move:

{game_state_description}

Please provide your next move suggestion along with your reasoning."""

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=HanoiMoveResponse,
                temperature=0.1  # Low temperature for consistent, logical moves
            )
            
            parsed_move = completion.choices[0].message.parsed
            if parsed_move is None:
                raise RuntimeError("OpenAI did not return a valid move.")
            return parsed_move
            
        except Exception as e:
            raise RuntimeError(f"Failed to get move from OpenAI: {str(e)}")
    
    def get_solution_sequence(self, num_disks: int) -> list[HanoiMoveResponse]:
        """
        Get a complete solution sequence for a Towers of Hanoi puzzle.
        
        Args:
            num_disks: Number of disks in the puzzle
            
        Returns:
            List of HanoiMoveResponse objects representing the complete solution
        """
        system_prompt = f"""You are an expert at solving the Towers of Hanoi puzzle.

Generate the complete sequence of moves to solve a {num_disks}-disk Towers of Hanoi puzzle.
Initial state: All disks are on tower A, arranged from smallest (1) on top to largest ({num_disks}) on bottom.
Goal: Move all disks to tower C following the rules.

Rules:
1. Only move one disk at a time
2. Only move the top disk from a tower  
3. Never place a larger disk on top of a smaller disk

Provide each move in the sequence with reasoning."""

        user_prompt = f"Generate the complete solution for a {num_disks}-disk Towers of Hanoi puzzle."

        try:
            # For now, we'll get one move at a time
            # This could be enhanced to get the full sequence in one call
            # by creating a response format that includes a list of moves
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=HanoiMoveResponse,
                temperature=0.1
            )
            
            # For now, return single move - can be enhanced later
            parsed_move = completion.choices[0].message.parsed
            if parsed_move is None:
                raise RuntimeError("OpenAI did not return a valid move.")
            return [parsed_move]
            
        except Exception as e:
            raise RuntimeError(f"Failed to get solution from OpenAI: {str(e)}")
