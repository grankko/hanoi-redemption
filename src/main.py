"""
Towers of Hanoi AI Testing - Research Validation
Tests AI reasoning models' ability to solve Towers of Hanoi puzzles.

This is the main entry point for the application.
"""

import sys
import argparse

# Try absolute import first, fallback to relative
try:
    from src.testing import TestRunner
except ImportError:
    from .testing import TestRunner


def get_num_disks_from_user() -> int:
    """Get number of disks from user input."""
    while True:
        try:
            num_disks = input("Enter number of disks (3-8 recommended): ").strip()
            num_disks = int(num_disks)
            if 1 <= num_disks <= 10:
                return num_disks
            else:
                print("Please enter a number between 1 and 10")
        except ValueError:
            print("Please enter a valid number")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Test AI reasoning models on Towers of Hanoi puzzles"
    )
    parser.add_argument(
        "num_disks", 
        type=int, 
        nargs="?",
        help="Number of disks (3-8 recommended)"
    )
    parser.add_argument(
        "--auto", 
        action="store_true", 
        help="Run in auto mode (no pauses between moves)"
    )
    
    args = parser.parse_args()
    
    print("🗼 TOWERS OF HANOI - AI REASONING TEST 🗼")
    print("Testing AI models' ability to solve Towers of Hanoi puzzles")
    print()
    
    # Get number of disks
    if args.num_disks:
        num_disks = args.num_disks
        if not (1 <= num_disks <= 10):
            print("Error: Number of disks must be between 1 and 10")
            sys.exit(1)
    else:
        # Interactive mode if no argument provided
        num_disks = get_num_disks_from_user()
    
    # Run the test
    test_runner = TestRunner(num_disks)
    results = test_runner.run_test(auto_mode=args.auto)
    
    if 'error' not in results:
        print(f"\n💾 Test completed for {num_disks} disks")
        print(f"   Status: {results['status']}")
        print(f"   Moves: {results['total_moves']}/{results['max_moves']}")
        if results['success']:
            print(f"   Efficiency: {results['efficiency_percent']}%")
        else:
            print(f"   Efficiency: N/A (incomplete)")


if __name__ == "__main__":
    main()