"""
Mock AI client for Towers of Hanoi testing.

This module provides a mock AI client that can simulate different behaviors
for testing purposes without requiring external API calls.
"""

from enum import Enum
from typing import List, Optional

# Try absolute import first, fallback to relative
try:
    from src.schemas import HanoiMove, HanoiMoveResponse
    from src.game import OptimalSolver
    from src.api.ai_client_interface import AIClientInterface
except ImportError:
    from ..schemas import HanoiMove, HanoiMoveResponse
    from ..game import OptimalSolver
    from .ai_client_interface import AIClientInterface


class MockMode(Enum):
    """Enumeration of different mock AI behaviors."""
    OPTIMAL_SOLVER = "optimal"
    INVALID_MOVE = "invalid-move"
    BUDGET_EXCEEDED = "budget-exceeded"


class MockAIClient(AIClientInterface):
    """
    Mock AI client that provides predictable, configurable behaviors for testing.
    
    This client can simulate different scenarios including optimal play,
    invalid moves, and budget-exceeding behavior without external dependencies.
    """
    
    def __init__(self, mode: MockMode, num_disks: int, invalid_at_turn: int = 3):
        """
        Initialize the mock AI client.
        
        Args:
            mode: The simulation mode to use
            num_disks: Number of disks in the puzzle
            invalid_at_turn: Turn number to make invalid move (for INVALID_MOVE mode)
        """
        self.mode = mode
        self.num_disks = num_disks
        self.invalid_at_turn = invalid_at_turn
        self.turn_count = 0
        self.optimal_moves: List[HanoiMove] = []
        self.inefficient_moves: List[HanoiMove] = []
        
        # Pre-generate move sequences based on mode
        self._prepare_moves()
    
    def _prepare_moves(self):
        """Prepare move sequences based on the selected mode."""
        if self.mode in [MockMode.OPTIMAL_SOLVER, MockMode.INVALID_MOVE]:
            # Generate optimal solution
            solver = OptimalSolver(self.num_disks)
            self.optimal_moves = solver.solve()
        
        elif self.mode == MockMode.BUDGET_EXCEEDED:
            # Generate inefficient moves (cycles and suboptimal paths)
            self._generate_inefficient_moves()
    
    def _generate_inefficient_moves(self):
        """Generate an inefficient move sequence that will exceed budget."""
        # Calculate the actual budget for this number of disks
        optimal_moves = (2 ** self.num_disks) - 1
        budget = optimal_moves * 2
        
        # Generate enough moves to exceed the budget by a small margin
        target_moves = budget + 5  # Exceed by 5 moves to ensure budget failure
        
        # Create basic cycling pattern for disk 1
        basic_cycle = [
            HanoiMove(source_tower="A", destination_tower="B"),  # Move disk 1
            HanoiMove(source_tower="B", destination_tower="C"),  # Move disk 1
            HanoiMove(source_tower="C", destination_tower="A"),  # Move disk 1 back to start
        ]
        
        # Alternative cycling patterns to add variety
        alt_cycle_1 = [
            HanoiMove(source_tower="A", destination_tower="C"),  # Move disk 1
            HanoiMove(source_tower="C", destination_tower="B"),  # Move disk 1
            HanoiMove(source_tower="B", destination_tower="A"),  # Move disk 1 back
        ]
        
        alt_cycle_2 = [
            HanoiMove(source_tower="A", destination_tower="B"),  # Move disk 1
            HanoiMove(source_tower="B", destination_tower="A"),  # Move disk 1 back immediately
        ]
        
        # Build the inefficient move sequence
        self.inefficient_moves = []
        
        while len(self.inefficient_moves) < target_moves:
            remaining = target_moves - len(self.inefficient_moves)
            
            if remaining >= 6:
                # Add a full 6-move cycle (there and back)
                self.inefficient_moves.extend([
                    HanoiMove(source_tower="A", destination_tower="B"),
                    HanoiMove(source_tower="B", destination_tower="C"),
                    HanoiMove(source_tower="C", destination_tower="A"),
                    HanoiMove(source_tower="A", destination_tower="C"),
                    HanoiMove(source_tower="C", destination_tower="B"),
                    HanoiMove(source_tower="B", destination_tower="A"),
                ])
            elif remaining >= 3:
                # Add a basic 3-move cycle
                self.inefficient_moves.extend(basic_cycle[:remaining])
            elif remaining >= 2:
                # Add a 2-move back-and-forth
                self.inefficient_moves.extend(alt_cycle_2[:remaining])
            else:
                # Add single moves to reach exact target
                self.inefficient_moves.append(HanoiMove(source_tower="A", destination_tower="B"))
        
        print(f"🔧 Mock: Generated {len(self.inefficient_moves)} inefficient moves for {self.num_disks} disks (budget: {budget})")
        print(f"🎯 Mock: Will exceed budget by {len(self.inefficient_moves) - budget} moves")
    
    def get_next_move(self, game_state_description: str) -> HanoiMoveResponse:
        """
        Get the next move based on the configured mode.
        
        Args:
            game_state_description: Description of the current game state
            
        Returns:
            HanoiMoveResponse with the suggested move and reasoning
        """
        self.turn_count += 1
        
        if self.mode == MockMode.OPTIMAL_SOLVER:
            return self._get_optimal_move()
        
        elif self.mode == MockMode.INVALID_MOVE:
            return self._get_invalid_move()
        
        elif self.mode == MockMode.BUDGET_EXCEEDED:
            return self._get_budget_exceeding_move()
        
        else:
            raise ValueError(f"Unsupported mock mode: {self.mode}")
    
    def _get_optimal_move(self) -> HanoiMoveResponse:
        """Get the next optimal move from the pre-calculated sequence."""
        if self.turn_count <= len(self.optimal_moves):
            move = self.optimal_moves[self.turn_count - 1]
            reasoning = f"Optimal move #{self.turn_count}: Following the mathematical optimal solution for {self.num_disks} disks. This move progresses toward the goal efficiently."
        else:
            # This shouldn't happen with a proper optimal solver
            move = HanoiMove(source_tower="A", destination_tower="B")
            reasoning = f"Mock AI: Puzzle should be solved by now. This is a fallback move."
        
        return HanoiMoveResponse(move=move, reasoning=reasoning)
    
    def _get_invalid_move(self) -> HanoiMoveResponse:
        """Get moves that start optimal but become invalid at specified turn."""
        if self.turn_count < self.invalid_at_turn:
            # Use optimal moves until it's time for the invalid move
            move = self.optimal_moves[self.turn_count - 1]
            reasoning = f"Mock AI: Valid move #{self.turn_count} following optimal strategy before making intentional error."
        
        elif self.turn_count == self.invalid_at_turn:
            # Make an intentionally invalid move
            if self.num_disks >= 3:
                # Try to place a large disk on a small one
                move = HanoiMove(source_tower="A", destination_tower="C")
                reasoning = f"Mock AI: Intentionally invalid move - attempting to place larger disk on smaller disk to test error handling."
            else:
                # For smaller puzzles, try to move from empty tower
                move = HanoiMove(source_tower="B", destination_tower="C")
                reasoning = f"Mock AI: Intentionally invalid move - attempting to move from empty tower to test error handling."
        
        else:
            # After invalid move, continue with valid moves if somehow the test continues
            remaining_index = self.turn_count - 2  # Account for the skipped invalid move
            if remaining_index < len(self.optimal_moves):
                move = self.optimal_moves[remaining_index]
                reasoning = f"Mock AI: Resuming valid moves after intentional invalid move."
            else:
                move = HanoiMove(source_tower="A", destination_tower="B")
                reasoning = f"Mock AI: Fallback move after invalid move test."
        
        return HanoiMoveResponse(move=move, reasoning=reasoning)
    
    def _get_budget_exceeding_move(self) -> HanoiMoveResponse:
        """Get moves that will deliberately exceed the budget."""
        if self.turn_count <= len(self.inefficient_moves):
            move = self.inefficient_moves[self.turn_count - 1]
            reasoning = f"Mock AI: Inefficient move #{self.turn_count} - deliberately making suboptimal moves to test budget enforcement."
        else:
            # Continue with more cycling if we run out of pre-generated moves
            from typing import cast, Literal
            cycle_moves = ["A", "B", "C"]
            source = cast(Literal["A", "B", "C"], cycle_moves[self.turn_count % 3])
            dest = cast(Literal["A", "B", "C"], cycle_moves[(self.turn_count + 1) % 3])
            move = HanoiMove(source_tower=source, destination_tower=dest)
            reasoning = f"Mock AI: Extended inefficient cycling to ensure budget is exceeded."
        
        return HanoiMoveResponse(move=move, reasoning=reasoning)
