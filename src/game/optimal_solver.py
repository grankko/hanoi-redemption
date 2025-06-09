"""
Optimal Towers of Hanoi solver for validation.
"""

from typing import List, Tuple

# Try absolute import first, fallback to relative
try:
    from src.schemas import HanoiMove
except ImportError:
    from ..schemas import HanoiMove


class OptimalSolver:
    """
    Generates the optimal solution sequence for Towers of Hanoi.
    """
    
    def __init__(self, num_disks: int):
        self.num_disks = num_disks
        self.moves: List[HanoiMove] = []
        
    def solve(self) -> List[HanoiMove]:
        """
        Generate the complete optimal solution.
        Returns list of moves from start to finish.
        """
        self.moves = []
        self._hanoi_recursive(self.num_disks, "A", "C", "B")
        return self.moves
    
    from typing import Literal

    def _hanoi_recursive(
        self,
        n: int,
        source: 'Literal["A", "B", "C"]',
        destination: 'Literal["A", "B", "C"]',
        auxiliary: 'Literal["A", "B", "C"]'
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
    
    def get_next_optimal_move(self, move_number: int) -> HanoiMove:
        """
        Get the optimal move for a given turn number (0-based).
        """
        if not self.moves:
            self.solve()
        
        if 0 <= move_number < len(self.moves):
            return self.moves[move_number]
        else:
            raise IndexError(f"Move {move_number} is out of range for {self.num_disks} disks")
    
    def is_optimal_move(self, move: HanoiMove, move_number: int) -> bool:
        """
        Check if the given move matches the optimal move for this turn.
        """
        try:
            optimal_move = self.get_next_optimal_move(move_number)
            return (move.source_tower == optimal_move.source_tower and 
                   move.destination_tower == optimal_move.destination_tower)
        except IndexError:
            return False
    
    def get_total_moves(self) -> int:
        """
        Get the total number of moves in the optimal solution.
        """
        return 2 ** self.num_disks - 1
