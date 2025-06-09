"""
Towers of Hanoi AI Testing - Research Validation
Tests AI reasoning models' ability to solve Towers of Hanoi puzzles.
"""

import sys
from typing import Optional

# Try absolute import first, fallback to relative
try:
    from src.api import HanoiAIClient
    from src.game import TowersOfHanoi, OptimalSolver
    from src.schemas import HanoiMove
    from src.display import TowerDisplay
except ImportError:
    from .api import HanoiAIClient
    from .game import TowersOfHanoi, OptimalSolver
    from .schemas import HanoiMove
    from .display import TowerDisplay


class HanoiAITester:
    """
    Tests AI reasoning models on Towers of Hanoi puzzles.
    """
    
    def __init__(self, num_disks: int):
        self.num_disks = num_disks
        self.game = TowersOfHanoi(num_disks)
        self.optimal_solver = OptimalSolver(num_disks)
        self.display = TowerDisplay(num_disks)
        self.ai_client = None
        self.move_count = 0
        self.ai_correct_moves = 0
        self.test_results = []
        
    def initialize_ai(self) -> bool:
        """Initialize the AI client."""
        try:
            self.ai_client = HanoiAIClient()
            return True
        except ValueError as e:
            print(f"❌ Error initializing AI: {e}")
            print("Please create a .env file with your OpenAI API key:")
            print("OPENAI_API_KEY=your_api_key_here")
            return False
    
    def get_ai_move(self) -> Optional[tuple[HanoiMove, str]]:
        """Get the next move from AI."""
        try:
            # Create detailed state description for AI
            state_desc = self._create_ai_prompt()
            if self.ai_client is None:
                raise ValueError("AI client is not initialized.")
            response = self.ai_client.get_next_move(state_desc)
            return response.move, response.reasoning
        except Exception as e:
            print(f"❌ Error getting AI move: {e}")
            return None
    
    def _create_ai_prompt(self) -> str:
        """Create a simple game state description for the AI."""
        towers = self.game.state
        
        prompt = f"""{self.num_disks}-disk Towers of Hanoi puzzle - Turn #{self.move_count + 1}

Tower A: {towers.tower_a if towers.tower_a else 'empty'}
Tower B: {towers.tower_b if towers.tower_b else 'empty'}  
Tower C: {towers.tower_c if towers.tower_c else 'empty'}"""

        return prompt
    
    def validate_move(self, ai_move: HanoiMove) -> tuple[bool, bool]:
        """
        Validate AI move against game rules and optimal solution.
        Returns (is_valid_move, is_optimal_move)
        """
        # Check if move is valid according to game rules
        is_valid, error = self.game.is_valid_move(ai_move)
        
        # Check if move matches optimal solution
        is_optimal = False
        if is_valid:
            is_optimal = self.optimal_solver.is_optimal_move(ai_move, self.move_count)
        
        return is_valid, is_optimal
    
    def run_test(self, auto_mode: bool = False) -> dict:
        """
        Run the complete AI test.
        Returns test results dictionary.
        """
        if not self.initialize_ai():
            return {"error": "Failed to initialize AI"}
        
        print(f"\n🧪 Testing AI on {self.num_disks}-disk Towers of Hanoi")
        print("=" * 60)
        
        # Display initial state
        self.display.display_welcome()
        self.display.display_towers([
            self.game.state.tower_a,
            self.game.state.tower_b, 
            self.game.state.tower_c
        ], self.move_count)
        
        # Get optimal solution for comparison
        optimal_moves = self.optimal_solver.solve()
        total_optimal_moves = len(optimal_moves)
        
        print(f"📊 Optimal solution requires {total_optimal_moves} moves")
        print(f"🤖 Testing AI reasoning capability...")
        print()
        
        # Main game loop
        while not self.game.is_solved() and self.move_count < total_optimal_moves * 2:
            print(f"\n--- Turn #{self.move_count + 1} ---")
            
            # Get AI's move
            print("🤖 AI is thinking...")
            ai_move_result = self.get_ai_move()
            if ai_move_result is None:
                print("❌ Failed to get AI move")
                break
            ai_move, ai_reasoning = ai_move_result
            
            print(f"🎯 AI suggests: {ai_move}")
            print(f"💭 AI reasoning: {ai_reasoning}")
            
            # Validate the move
            is_valid, is_optimal = self.validate_move(ai_move)
            
            # Get optimal move for comparison
            try:
                optimal_move = self.optimal_solver.get_next_optimal_move(self.move_count)
                print(f"✅ Optimal move: {optimal_move}")
            except IndexError:
                optimal_move = None
                print("⚠️  No more optimal moves available")
            
            # Display validation results
            if is_valid:
                print("✅ AI move is VALID")
                if is_optimal:
                    print("🎯 AI move is OPTIMAL!")
                    self.ai_correct_moves += 1
                else:
                    print("⚠️  AI move is SUBOPTIMAL")
            else:
                print("❌ AI move is INVALID")
            
            # Record the result
            self.test_results.append({
                'turn': self.move_count + 1,
                'ai_move': ai_move,
                'optimal_move': optimal_move,
                'is_valid': is_valid,
                'is_optimal': is_optimal,
                'ai_reasoning': ai_reasoning
            })
            
            # Execute the move if valid
            if is_valid:
                success = self.game.make_move(ai_move)
                if success:
                    self.move_count += 1
                    
                    # Display updated state (no auto pause)
                    self.display.display_towers([
                        self.game.state.tower_a,
                        self.game.state.tower_b,
                        self.game.state.tower_c
                    ], self.move_count, pause=False)
                else:
                    print("❌ Failed to execute move")
                    break
            else:
                print("💔 Invalid move - stopping test")
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
        
        # Test completed - show results
        return self._generate_test_results(total_optimal_moves)
    
    def _generate_test_results(self, optimal_total: int) -> dict:
        """Generate comprehensive test results."""
        if self.game.is_solved():
            success = True
            status = "COMPLETED"
        else:
            success = False
            status = "FAILED" if self.move_count < optimal_total * 2 else "EXCEEDED_LIMIT"
        
        accuracy = (self.ai_correct_moves / self.move_count * 100) if self.move_count > 0 else 0
        efficiency = (optimal_total / self.move_count * 100) if self.move_count > 0 else 0
        
        results = {
            'num_disks': self.num_disks,
            'success': success,
            'status': status,
            'total_moves': self.move_count,
            'optimal_moves': optimal_total,
            'ai_correct_moves': self.ai_correct_moves,
            'accuracy_percent': round(accuracy, 1),
            'efficiency_percent': round(efficiency, 1),
            'move_details': self.test_results
        }
        
        self._display_final_results(results)
        return results
    
    def _display_final_results(self, results: dict):
        """Display comprehensive test results."""
        print("\n" + "="*60)
        print("🏁 TEST RESULTS")
        print("="*60)
        
        print(f"🗼 Disks: {results['num_disks']}")
        print(f"📊 Status: {results['status']}")
        print(f"✅ Success: {'YES' if results['success'] else 'NO'}")
        print(f"🎯 Total moves: {results['total_moves']}")
        print(f"⭐ Optimal moves: {results['optimal_moves']}")
        print(f"🎪 AI optimal moves: {results['ai_correct_moves']}/{results['total_moves']}")
        print(f"📈 Accuracy: {results['accuracy_percent']}%")
        print(f"⚡ Efficiency: {results['efficiency_percent']}%")
        
        if results['success']:
            if results['accuracy_percent'] == 100:
                print("\n🏆 PERFECT! AI solved optimally!")
            elif results['accuracy_percent'] >= 80:
                print("\n🥈 EXCELLENT! AI performed very well!")
            else:
                print("\n🥉 GOOD! AI completed but with suboptimal moves!")
        else:
            print(f"\n💔 AI failed to complete the puzzle")
            if results['total_moves'] >= results['optimal_moves'] * 2:
                print("   Exceeded maximum move limit")
        
        # Display final tower state if completed
        if results['success']:
            self.display.display_completion(results['total_moves'], results['optimal_moves'])


def main():
    """Main application entry point."""
    print("🗼 TOWERS OF HANOI - AI REASONING TEST 🗼")
    print("Testing AI models' ability to solve Towers of Hanoi puzzles")
    print("(Research validation after claims about reasoning model limitations)")
    print()
    
    # Get number of disks from user
    while True:
        try:
            num_disks = input("Enter number of disks (3-8 recommended): ").strip()
            num_disks = int(num_disks)
            if 1 <= num_disks <= 10:
                break
            else:
                print("Please enter a number between 1 and 10")
        except ValueError:
            print("Please enter a valid number")
    
    # Ask for auto mode
    auto_mode = input("Auto mode (no pauses between moves)? (y/n): ").lower().startswith('y')
    
    # Run the test
    tester = HanoiAITester(num_disks)
    results = tester.run_test(auto_mode)
    
    if 'error' not in results:
        print(f"\n💾 Test completed for {num_disks} disks")
        print(f"   AI accuracy: {results['accuracy_percent']}%")
        print(f"   AI efficiency: {results['efficiency_percent']}%")


if __name__ == "__main__":
    main()
