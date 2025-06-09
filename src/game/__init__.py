"""
Game package for Towers of Hanoi logic.
"""

# Try absolute import first, fallback to relative
try:
    from src.game.towers_of_hanoi import TowersOfHanoi
    from src.game.optimal_solver import OptimalSolver
except ImportError:
    from .towers_of_hanoi import TowersOfHanoi
    from .optimal_solver import OptimalSolver

__all__ = ["TowersOfHanoi", "OptimalSolver"]
