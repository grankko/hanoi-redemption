#!/usr/bin/env python3
"""
Simple demonstration of enhanced AI context.
"""

print("🧪 ENHANCED AI CONTEXT DEMONSTRATION")
print("=" * 50)

print("\n🎯 NEW FEATURES IMPLEMENTED:")
print("✅ AI Context Enhancement:")
print("   • AI now sees last 3 MOVES + corresponding STATES")
print("   • Previous state visibility prevents cycling")
print("   • Rich historical context for strategic planning")

print("\n✅ System Prompt Enhancement:")
print("   • Added anti-cycling instructions")
print("   • Explicit warning about returning to previous states")
print("   • Better guidance for optimal path finding")

print("\n🚀 EXAMPLE ENHANCED PROMPT FORMAT:")
print("-" * 50)

example_prompt = """3-disk Towers of Hanoi puzzle - Turn #4

CURRENT STATE:
Tower A: [3]
Tower B: [1, 2]
Tower C: empty

RECENT GAME HISTORY:

--- Move 1 ---
State before move:
  Tower A: [1, 2, 3]
  Tower B: empty
  Tower C: empty
Move made: Move disk from tower A to tower C

--- Move 2 ---
State before move:
  Tower A: [2, 3]
  Tower B: empty
  Tower C: [1]
Move made: Move disk from tower A to tower B

--- Move 3 ---
State before move:
  Tower A: [3]
  Tower B: [2]
  Tower C: [1]
Move made: Move disk from tower C to tower B

NOTE: Avoid making moves that would return to any of the previous states shown above."""

print(example_prompt)
print("-" * 50)

print("\n🧠 STRATEGIC BENEFITS:")
print("   • AI can see progression patterns")
print("   • Prevents wasteful cycling between states")
print("   • Enables better forward planning")
print("   • More human-like problem-solving context")

print("\n✅ ENHANCEMENT COMPLETE!")
print("🚀 Ready for advanced AI reasoning testing!")
