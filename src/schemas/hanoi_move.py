"""
Hanoi move schema for Towers of Hanoi game.
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

