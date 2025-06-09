#!/usr/bin/env python3
"""
Demo script showing the optimal solution for Towers of Hanoi.
This demonstrates what the AI should achieve.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.game import TowersOfHanoi, OptimalSolver
from src.display import TowerDisplay


def demo_optimal_solution(num_disks: int):
    """Demo the optimal solution for a given number of disks."""
    print(f"🗼 TOWERS OF HANOI - OPTIMAL SOLUTION DEMO ({num_disks} disks)")
    print("=" * 60)
    
    # Initialize components
    game = TowersOfHanoi(num_disks)
    solver = OptimalSolver(num_disks)
    display = TowerDisplay(num_disks)
    
    # Get optimal solution
    optimal_moves = solver.solve()
    total_moves = len(optimal_moves)
    
    print(f"📊 Optimal solution requires {total_moves} moves")
    print("🎯 Here's the optimal sequence:\n")
    
    # Display initial state
    display.display_welcome()
    display.display_towers([
        game.state.tower_a,
        game.state.tower_b,
        game.state.tower_c
    ], 0)
    
    # Execute each optimal move
    for i, move in enumerate(optimal_moves):
        print(f"\n--- Optimal Move {i + 1}/{total_moves} ---")
        print(f"🎯 Move: {move}")
        
        # Execute the move
        success = game.make_move(move)
        if not success:
            print("❌ Error executing move!")
            break
        
        # Display the updated state
        display.display_towers([
            game.state.tower_a,
            game.state.tower_b,
            game.state.tower_c
        ], i + 1, pause=False)
        
        # Wait for user confirmation
        try:
            user_input = input("Press Enter for next move (or 'q' to quit)...").strip().lower()
            if user_input == 'q':
                print("🛑 Demo interrupted by user")
                break
        except (EOFError, KeyboardInterrupt):
            print("\n🛑 Demo interrupted by user")
            break
    
    # Final results
    if game.is_solved():
        display.display_completion(total_moves, total_moves)
        print("🏆 Perfect optimal solution!")
    else:
        print("❌ Something went wrong...")


def main():
    """Main demo function."""
    print("🗼 TOWERS OF HANOI - OPTIMAL SOLUTION DEMO 🗼")
    print("This shows what the AI should achieve.\n")
    
    # Get number of disks
    while True:
        try:
            num_disks = input("Enter number of disks (3-6 recommended): ").strip()
            num_disks = int(num_disks)
            if 1 <= num_disks <= 8:
                break
            else:
                print("Please enter a number between 1 and 8")
        except ValueError:
            print("Please enter a valid number")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return
    
    try:
        demo_optimal_solution(num_disks)
    except (EOFError, KeyboardInterrupt):
        print("\n\nDemo interrupted. Goodbye!")


if __name__ == "__main__":
    main()
