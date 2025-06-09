#!/usr/bin/env python3
"""
Quick test script to verify the Hanoi AI project is working correctly.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_components():
    """Test all major components."""
    print("🧪 Testing Hanoi AI components...")
    
    try:
        # Test imports
        from src.schemas import HanoiMove, HanoiGameState, HanoiMoveResponse
        from src.game import TowersOfHanoi, OptimalSolver
        from src.display import TowerDisplay
        print("✅ All imports successful")
        
        # Test schema validation
        move = HanoiMove(source_tower="A", destination_tower="C")
        print(f"✅ HanoiMove schema: {move}")
        
        # Test game logic
        game = TowersOfHanoi(3)
        initial_state = game.state
        print(f"✅ Game initialized: Tower A has {len(initial_state.tower_a)} disks")
        
        # Test optimal solver
        solver = OptimalSolver(3)
        optimal_moves = solver.solve()
        print(f"✅ Optimal solver: {len(optimal_moves)} moves for 3 disks")
        
        # Test first optimal move
        first_move = optimal_moves[0]
        is_valid, error = game.is_valid_move(first_move)
        print(f"✅ First optimal move is valid: {first_move}")
        
        # Test display (basic functionality)
        display = TowerDisplay(3)
        print("✅ Display component initialized")
        
        # Test move execution
        game.make_move(first_move)
        print("✅ Move execution successful")
        
        print("\n🎉 All components working correctly!")
        print("\nNext steps:")
        print("1. Set up your OpenAI API key in .env file")
        print("2. Run: python -m src.main")
        print("3. Or try demo: python demo_optimal.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_components()
    sys.exit(0 if success else 1)
