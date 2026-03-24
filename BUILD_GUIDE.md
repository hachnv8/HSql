# HSql Build Guide (Windows EXE)

This guide provides the exact steps to build the HSql executable on a production machine, including a workaround for the `JPype1` crash issue with PyInstaller 6+.

## 1. Prerequisites
- Python 3.11 installed.
- `HSql.spec` file (already in the project root).

## 2. Setup Virtual Environment (VENV)
**Crucial:** Always use a virtual environment within the project folder to avoid background process conflicts.

```bash
# 1. Navigate to the project root
# 2. Create the venv
py -3.11 -m venv venv

# 3. Activate the venv
# For Git Bash (Recommended):
source venv/Scripts/activate

# For Command Prompt:
venv\Scripts\activate

# For PowerShell:
.\venv\Scripts\Activate.ps1
```

## 3. Install Requirements
While the `(venv)` is active, run:
```bash
# Update pip
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install PyInstaller (Version 6.3 or higher)
pip install pyinstaller
```

## 4. Build the Executable
To prevent the `JPype1` analysis crash, we **must** use the custom `.spec` file instead of a one-line command:

```bash
# Run the build using the spec file
pyinstaller --noconfirm HSql.spec
```

### Why use `HSql.spec`?
The `HSql.spec` file is configured to:
1. **Manually collect** all `jpype` and `jaydebeapi` assets.
2. **Exclude** the modules from automatic analysis to prevent the `SubprocessDiedError` crash.

## 5. Locate Output
The final executable will be created in:
- `dist/HSql.exe`

## 6. Deployment Notes
- When moving the `HSql.exe` to another machine, you must also copy the `drivers/` folder (with `jt400.jar`) to the same location if you want to use DB2 features.
- Ensure the target machine has the **Java Runtime Environment (JRE)** installed for `jt400.jar` to work.
