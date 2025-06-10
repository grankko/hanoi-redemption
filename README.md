# Towers of Hanoi AI Test

Tests AI reasoning models on the classic Towers of Hanoi puzzle. The AI gets up to double the theoretical minimum moves to solve the puzzle, with outcomes based on efficiency.

No, this does not test the exact same scenario from that [Apple paper](https://ml-site.cdn-apple.com/papers/the-illusion-of-thinking.pdf).

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
python run.py

# Auto mode (no pauses)
python run.py 4 --auto

```

## How it works

- AI gets up to 2x the theoretical minimum moves (2 * (2^n - 1)) to solve n disks
- AI receives **comprehensive enhanced context**: last 3 moves + corresponding previous game states + previous reasoning
- AI can learn from its own past reasoning patterns and build upon successful strategies
- AI is instructed to avoid cycling back to previous states (prevents inefficient loops)
- Test stops when puzzle is solved, when an invalid move is detected, or when the budget is exceeded
- Results auto-exported to `output/` with timestamps
- **Efficiency calculated only for completed games** - incomplete games show "N/A"

## Results

- **OPTIMAL_SUCCESS**: AI solved within theoretical minimum moves (2^n - 1)
- **SUCCESS**: AI solved within 2x budget but used more than minimum moves
- **FAILURE**: AI exceeded 2x budget or made invalid move