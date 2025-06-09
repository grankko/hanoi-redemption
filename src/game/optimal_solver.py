"""
Optimal Towers of Hanoi solver for demo purposes.
"""

from typing import List, Literal

# Try absolute import first, fallback to relative
try:
    from src.schemas import HanoiMove
except ImportError:
    from ..schemas import HanoiMove


class OptimalSolver:
    """
    Generates one optimal solution sequence for Towers of Hanoi.
    Used only for demo purposes.
    """
    
    def __init__(self, num_disks: int):
        self.num_disks = num_disks
        self.moves: List[HanoiMove] = []
        
    def solve(self) -> List[HanoiMove]:
        """
        Generate one optimal solution sequence.
        Returns list of moves from start to finish.
        """
        self.moves = []
        self._hanoi_recursive(self.num_disks, "A", "C", "B")
        return self.moves
    
    def _hanoi_recursive(
        self, 
        n: int, 
        source: Literal["A", "B", "C"], 
        destination: Literal["A", "B", "C"], 
        auxiliary: Literal["A", "B", "C"]
    ):
        """
        Recursive algorithm to solve Towers of Hanoi.
        """
        if n == 1:
            # Base case: move the smallest disk
            self.moves.append(HanoiMove(source_tower=source, destination_tower=destination))
        else:
            # Step 1: Move n-1 disks from source to auxiliary
            self._hanoi_recursive(n - 1, source, auxiliary, destination)
            
            # Step 2: Move the largest disk from source to destination
            self.moves.append(HanoiMove(source_tower=source, destination_tower=destination))
            
            # Step 3: Move n-1 disks from auxiliary to destination
            self._hanoi_recursive(n - 1, auxiliary, destination, source)
