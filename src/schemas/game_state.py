"""
Game state and response schemas for Towers of Hanoi.
"""

from typing import Literal
from pydantic import BaseModel, Field

from .hanoi_move import HanoiMove


class HanoiGameState(BaseModel):
    """
    Represents the current state of a Towers of Hanoi game.
    
    Each tower is represented as a list of disk sizes, where the first element
    is the top disk (smallest number = smallest disk).
    """
    
    tower_a: list[int] = Field(
        default_factory=list,
        description="Disks on tower A, top to bottom"
    )
    tower_b: list[int] = Field(
        default_factory=list,
        description="Disks on tower B, top to bottom"
    )
    tower_c: list[int] = Field(
        default_factory=list,
        description="Disks on tower C, top to bottom"
    )
    
    def get_tower(self, tower_name: Literal["A", "B", "C"]) -> list[int]:
        """Get the list of disks for a given tower."""
        if tower_name == "A":
            return self.tower_a
        elif tower_name == "B":
            return self.tower_b
        elif tower_name == "C":
            return self.tower_c
        else:
            raise ValueError(f"Invalid tower name: {tower_name}")
    
    def set_tower(self, tower_name: Literal["A", "B", "C"], disks: list[int]) -> None:
        """Set the list of disks for a given tower."""
        if tower_name == "A":
            self.tower_a = disks
        elif tower_name == "B":
            self.tower_b = disks
        elif tower_name == "C":
            self.tower_c = disks
        else:
            raise ValueError(f"Invalid tower name: {tower_name}")


class HanoiMoveResponse(BaseModel):
    """
    Response from the AI containing a suggested move and reasoning.
    """
    reasoning: str = Field(
        description="Explanation of why this move was chosen"
    )
    
    move: HanoiMove = Field(
        description="The suggested move to make"
    )
