"""
Towers of Hanoi game logic and validation.
"""

from typing import Literal

# Try absolute import first, fallback to relative
try:
    from src.schemas import HanoiGameState, HanoiMove
except ImportError:
    from ..schemas import HanoiGameState, HanoiMove


class TowersOfHanoi:
    """
    Manages the state and rules of a Towers of Hanoi game.
    """
    
    def __init__(self, num_disks: int = 3):
        """
        Initialize a new Towers of Hanoi game.
        
        Args:
            num_disks: Number of disks to start with (default: 3)
        """
        self.num_disks = num_disks
        self.state = HanoiGameState()
        self.reset()
    
    def reset(self) -> None:
        """Reset the game to initial state with all disks on tower A."""
        self.state.tower_a = list(range(1, self.num_disks + 1))  # [1, 2, 3, ...]
        self.state.tower_b = []
        self.state.tower_c = []
    
    def is_valid_move(self, move: HanoiMove) -> tuple[bool, str]:
        """
        Check if a move is valid according to Towers of Hanoi rules.
        
        Args:
            move: The move to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        source_tower = self.state.get_tower(move.source_tower)
        dest_tower = self.state.get_tower(move.destination_tower)
        
        # Cannot move from the same tower to itself
        if move.source_tower == move.destination_tower:
            return False, f"Cannot move from tower {move.source_tower} to itself"
        
        # Source tower must have at least one disk
        if not source_tower:
            return False, f"Tower {move.source_tower} is empty"
        
        # Cannot place a larger disk on a smaller disk
        if dest_tower and source_tower[0] > dest_tower[0]:
            return False, f"Cannot place disk {source_tower[0]} on top of disk {dest_tower[0]}"
        
        return True, ""
    
    def make_move(self, move: HanoiMove) -> bool:
        """
        Execute a move if it's valid.
        
        Args:
            move: The move to execute
            
        Returns:
            True if move was successful, False otherwise
        """
        is_valid, error = self.is_valid_move(move)
        if not is_valid:
            print(f"Invalid move: {error}")
            return False
        
        # Execute the move
        source_tower = self.state.get_tower(move.source_tower)
        dest_tower = self.state.get_tower(move.destination_tower)
        
        disk = source_tower.pop(0)  # Remove from top of source
        dest_tower.insert(0, disk)  # Add to top of destination
        
        print(f"✓ {move}")
        return True
    
    def is_solved(self) -> bool:
        """Check if the puzzle is solved (all disks on tower C)."""
        return (
            len(self.state.tower_c) == self.num_disks and
            len(self.state.tower_a) == 0 and
            len(self.state.tower_b) == 0
        )
    
    def get_state_description(self) -> str:
        """Get a human-readable description of the current game state."""
        return (
            f"Tower A: {self.state.tower_a}\n"
            f"Tower B: {self.state.tower_b}\n"
            f"Tower C: {self.state.tower_c}"
        )
    
    def get_state_for_ai(self) -> str:
        """Get a formatted description of the game state for AI input."""
        return (
            f"Current game state:\n"
            f"Tower A (source): {self.state.tower_a if self.state.tower_a else 'empty'}\n"
            f"Tower B (auxiliary): {self.state.tower_b if self.state.tower_b else 'empty'}\n"
            f"Tower C (destination): {self.state.tower_c if self.state.tower_c else 'empty'}\n\n"
            f"Rules:\n"
            f"- Only move one disk at a time\n"
            f"- Only move the top disk from a tower\n"
            f"- Never place a larger disk on top of a smaller disk\n"
            f"- Goal: Move all disks to tower C\n\n"
            f"Disk sizes: 1 (smallest) to {self.num_disks} (largest)"
        )
