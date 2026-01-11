# Setup Instructions

## Python Installation

### Check if Python is installed
```bash
python3 --version
```

You should see Python 3.7 or higher. If not, install Python:

### macOS
```bash
# Using Homebrew (recommended)
brew install python3

# Or download from python.org
# Visit https://www.python.org/downloads/
```

### Windows
1. Visit https://www.python.org/downloads/
2. Download Python 3.9 or higher
3. Run the installer
4. Make sure to check "Add Python to PATH" during installation

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
```

### Linux (RHEL/CentOS)
```bash
sudo yum install python3 python3-pip
```

## Verify Installation

After installing Python, verify it works:
```bash
python3 --version
```

You should see something like: `Python 3.9.6`

## Running the Simulation

No additional libraries are needed! The script uses only Python standard library modules.

Simply run:
```bash
cd /Users/johnsellers/mathospayment
python3 src/simulate_new_bonus_models.py
```

## Optional: Virtual Environment (Recommended for Python projects)

While not required for this project, using a virtual environment is a best practice:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Then run the script
python3 src/simulate_new_bonus_models.py
```

## Troubleshooting

### "python3: command not found"
- Make sure Python is installed and in your PATH
- Try `python --version` instead (some systems use `python` instead of `python3`)

### "ModuleNotFoundError"
- This project uses only standard library modules
- If you see this error, you may have a corrupted Python installation
- Try reinstalling Python

### Permission errors
- On macOS/Linux, you may need to use `python3` instead of `python`
- If using pip, you might need `pip3` instead of `pip`

## Current Status

✅ Python 3.9.6 is installed
✅ All required modules are available
✅ Script runs successfully

You're all set! Just run:
```bash
python3 src/simulate_new_bonus_models.py
```


