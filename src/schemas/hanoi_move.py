"""
Pydantic schemas for Towers of Hanoi structured outputs.
"""

from typing import Literal
from pydantic import BaseModel, Field


class HanoiMove(BaseModel):
    """
    A move in the Towers of Hanoi game.
    
    Represents moving a disk from a source tower to a destination tower.
    Towers are named A, B, and C.
    """
    
    source_tower: Literal["A", "B", "C"] = Field(
        description="The tower to move the disk from"
    )
    destination_tower: Literal["A", "B", "C"] = Field(
        description="The tower to move the disk to"
    )
    
    def __str__(self) -> str:
        return f"Move disk from tower {self.source_tower} to tower {self.destination_tower}"
    
    def __repr__(self) -> str:
        return f"HanoiMove(source_tower='{self.source_tower}', destination_tower='{self.destination_tower}')"


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

