# Towers of Hanoi AI Test

Tests AI reasoning models on the classic Towers of Hanoi puzzle. The AI gets up to double the theoretical minimum moves to solve the puzzle, with outcomes based on efficiency.

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

- AI gets up to 2x the theoretical minimum moves (2 * (2^n - 1)) to solve n disks
- AI receives context of the last 3 moves (more comparable to human problem-solving)
- Test stops when puzzle is solved or budget is exceeded
- Results auto-exported to `output/` with timestamps
- Efficiency calculated at end based on theoretical minimum

## Results

- **OPTIMAL_SUCCESS**: AI solved within theoretical minimum moves (2^n - 1)
- **SUCCESS**: AI solved within 2x budget but used more than minimum moves
- **FAILURE**: AI exceeded 2x budget or made invalid move