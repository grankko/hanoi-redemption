# Towers of Hanoi AI Test

Tests AI reasoning models on the classic Towers of Hanoi puzzle. The AI gets a strict budget of optimal moves (2^n - 1) to solve the puzzle.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set OpenAI API key:**
```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=your_key_here
```

## Usage

```bash
# Interactive mode
python -m src.main

# Auto mode (no pauses)
python -m src.main 4 --auto

# Demo optimal solution (no API key needed)
python demo_optimal.py
```

## How it works

- AI gets exactly 2^n - 1 moves to solve n disks
- Test fails if AI exceeds this optimal budget
- Results auto-exported to `output/` with timestamps
- Multiple optimal solutions exist, any path within budget counts as success

## Results

- **SUCCESS**: AI solved within the optimal move budget (2^n - 1 moves)
- **FAILURE**: AI exceeded budget or made invalid move

Built to validate research claims about AI reasoning limitations on recursive problems.