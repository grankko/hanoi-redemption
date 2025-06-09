#!/usr/bin/env python3
"""
Test script to verify the budget-based validation logic works correctly.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import HanoiAITester


def test_budget_validation():
    """Test the budget-based validation logic."""
    print("🧪 Testing budget-based validation logic...")
    
    # Create a tester instance (without initializing AI)
    tester = HanoiAITester(3)
    tester.test_results = []  # Initialize empty test results
    optimal_moves = 7  # 2^3 - 1 = 7
    
    # Test case 1: Completed within budget (SUCCESS)
    tester.game.reset()
    tester.move_count = 7
    # Manually set game to solved state
    tester.game.state.tower_a = []
    tester.game.state.tower_b = []
    tester.game.state.tower_c = [1, 2, 3]
    
    results1 = tester._generate_test_results(optimal_moves)
    print(f"✅ Test 1 - Solved in 7 moves (budget=7): {results1['status']} (expected: SUCCESS)")
    assert results1['status'] == "SUCCESS", f"Expected SUCCESS, got {results1['status']}"
    assert results1['success'] == True, f"Expected success=True, got {results1['success']}"
    
    # Test case 2: Exceeded budget (FAILURE)
    tester.game.reset()
    tester.move_count = 8
    # Manually set game to solved state
    tester.game.state.tower_a = []
    tester.game.state.tower_b = []
    tester.game.state.tower_c = [1, 2, 3]
    
    results2 = tester._generate_test_results(optimal_moves)
    print(f"✅ Test 2 - Solved in 8 moves (budget=7): {results2['status']} (expected: FAILURE)")
    assert results2['status'] == "FAILURE", f"Expected FAILURE, got {results2['status']}"
    assert results2['success'] == False, f"Expected success=False, got {results2['success']}"
    
    # Test case 3: Not solved within budget (FAILURE)
    tester.game.reset()
    tester.move_count = 6
    # Game not solved (towers not in final state)
    
    results3 = tester._generate_test_results(optimal_moves)
    print(f"✅ Test 3 - Not solved in 6 moves (budget=7): {results3['status']} (expected: FAILURE)")
    assert results3['status'] == "FAILURE", f"Expected FAILURE, got {results3['status']}"
    assert results3['success'] == False, f"Expected success=False, got {results3['success']}"
    
    # Test case 4: Perfect optimal solution (SUCCESS)
    tester.game.reset()
    tester.move_count = 7
    # Manually set game to solved state
    tester.game.state.tower_a = []
    tester.game.state.tower_b = []
    tester.game.state.tower_c = [1, 2, 3]
    
    results4 = tester._generate_test_results(optimal_moves)
    print(f"✅ Test 4 - Perfect solution (7/7 moves): {results4['status']} (expected: SUCCESS)")
    assert results4['status'] == "SUCCESS", f"Expected SUCCESS, got {results4['status']}"
    assert results4['success'] == True, f"Expected success=True, got {results4['success']}"
    
    print("\n🎉 All budget validation tests passed!")
    print("✅ Only 2 status outcomes: SUCCESS or FAILURE")
    print("✅ Strict budget enforcement working correctly")
    return True


def main():
    """Run the budget validation test."""
    print("🧪 Testing Budget-Based Validation Logic")
    print("=" * 50)
    
    try:
        test_budget_validation()
        print("\n✅ Budget validation logic is working correctly!")
        print("🎯 The inconsistency has been fixed:")
        print("   • Only 2 possible outcomes: SUCCESS or FAILURE")
        print("   • SUCCESS: Solved within optimal move budget")
        print("   • FAILURE: Exceeded budget or didn't solve")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
