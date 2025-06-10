"""
Towers of Hanoi AI Testing - Research Validation
Tests AI reasoning models' ability to solve Towers of Hanoi puzzles.
"""

import sys
import argparse
import json
import os
from datetime import datetime
from typing import Optional

# Try absolute import first, fallback to relative
try:
    from src.api import HanoiAIClient
    from src.game import TowersOfHanoi
    from src.schemas import HanoiMove
    from src.display import TowerDisplay
except ImportError:
    from .api import HanoiAIClient
    from .game import TowersOfHanoi
    from .schemas import HanoiMove
    from .display import TowerDisplay


class HanoiAITester:
    """
    Tests AI reasoning models on Towers of Hanoi puzzles.
    """
    
    def __init__(self, num_disks: int):
        self.num_disks = num_disks
        self.game = TowersOfHanoi(num_disks)
        self.display = TowerDisplay(num_disks)
        self.ai_client = None
        self.move_count = 0
        self.test_results = []
        self.recent_moves = []  # Track last 3 moves for context
        self.recent_states = []  # Track states corresponding to recent moves
        
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
        """Create a detailed game state description for the AI with recent move and state context."""
        towers = self.game.state
        
        prompt = f"""{self.num_disks}-disk Towers of Hanoi puzzle - Turn #{self.move_count + 1}

CURRENT STATE:
Tower A: {towers.tower_a if towers.tower_a else 'empty'}
Tower B: {towers.tower_b if towers.tower_b else 'empty'}  
Tower C: {towers.tower_c if towers.tower_c else 'empty'}"""

        # Add recent moves and states context (last 3 moves)
        if self.recent_moves and self.recent_states:
            prompt += f"\n\nRECENT GAME HISTORY:"
            recent_moves_to_show = self.recent_moves[-3:]  # Get last 3 moves
            recent_states_to_show = self.recent_states[-3:]  # Get last 3 corresponding states
            start_move_num = max(1, self.move_count - len(recent_moves_to_show) + 1)
            
            for i, (move, state_before) in enumerate(zip(recent_moves_to_show, recent_states_to_show)):
                move_num = start_move_num + i
                prompt += f"\n\n--- Move {move_num} ---"
                prompt += f"\nState before move:"
                prompt += f"\n  Tower A: {state_before['tower_a'] if state_before['tower_a'] else 'empty'}"
                prompt += f"\n  Tower B: {state_before['tower_b'] if state_before['tower_b'] else 'empty'}"
                prompt += f"\n  Tower C: {state_before['tower_c'] if state_before['tower_c'] else 'empty'}"
                prompt += f"\nMove made: {move}"

        prompt += f"\n\nNOTE: Avoid making moves that would return to any of the previous states shown above."

        return prompt
    
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
        
        # Calculate move budgets
        optimal_moves = (2 ** self.num_disks) - 1
        max_moves = optimal_moves * 2  # Double the optimal for maximum allowed
        
        print(f"📊 Theoretical minimum moves for {self.num_disks} disks: {optimal_moves}")
        print(f"🤖 AI has budget of {max_moves} moves to solve this puzzle")
        print(f"🏆 Optimal completion: {optimal_moves} moves")
        print(f"🧠 Testing AI reasoning capability...")
        print()
        
        # Main game loop
        while not self.game.is_solved() and self.move_count < max_moves:
            print(f"\n--- Turn #{self.move_count + 1} ---")
            print(f"💰 Moves remaining in budget: {max_moves - self.move_count}")
            
            # Get AI's move
            print("🤖 AI is thinking...")
            ai_move_result = self.get_ai_move()
            if ai_move_result is None:
                print("❌ Failed to get AI move")
                break
            ai_move, ai_reasoning = ai_move_result
            
            print(f"🎯 AI suggests: Move disk from {ai_move.source_tower} to {ai_move.destination_tower}")
            print(f"💭 AI reasoning: {ai_reasoning}")
            
            # Validate the move (only check if it's valid, not optimal)
            is_valid, error_msg = self.game.is_valid_move(ai_move)
            
            if is_valid:
                print("✅ AI move is VALID")
            else:
                print(f"❌ AI move is INVALID: {error_msg}")
            
            # Record the result
            self.test_results.append({
                'turn': self.move_count + 1,
                'ai_move': {'source': ai_move.source_tower, 'destination': ai_move.destination_tower},
                'is_valid': is_valid,
                'ai_reasoning': ai_reasoning
            })
            
            # Execute the move if valid
            if is_valid:
                # Capture the current state BEFORE making the move
                state_before_move = {
                    'tower_a': self.game.state.tower_a.copy(),
                    'tower_b': self.game.state.tower_b.copy(),
                    'tower_c': self.game.state.tower_c.copy()
                }
                
                success = self.game.make_move(ai_move)
                if success:
                    self.move_count += 1
                    
                    # Track recent moves and states for context (keep last 3)
                    self.recent_moves.append(ai_move)
                    self.recent_states.append(state_before_move)
                    
                    # Keep only last 3 items in both lists
                    if len(self.recent_moves) > 3:
                        self.recent_moves.pop(0)  # Remove oldest move
                        self.recent_states.pop(0)  # Remove oldest state
                    
                    # Display updated state
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
        
        # Check if AI exceeded budget
        if self.move_count >= max_moves and not self.game.is_solved():
            print(f"\n💸 AI EXCEEDED MOVE BUDGET!")
            print(f"   Used {self.move_count} moves, budget was {max_moves}")
            print("   AI failed to solve within budget")
        
        # Test completed - show results
        return self._generate_test_results(optimal_moves, max_moves)
    
    def _generate_test_results(self, optimal_moves: int, max_moves: int) -> dict:
        """Generate comprehensive test results with 3-outcome validation."""
        # Determine outcome based on completion and move count
        if self.game.is_solved():
            if self.move_count <= optimal_moves:
                # Solved within theoretical minimum
                success = True
                status = "OPTIMAL_SUCCESS"
            elif self.move_count <= max_moves:
                # Solved within 2x budget
                success = True
                status = "SUCCESS"
            else:
                # This shouldn't happen due to loop condition, but safety check
                success = False
                status = "FAILURE"
        else:
            # Not solved (either exceeded budget or invalid move)
            success = False
            status = "FAILURE"
        
        # Calculate efficiency
        efficiency = (optimal_moves / self.move_count * 100) if self.move_count > 0 else 0
        
        results = {
            'num_disks': self.num_disks,
            'success': success,
            'status': status,
            'total_moves': self.move_count,
            'optimal_moves': optimal_moves,
            'max_moves': max_moves,
            'efficiency_percent': round(efficiency, 1),
            'exceeded_optimal': self.move_count > optimal_moves,
            'exceeded_budget': self.move_count > max_moves,
            'move_details': self.test_results
        }
        
        self._display_final_results(results)
        
        # Automatically export results to JSON file
        exported_file = self._export_results(results)
        if exported_file:
            print(f"📄 Results exported to: {exported_file}")
        
        return results
    
    def _display_final_results(self, results: dict):
        """Display comprehensive test results."""
        print("\n" + "="*60)
        print("🏁 TEST RESULTS")
        print("="*60)
        
        print(f"🗼 Disks: {results['num_disks']}")
        print(f"📊 Status: {results['status']}")
        print(f"✅ Success: {'YES' if results['success'] else 'NO'}")
        print(f"🎯 Moves used: {results['total_moves']}")
        print(f"⭐ Optimal moves: {results['optimal_moves']}")
        print(f"💰 Max budget: {results['max_moves']}")
        print(f"⚡ Efficiency: {results['efficiency_percent']}%")
        print(f"🏆 Optimal: {'YES' if not results['exceeded_optimal'] else 'NO'}")
        print(f"💸 Budget exceeded: {'YES' if results['exceeded_budget'] else 'NO'}")
        
        if results['success']:
            if results['status'] == "OPTIMAL_SUCCESS":
                print("\n🏆 OPTIMAL SUCCESS! AI solved within theoretical minimum!")
                print(f"   Used {results['total_moves']}/{results['optimal_moves']} moves (perfect efficiency)")
            else:  # SUCCESS
                print("\n🥈 SUCCESS! AI solved within budget!")
                print(f"   Used {results['total_moves']}/{results['max_moves']} moves")
                print(f"   Efficiency: {results['efficiency_percent']}%")
        else:
            print(f"\n💔 FAILURE! AI did not solve within budget")
            if results['exceeded_budget']:
                print(f"   Used {results['total_moves']} moves, budget was {results['max_moves']}")
            else:
                print(f"   AI made invalid move or couldn't complete puzzle")
        
        # Display final tower state if completed
        if results['success']:
            self.display.display_completion(results['total_moves'], results['optimal_moves'])

    def _export_results(self, results: dict) -> str:
        """Export test results to a timestamped JSON file."""
        try:
            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hanoi_test_{self.num_disks}disks_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Add metadata to results
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'export_info': {
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'disk_count': self.num_disks,
                    'test_type': 'AI_reasoning_validation'
                },
                'results': results
            }
            
            # Export to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            return filepath
        except Exception as e:
            print(f"⚠️  Warning: Failed to export results: {e}")
            return ""

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
    print("(Research validation after claims about reasoning model limitations)")
    print()
    
    # Get number of disks
    if args.num_disks:
        num_disks = args.num_disks
        if not (1 <= num_disks <= 10):
            print("Error: Number of disks must be between 1 and 10")
            sys.exit(1)
    else:
        # Interactive mode if no argument provided
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
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                sys.exit(0)
    
    # Run the test
    tester = HanoiAITester(num_disks)
    results = tester.run_test(auto_mode=args.auto)
    
    if 'error' not in results:
        print(f"\n💾 Test completed for {num_disks} disks")
        print(f"   Status: {results['status']}")
        print(f"   Moves: {results['total_moves']}/{results['max_moves']}")
        print(f"   Efficiency: {results['efficiency_percent']}%")


if __name__ == "__main__":
    main()
