# Towers of Hanoi AI Reasoning Test

This application tests AI reasoning models' ability to solve Towers of Hanoi puzzles, validating their performance against optimal solutions. Built in response to research claims about reasoning models failing on Towers of Hanoi with higher disk counts.

## Features

- 🧪 **AI Reasoning Testing** - Test AI models on Towers of Hanoi puzzles
- 🎯 **Accuracy Tracking** - Compare AI moves against optimal solutions  
- ⚡ **Efficiency Analysis** - Measure how efficiently AI solves puzzles
- 📊 **Comprehensive Reporting** - Detailed test results and statistics
- 🎮 **Interactive & Auto Modes** - Step-through or automatic testing
- 🔒 **Type-safe schemas** with Pydantic validation and OpenAI structured outputs
- 🗼 **ASCII Art Display** - Visual representation of tower states

## Setup

1. **Clone and navigate to the project:**
```bash
cd /path/to/hanoi-redemption
```

2. **Create and activate a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up your OpenAI API key:**
```bash
# Create a .env file
cp .env.example .env
# Edit .env and add your API key:
# OPENAI_API_KEY=your_actual_api_key_here
```

## Usage

### Run the AI Reasoning Test
```bash
# Run as a module (recommended)
python -m src.main

# Or test optimal solver demo (no API key needed)
python demo_optimal.py
```

Choose number of disks (3-8 recommended) and auto/interactive mode:
- **Interactive mode** - Confirm each AI move manually
- **Auto mode** - Run test automatically without pauses

### Test Results
The application provides comprehensive analysis:
- **Accuracy**: Percentage of AI moves that match optimal solution
- **Efficiency**: How close AI's total moves are to optimal
- **Success**: Whether AI completed the puzzle
- **Move-by-move comparison** with optimal solution

## Project Structure

```
hanoi-redemption/
├── src/                    # Source code
│   ├── main.py            # Main AI testing application
│   ├── schemas/           # Pydantic models for structured outputs
│   │   ├── hanoi_move.py  # HanoiMove, HanoiGameState, HanoiMoveResponse
│   │   └── __init__.py
│   ├── game/              # Game logic and validation
│   │   ├── towers_of_hanoi.py  # TowersOfHanoi game class
│   │   ├── optimal_solver.py   # Optimal solution generator
│   │   └── __init__.py
│   ├── api/               # OpenAI client integration
│   │   ├── openai_client.py    # HanoiAIClient for structured outputs
│   │   └── __init__.py
│   └── display/           # ASCII art visualization
│       ├── display.py     # TowerDisplay for game visualization
│       └── __init__.py
├── demo_optimal.py        # Demo of optimal solution (no API key needed)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Structured Output Schemas

The application defines three main Pydantic schemas for OpenAI structured outputs:

### 1. HanoiMove
Represents a single move in the game:
```python
class HanoiMove(BaseModel):
    source_tower: Literal["A", "B", "C"]      # Tower to move from
    destination_tower: Literal["A", "B", "C"]  # Tower to move to
```

### 2. HanoiGameState  
Represents the current state of all towers:
```python
class HanoiGameState(BaseModel):
    tower_a: list[int]  # Disks on tower A (top to bottom)
    tower_b: list[int]  # Disks on tower B (top to bottom)  
    tower_c: list[int]  # Disks on tower C (top to bottom)
```

### 3. HanoiMoveResponse
The AI's response with move and reasoning:
```python
class HanoiMoveResponse(BaseModel):
    move: HanoiMove        # The suggested move
    reasoning: str         # AI's explanation
```

## Research Context

This project investigates claims about AI reasoning model limitations on Towers of Hanoi puzzles. Recent research suggested that reasoning models struggle with this classic recursive problem, particularly with higher disk counts.

**Test Approach:**
- Compare AI moves against mathematically optimal solutions
- Track accuracy and efficiency across different disk counts  
- Analyze failure patterns and suboptimal move sequences
- Validate whether claims about reasoning model limitations hold true

**Expected Results:**
- Perfect accuracy (100%) means AI matches optimal solution exactly
- High efficiency (close to 100%) means AI solves in near-optimal moves
- Failure patterns may reveal specific reasoning limitations

## Game Rules

**Towers of Hanoi Rules:**
- Only move one disk at a time
- Only move the top disk from a tower
- Never place a larger disk on top of a smaller disk
- Goal: Move all disks to tower C

**Disk Notation:**
- Smaller numbers = smaller disks
- Example: `[1, 2, 3]` means disk 1 (smallest) is on top

## Development

### Running Tests
```bash
# Test basic functionality
python test_basic.py

# Test specific components
python -c "
import sys; sys.path.insert(0, 'src')
from src.schemas import HanoiMove
move = HanoiMove(source_tower='A', destination_tower='B')
print('✅ Schema validation works!')
"
```

### Example Usage in Code
```python
from src.main import HanoiAITester

# Create tester for 4-disk puzzle
tester = HanoiAITester(4)

# Run test in auto mode
results = tester.run_test(auto_mode=True)

# Analyze results
print(f"AI Accuracy: {results['accuracy_percent']}%")
print(f"AI Efficiency: {results['efficiency_percent']}%") 
print(f"Success: {results['success']}")

# Access detailed move-by-move data
for move_data in results['move_details']:
    print(f"Turn {move_data['turn']}: AI={move_data['ai_move']}, Optimal={move_data['optimal_move']}")
```

## Dependencies

- **openai** - OpenAI API client with structured outputs support
- **pydantic** - Data validation using Python type annotations  
- **python-dotenv** - Environment variable management

## License

This project is for research purposes, investigating AI reasoning capabilities on the Towers of Hanoi puzzle. Built to validate claims about reasoning model limitations.
