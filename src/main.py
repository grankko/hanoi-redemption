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
    from src.api import MockAIClient, MockMode
except ImportError:
    from .testing import TestRunner
    from .api import MockAIClient, MockMode


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
    parser.add_argument(
        "--mock",
        type=str,
        choices=["optimal", "invalid-move", "budget-exceeded"],
        help="Use mock AI client with specified behavior mode"
    )
    
    args = parser.parse_args()
    
    print("🗼 TOWERS OF HANOI - AI REASONING TEST 🗼")
    print("Testing AI models' ability to solve Towers of Hanoi puzzles")
    if args.mock:
        print(f"🤖 Mock Mode: {args.mock}")
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
    
    # Create AI client based on mode
    ai_client = None
    if args.mock:
        try:
            mode = MockMode(args.mock)
            ai_client = MockAIClient(mode, num_disks)
            print(f"✅ Mock AI client initialized in {args.mock} mode")
        except ValueError as e:
            print(f"❌ Error creating mock client: {e}")
            sys.exit(1)
    
    # Run the test
    test_runner = TestRunner(num_disks, ai_client)
    results = test_runner.run_test(auto_mode=args.auto)
    
    if 'error' not in results:
        print(f"\n💾 Test completed for {num_disks} disks")
        print(f"   Status: {results['status']}")
        print(f"   Moves: {results['total_moves']}/{results['max_moves']}")
        if results['success']:
            print(f"   Efficiency: {results['efficiency_percent']}%")
        else:
            print(f"   Efficiency: N/A (incomplete)")
        
        if args.mock:
            print(f"   Mock Mode: {args.mock} - Test completed successfully! ✅")


if __name__ == "__main__":
    main()