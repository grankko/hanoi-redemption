"""
Core AI testing logic for Towers of Hanoi.

This module contains the HanoiAITester class which handles the core AI testing
functionality including move generation, validation, and context tracking.
"""

from typing import Optional

# Try absolute import first, fallback to relative
try:
    from src.api import HanoiAIClient, AIClientInterface
    from src.game import TowersOfHanoi
    from src.schemas import HanoiMove
    from src.display import TowerDisplay
except ImportError:
    from ..api import HanoiAIClient, AIClientInterface
    from ..game import TowersOfHanoi
    from ..schemas import HanoiMove
    from ..display import TowerDisplay


class HanoiAITester:
    """
    Core AI testing functionality for Towers of Hanoi puzzles.
    
    Handles AI initialization, move generation, validation, and context tracking.
    Supports dependency injection for different AI client implementations.
    """
    
    def __init__(self, num_disks: int, ai_client: Optional[AIClientInterface] = None):
        self.num_disks = num_disks
        self.game = TowersOfHanoi(num_disks)
        self.display = TowerDisplay(num_disks)
        self.ai_client = ai_client  # Use injected client if provided
        self.move_count = 0
        self.test_results = []
        self.recent_moves = []  # Track last 3 moves for context
        self.recent_states = []  # Track states corresponding to recent moves
        self.recent_reasoning = []  # Track AI reasoning for recent moves
        
    def initialize_ai(self) -> bool:
        """Initialize the AI client if not already provided via dependency injection."""
        # If a client was already injected, we're good to go
        if self.ai_client is not None:
            return True
            
        # Otherwise, initialize the default OpenAI client
        try:
            self.ai_client = HanoiAIClient()
            return True
        except ValueError as e:
            print(f"❌ Error initializing AI: {e}")
            print("Please create a .env file with your OpenAI API key:")
            print("OPENAI_API_KEY=your_api_key_here")
            return False
    
    def get_ai_move(self) -> Optional[tuple[HanoiMove, str]]:
        """Get the next move from AI."""
        try:
            # Create detailed state description for AI
            state_desc = self._create_ai_prompt()
            if self.ai_client is None:
                raise ValueError("AI client is not initialized.")
            response = self.ai_client.get_next_move(state_desc)
            return response.move, response.reasoning
        except Exception as e:
            print(f"❌ Error getting AI move: {e}")
            return None
    
    def _create_ai_prompt(self) -> str:
        """Create a detailed game state description for the AI with recent move and state context."""
        towers = self.game.state
        
        prompt = f"""{self.num_disks}-disk Towers of Hanoi puzzle - Turn #{self.move_count + 1}

CURRENT STATE:
Tower A: {towers.tower_a if towers.tower_a else 'empty'}
Tower B: {towers.tower_b if towers.tower_b else 'empty'}  
Tower C: {towers.tower_c if towers.tower_c else 'empty'}"""

        # Add recent moves, states, and reasoning context (last 3 moves)
        if self.recent_moves and self.recent_states and self.recent_reasoning:
            prompt += f"\n\nRECENT GAME HISTORY:"
            recent_moves_to_show = self.recent_moves[-3:]  # Get last 3 moves
            recent_states_to_show = self.recent_states[-3:]  # Get last 3 corresponding states
            recent_reasoning_to_show = self.recent_reasoning[-3:]  # Get last 3 reasoning explanations
            start_move_num = max(1, self.move_count - len(recent_moves_to_show) + 1)
            
            for i, (move, state_before, reasoning) in enumerate(zip(recent_moves_to_show, recent_states_to_show, recent_reasoning_to_show)):
                move_num = start_move_num + i
                prompt += f"\n\n--- Move {move_num} ---"
                prompt += f"\nState before move:"
                prompt += f"\n  Tower A: {state_before['tower_a'] if state_before['tower_a'] else 'empty'}"
                prompt += f"\n  Tower B: {state_before['tower_b'] if state_before['tower_b'] else 'empty'}"
                prompt += f"\n  Tower C: {state_before['tower_c'] if state_before['tower_c'] else 'empty'}"
                prompt += f"\nMove made: {move}"
                prompt += f"\nReasoning: {reasoning}"

        return prompt
    
    def validate_and_execute_move(self, ai_move: HanoiMove, ai_reasoning: str) -> tuple[bool, str]:
        """
        Validate and execute an AI move.
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        # Validate the move
        is_valid, error_msg = self.game.is_valid_move(ai_move)
        
        if is_valid:
            print("✅ AI move is VALID")
        else:
            print(f"❌ AI move is INVALID: {error_msg}")
            return False, error_msg
        
        # Record the result
        self.test_results.append({
            'turn': self.move_count + 1,
            'ai_move': {'source': ai_move.source_tower, 'destination': ai_move.destination_tower},
            'is_valid': is_valid,
            'ai_reasoning': ai_reasoning
        })
        
        # Execute the move if valid
        if is_valid:
            # Capture the current state BEFORE making the move
            state_before_move = {
                'tower_a': self.game.state.tower_a.copy(),
                'tower_b': self.game.state.tower_b.copy(),
                'tower_c': self.game.state.tower_c.copy()
            }
            
            success = self.game.make_move(ai_move)
            if success:
                self.move_count += 1
                
                # Track recent moves, states, and reasoning for context (keep last 3)
                self.recent_moves.append(ai_move)
                self.recent_states.append(state_before_move)
                self.recent_reasoning.append(ai_reasoning)
                
                # Keep only last 3 items in all lists
                if len(self.recent_moves) > 3:
                    self.recent_moves.pop(0)  # Remove oldest move
                    self.recent_states.pop(0)  # Remove oldest state
                    self.recent_reasoning.pop(0)  # Remove oldest reasoning
                
                # Display updated state
                self.display.display_towers([
                    self.game.state.tower_a,
                    self.game.state.tower_b,
                    self.game.state.tower_c
                ], self.move_count, pause=False)
                
                return True, "Move executed successfully"
            else:
                return False, "Failed to execute move"
        
        return False, "Invalid move"
    
    def is_solved(self) -> bool:
        """Check if the puzzle is solved."""
        return self.game.is_solved()
    
    def get_current_state(self) -> tuple[list[int], list[int], list[int]]:
        """Get the current tower states."""
        return (
            self.game.state.tower_a,
            self.game.state.tower_b,
            self.game.state.tower_c
        )
    
    def reset(self):
        """Reset the tester for a new test."""
        self.game = TowersOfHanoi(self.num_disks)
        self.move_count = 0
        self.test_results = []
        self.recent_moves = []
        self.recent_states = []
        self.recent_reasoning = []
