"""
Test runner for Towers of Hanoi AI tests.

This module orchestrates the execution of AI tests, handling the main game loop,
user interaction, and coordination between components.
"""

from typing import Optional
from .ai_tester import HanoiAITester
from .results_manager import ResultsManager


class TestRunner:
    """
    Orchestrates the execution of Towers of Hanoi AI tests.
    
    Handles the main game loop, user interaction, and coordination between
    the AI tester and results manager.
    """
    
    def __init__(self, num_disks: int):
        self.num_disks = num_disks
        self.tester = HanoiAITester(num_disks)
        self.results_manager = ResultsManager(num_disks)
    
    def run_test(self, auto_mode: bool = False) -> dict:
        """
        Run the complete AI test.
        Returns test results dictionary.
        """
        if not self.tester.initialize_ai():
            return {"error": "Failed to initialize AI"}
        
        print(f"\n🧪 Testing AI on {self.num_disks}-disk Towers of Hanoi")
        print("=" * 60)
        
        # Display initial state
        self.tester.display.display_welcome()
        tower_states = self.tester.get_current_state()
        self.tester.display.display_towers(list(tower_states), self.tester.move_count)
        
        # Calculate move budgets
        optimal_moves = (2 ** self.num_disks) - 1
        max_moves = optimal_moves * 2  # Double the optimal for maximum allowed
        
        self._display_test_info(optimal_moves, max_moves)
        
        # Main game loop
        test_result = self._run_game_loop(auto_mode, max_moves)
        if test_result:
            return test_result
        
        # Check if AI exceeded budget
        if self.tester.move_count >= max_moves and not self.tester.is_solved():
            print(f"\n💸 AI EXCEEDED MOVE BUDGET!")
            print(f"   Used {self.tester.move_count} moves, budget was {max_moves}")
            print("   AI failed to solve within budget")
        
        # Test completed - show results
        return self._finalize_results(optimal_moves, max_moves)
    
    def _display_test_info(self, optimal_moves: int, max_moves: int):
        """Display test information and budgets."""
        print(f"📊 Theoretical minimum moves for {self.num_disks} disks: {optimal_moves}")
        print(f"🤖 AI has budget of {max_moves} moves to solve this puzzle")
        print(f"🏆 Optimal completion: {optimal_moves} moves")
        print(f"🧠 Testing AI reasoning capability...")
        print()
    
    def _run_game_loop(self, auto_mode: bool, max_moves: int) -> Optional[dict]:
        """
        Run the main game loop.
        
        Returns:
            Optional[dict]: Error result if loop should terminate early, None to continue
        """
        while not self.tester.is_solved() and self.tester.move_count < max_moves:
            print(f"\n--- Turn #{self.tester.move_count + 1} ---")
            print(f"💰 Moves remaining in budget: {max_moves - self.tester.move_count}")
            
            # Get AI's move
            print("🤖 AI is thinking...")
            ai_move_result = self.tester.get_ai_move()
            if ai_move_result is None:
                print("❌ Failed to get AI move")
                break
            ai_move, ai_reasoning = ai_move_result
            
            print(f"🎯 AI suggests: Move disk from {ai_move.source_tower} to {ai_move.destination_tower}")
            print(f"💭 AI reasoning: {ai_reasoning}")
            
            # Validate and execute the move
            success, message = self.tester.validate_and_execute_move(ai_move, ai_reasoning)
            
            if not success:
                print(f"💔 {message} - stopping test")
                break
            
            # Wait for user confirmation (unless auto mode)
            if not auto_mode:
                try:
                    user_input = input("\nPress Enter to continue to next turn (or 'q' to quit)...").strip().lower()
                    if user_input == 'q':
                        print("🛑 Test interrupted by user")
                        break
                except (EOFError, KeyboardInterrupt):
                    print("\n🛑 Test interrupted by user")
                    break
        
        return None  # Continue to results
    
    def _finalize_results(self, optimal_moves: int, max_moves: int) -> dict:
        """Generate and display final results."""
        results = self.results_manager.generate_test_results(
            self.tester, optimal_moves, max_moves
        )
        
        self.results_manager.display_final_results(results, self.tester)
        
        # Automatically export results to JSON file
        exported_file = self.results_manager.export_results(results)
        if exported_file:
            print(f"📄 Results exported to: {exported_file}")
        
        return results
