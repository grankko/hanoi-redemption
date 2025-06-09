# VS Code Setup Guide

This project is configured for optimal development in VS Code. Here's how to use the setup:

## Quick Start

1. **Open in VS Code**: Open the project folder in VS Code
2. **Select Python Interpreter**: VS Code should automatically detect `.venv/bin/python`
3. **Install Extensions** (if prompted):
   - Python
   - Python Debugger

## Running the Application

### Method 1: Using Tasks (F5)
- **F5**: Run main AI test application
- **Ctrl+F5**: Run as Python module
- **Shift+F5**: Run optimal demo

### Method 2: Using Command Palette
1. Press `Ctrl+Shift+P`
2. Type "Tasks: Run Task"
3. Select from available tasks:
   - Run Hanoi AI Test
   - Run Demo Optimal
   - Test Components
   - Install Dependencies

### Method 3: Using Terminal
```bash
# Activate virtual environment
source .venv/bin/activate

# Run application
python run.py
# OR
python -m src.main
```

## Debugging

### Start Debugging
1. **F5** (or click Run and Debug)
2. Select debug configuration:
   - **Debug Hanoi AI Test**: Main application with launcher
   - **Debug Hanoi AI Test (Module)**: Run as Python module
   - **Debug Demo Optimal**: Demo optimal solver
   - **Debug Test Components**: Component tests

### Setting Breakpoints
- Click in the gutter next to line numbers
- Or press F9 on the line you want to break at

### Debug Features Available
- Step through code (F10, F11)
- Variable inspection
- Call stack viewing
- Interactive debugging console

## Project Structure
```
.vscode/
├── launch.json      # Debug configurations
├── tasks.json       # Build/run tasks
├── settings.json    # Python interpreter and workspace settings
└── keybindings.json # F5 shortcuts
```

## Environment Setup
The configuration automatically:
- Uses `.venv/bin/python` as the Python interpreter
- Sets up PYTHONPATH for proper imports
- Activates virtual environment in integrated terminal
- Excludes `__pycache__` files from explorer

## Troubleshooting

### Python Interpreter Issues
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose `./.venv/bin/python`

### Import Errors
- Ensure virtual environment is activated
- Check that PYTHONPATH includes workspace folder
- Restart VS Code if needed

### Task Not Running
- Ensure you're in the project root directory
- Check that virtual environment exists: `.venv/bin/python`
- Run "Install Dependencies" task first if needed
