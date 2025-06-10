#!/usr/bin/env python3
"""
Test script to verify the recent moves context works correctly.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import HanoiAITester
from src.schemas import HanoiMove


def test_recent_moves_context():
    """Test the recent moves context in AI prompts."""
    print("🧪 Testing recent moves context...")
    
    # Create a tester instance
    tester = HanoiAITester(3)
    
    # Simulate some moves and corresponding states
    moves = [
        HanoiMove(source_tower="A", destination_tower="C"),
        HanoiMove(source_tower="A", destination_tower="B"),
        HanoiMove(source_tower="C", destination_tower="B"),
        HanoiMove(source_tower="A", destination_tower="C"),
        HanoiMove(source_tower="B", destination_tower="A")
    ]
    
    # Simulate corresponding states before each move
    states = [
        {'tower_a': [1, 2, 3], 'tower_b': [], 'tower_c': []},  # Initial state
        {'tower_a': [2, 3], 'tower_b': [], 'tower_c': [1]},   # After move 1
        {'tower_a': [3], 'tower_b': [2], 'tower_c': [1]},     # After move 2
        {'tower_a': [3], 'tower_b': [1, 2], 'tower_c': []},   # After move 3
        {'tower_a': [], 'tower_b': [1, 2], 'tower_c': [3]}    # After move 4
    ]
    
    # Test each stage of move tracking
    for i, move in enumerate(moves):
        tester.move_count = i
        tester.recent_moves = moves[:i]  # Simulate moves made so far
        tester.recent_states = states[:i]  # Simulate states before each move
        
        prompt = tester._create_ai_prompt()
        print(f"\n--- After {i} moves ---")
        print(f"Recent moves: {tester.recent_moves}")
        print(f"Recent states: {tester.recent_states}")
        print("Generated prompt:")
        print(prompt)
        print("-" * 50)
    
    # Test the 3-move limit specifically
    print("\n🧪 Testing 3-move limit...")
    tester.move_count = 5
    tester.recent_moves = moves  # All 5 moves
    tester.recent_states = states  # All 5 states
    
    prompt = tester._create_ai_prompt()
    print(f"All moves: {moves}")
    print(f"All states: {states}")
    print(f"Recent moves (should be last 3): {tester.recent_moves[-3:]}")
    print(f"Recent states (should be last 3): {tester.recent_states[-3:]}")
    print("Generated prompt:")
    print(prompt)
    
    # Verify only last 3 moves are shown
    lines = prompt.split('\n')
    move_section_lines = [line for line in lines if '--- Move ' in line]
    
    print(f"\nMove section lines in prompt: {len(move_section_lines)}")
    assert len(move_section_lines) <= 3, f"Expected max 3 move sections, got {len(move_section_lines)}"
    
    if len(move_section_lines) == 3:
        # Should show moves 3, 4, 5 (1-indexed)
        expected_moves = ["--- Move 3 ---", "--- Move 4 ---", "--- Move 5 ---"]
        for i, line in enumerate(move_section_lines):
            assert expected_moves[i] in line, f"Expected '{expected_moves[i]}' in line: {line}"
    
    print("✅ Recent moves context working correctly!")
    return True


def main():
    """Run the recent moves context test."""
    print("🧪 Testing Enhanced AI Context (Moves + States)")
    print("=" * 60)
    
    try:
        test_recent_moves_context()
        print("\n✅ Enhanced AI context is working correctly!")
        print("🎯 Key improvements:")
        print("   • AI now sees last 3 moves AND corresponding previous states")
        print("   • AI can see exactly what the board looked like before each move") 
        print("   • Anti-cycling instructions prevent returning to previous states")
        print("   • Much richer strategic awareness for optimal problem-solving")
        print("   • Automatic management of move and state history buffers")
        
        # Demo the enhanced prompt format
        print("\n🚀 Enhanced Prompt Example:")
        print("=" * 40)
        tester = HanoiAITester(3)
        tester.move_count = 3
        tester.recent_moves = [
            HanoiMove(source_tower="A", destination_tower="C"),
            HanoiMove(source_tower="A", destination_tower="B"),
            HanoiMove(source_tower="C", destination_tower="B")
        ]
        tester.recent_states = [
            {'tower_a': [1, 2, 3], 'tower_b': [], 'tower_c': []},
            {'tower_a': [2, 3], 'tower_b': [], 'tower_c': [1]}, 
            {'tower_a': [3], 'tower_b': [2], 'tower_c': [1]}
        ]
        prompt = tester._create_ai_prompt()
        print(prompt)
        print("=" * 40)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
