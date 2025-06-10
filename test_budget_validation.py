#!/usr/bin/env python3
"""
Test script to verify the 3-outcome validation logic works correctly.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import HanoiAITester


def test_outcome_validation():
    """Test the 3-outcome validation logic."""
    print("🧪 Testing 3-outcome validation logic...")
    
    # Create a tester instance (without initializing AI)
    tester = HanoiAITester(3)
    tester.test_results = []  # Initialize empty test results
    optimal_moves = 7  # 2^3 - 1 = 7
    max_moves = 14    # 2 * 7 = 14
    
    # Test case 1: Optimal completion (OPTIMAL_SUCCESS)
    tester.game.reset()
    tester.move_count = 7
    # Manually set game to solved state
    tester.game.state.tower_a = []
    tester.game.state.tower_b = []
    tester.game.state.tower_c = [1, 2, 3]
    
    results1 = tester._generate_test_results(optimal_moves, max_moves)
    print(f"✅ Test 1 - Optimal (7/7 moves): {results1['status']} (expected: OPTIMAL_SUCCESS)")
    assert results1['status'] == "OPTIMAL_SUCCESS", f"Expected OPTIMAL_SUCCESS, got {results1['status']}"
    assert results1['success'] == True, f"Expected success=True, got {results1['success']}"
    assert results1['efficiency_percent'] == 100.0, f"Expected 100% efficiency, got {results1['efficiency_percent']}"
    
    # Test case 2: Solved within budget (SUCCESS)
    tester.game.reset()
    tester.move_count = 10
    # Manually set game to solved state
    tester.game.state.tower_a = []
    tester.game.state.tower_b = []
    tester.game.state.tower_c = [1, 2, 3]
    
    results2 = tester._generate_test_results(optimal_moves, max_moves)
    print(f"✅ Test 2 - Solved non-optimally (10/14 moves): {results2['status']} (expected: SUCCESS)")
    assert results2['status'] == "SUCCESS", f"Expected SUCCESS, got {results2['status']}"
    assert results2['success'] == True, f"Expected success=True, got {results2['success']}"
    assert results2['efficiency_percent'] == 70.0, f"Expected 70% efficiency, got {results2['efficiency_percent']}"
    
    # Test case 3: Exceeded budget (FAILURE)
    tester.game.reset()
    tester.move_count = 15
    # Manually set game to solved state (but too many moves)
    tester.game.state.tower_a = []
    tester.game.state.tower_b = []
    tester.game.state.tower_c = [1, 2, 3]
    
    results3 = tester._generate_test_results(optimal_moves, max_moves)
    print(f"✅ Test 3 - Exceeded budget (15/14 moves): {results3['status']} (expected: FAILURE)")
    assert results3['status'] == "FAILURE", f"Expected FAILURE, got {results3['status']}"
    assert results3['success'] == False, f"Expected success=False, got {results3['success']}"
    
    # Test case 4: Not solved within budget (FAILURE)
    tester.game.reset()
    tester.move_count = 10
    # Game not solved (towers not in final state)
    
    results4 = tester._generate_test_results(optimal_moves, max_moves)
    print(f"✅ Test 4 - Not solved (10/14 moves): {results4['status']} (expected: FAILURE)")
    assert results4['status'] == "FAILURE", f"Expected FAILURE, got {results4['status']}"
    assert results4['success'] == False, f"Expected success=False, got {results4['success']}"
    
    print("\n🎉 All 3-outcome validation tests passed!")
    print("✅ Three status outcomes: OPTIMAL_SUCCESS, SUCCESS, FAILURE")
    print("✅ Efficiency calculation working correctly")
    print("✅ 2x budget enforcement working correctly")
    return True


def main():
    """Run the 3-outcome validation test."""
    print("🧪 Testing 3-Outcome Validation Logic")
    print("=" * 50)
    
    try:
        test_outcome_validation()
        print("\n✅ 3-outcome validation logic is working correctly!")
        print("🎯 The new system features:")
        print("   • Three possible outcomes: OPTIMAL_SUCCESS, SUCCESS, FAILURE")
        print("   • OPTIMAL_SUCCESS: Solved within theoretical minimum")
        print("   • SUCCESS: Solved within 2x budget but not optimal")
        print("   • FAILURE: Exceeded 2x budget or didn't solve")
        print("   • Efficiency metrics shown at end of game")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
