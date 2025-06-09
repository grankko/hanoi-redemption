"""
ASCII Art Display for Tower of Hanoi
"""
import os
from typing import List


class TowerDisplay:
    def __init__(self, num_disks: int):
        """Initialize the display with given number of disks."""
        self.num_disks = num_disks
        self.tower_width = max(7, num_disks * 2 + 3)  # Minimum width for tower labels
        self.total_width = self.tower_width * 3 + 6  # 3 towers + spacing
        
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_disk_visual(self, disk_size: int) -> str:
        """Get ASCII representation of a disk."""
        if disk_size == 0:
            return "|"
        
        # Create disk with size proportional to disk number
        disk_chars = "*" * (disk_size * 2 - 1)
        return f"[{disk_chars}]"
    
    from typing import Optional, Tuple

    def display_towers(self, towers: List[List[int]], move_count: int = 0, 
                      current_move: Optional[Tuple[int, int]] = None, pause: bool = True):
        """Display the current state of all towers."""
        if pause:
            self.clear_screen()
        
        print("=" * self.total_width)
        print(f"🗼 TOWER OF HANOI - Move #{move_count} 🗼".center(self.total_width))
        if current_move:
            tower_names = ['A', 'B', 'C']
            print(f"Moving from Tower {tower_names[current_move[0]]} to Tower {tower_names[current_move[1]]}".center(self.total_width))
        print("=" * self.total_width)
        print()
        
        # Calculate the height needed (max tower height + base + labels)
        max_height = max(len(tower) for tower in towers) if any(towers) else 1
        display_height = max(max_height, self.num_disks) + 2
        
        # Build the display from top to bottom
        lines = []
        
        # Draw towers from top to bottom
        for level in range(display_height - 1, -1, -1):
            line_parts = []
            
            for tower_idx, tower in enumerate(towers):
                # Get disk at this level (if any)
                # Tower list is stored with index 0 = top disk, so we need to reverse the indexing
                tower_level_from_bottom = level
                disk_index_from_top = len(tower) - 1 - tower_level_from_bottom
                
                if 0 <= disk_index_from_top < len(tower):
                    disk_size = tower[disk_index_from_top]
                    disk_visual = self.get_disk_visual(disk_size)
                else:
                    disk_visual = "|"  # Empty pole
                
                # Center the disk/pole in the tower width
                centered_disk = disk_visual.center(self.tower_width)
                line_parts.append(centered_disk)
            
            lines.append("  ".join(line_parts))
        
        # Add base
        base_line = []
        for _ in range(3):
            base = "=" * self.tower_width
            base_line.append(base)
        lines.append("  ".join(base_line))
        
        # Add tower labels
        label_line = []
        for label in ['Tower A', 'Tower B', 'Tower C']:
            centered_label = label.center(self.tower_width)
            label_line.append(centered_label)
        lines.append("  ".join(label_line))
        
        # Print all lines
        for line in lines:
            print(line)
        
        print()
    
    def display_completion(self, total_moves: int, budget_moves: int):
        """Display completion message for budget-based validation."""
        print("🎉" * (self.total_width // 2))
        print("PUZZLE SOLVED!".center(self.total_width))
        print(f"Moves used: {total_moves}".center(self.total_width))
        print(f"Budget allowed: {budget_moves}".center(self.total_width))
        
        if total_moves <= budget_moves:
            print("SUCCESS! Solved within budget! 🏆".center(self.total_width))
        else:
            print("Budget exceeded but solved! 💸".center(self.total_width))
        
        print("🎉" * (self.total_width // 2))
    
    def display_welcome(self):
        """Display welcome message."""
        print("=" * self.total_width)
        print("🗼 WELCOME TO TOWER OF HANOI SIMULATION 🗼".center(self.total_width))
        print("=" * self.total_width)
        print()
        print("Rules:")
        print("1. Move all disks from Tower A to Tower C")
        print("2. Only one disk can be moved at a time")
        print("3. A larger disk cannot be placed on a smaller disk")
        print()
        print("Watch as the algorithm solves it automatically!")
        print("(Seeking redemption after Apple's criticism... 😤)")
        print()
