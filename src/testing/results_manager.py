"""
Results management for Towers of Hanoi AI tests.

This module handles test result generation, display, and export functionality.
"""

import json
import os
from datetime import datetime


class ResultsManager:
    """
    Manages test results including generation, display, and export.
    """
    
    def __init__(self, num_disks: int):
        self.num_disks = num_disks
    
    def generate_test_results(self, tester, optimal_moves: int, max_moves: int) -> dict:
        """Generate comprehensive test results with 3-outcome validation."""
        # Determine outcome based on completion and move count
        if tester.is_solved():
            if tester.move_count <= optimal_moves:
                # Solved within theoretical minimum
                success = True
                status = "OPTIMAL_SUCCESS"
            elif tester.move_count <= max_moves:
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
        
        # Calculate efficiency - only for completed games
        if tester.is_solved():
            efficiency = (optimal_moves / tester.move_count * 100) if tester.move_count > 0 else 0
        else:
            # Game not completed - efficiency is 0%
            efficiency = 0.0
        
        results = {
            'num_disks': self.num_disks,
            'success': success,
            'status': status,
            'total_moves': tester.move_count,
            'optimal_moves': optimal_moves,
            'max_moves': max_moves,
            'efficiency_percent': round(efficiency, 1),
            'exceeded_optimal': tester.move_count > optimal_moves,
            'exceeded_budget': tester.move_count > max_moves,
            'move_details': tester.test_results
        }
        
        return results
    
    def display_final_results(self, results: dict, tester):
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
        
        # Only show efficiency details for completed games
        if results['success']:
            print(f"⚡ Efficiency: {results['efficiency_percent']}%")
            print(f"🏆 Optimal: {'YES' if not results['exceeded_optimal'] else 'NO'}")
        else:
            print(f"⚡ Efficiency: N/A (game not completed)")
            print(f"🏆 Optimal: N/A")
            
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
            print(f"\n💔 FAILURE! AI did not solve the puzzle")
            if results['exceeded_budget']:
                print(f"   Used {results['total_moves']} moves, budget was {results['max_moves']}")
            else:
                print(f"   AI made invalid move or test was cancelled")
            print(f"   No efficiency calculated for incomplete games")
        
        # Display final tower state if completed
        if results['success']:
            tester.display.display_completion(results['total_moves'], results['optimal_moves'])
    
    def export_results(self, results: dict) -> str:
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
