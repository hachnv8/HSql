# HSql Build Guide (Windows EXE)

This guide explains how to package HSql into a standalone executable file using PyInstaller.

## 1. Prerequisites
Ensure you have Python installed and you are in the project root directory.

## 2. Setup Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

## 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install pyinstaller pyodbc oracledb JayDeBeApi JPype1
```

## 4. Build the Executable
Run the following command to build a single, windowed executable:

```bash
pyinstaller --noconfirm --onefile --windowed --name "HSql" --add-data "components;components" --add-data "drivers;drivers" --hidden-import="pymysql" --hidden-import="sqlparse" --hidden-import="pyodbc" --hidden-import="oracledb" main.py
```

### Explanation of flags:
- `--onefile`: Bundle everything into one `.exe`.
- `--windowed` (or `-w`): Do not open a terminal console when running the app.
- `--name "HSql"`: The name of the resulting executable.
- `--add-data "components;components"`: Ensures your component modules are included correctly.
- `--hidden-import`: Manually includes libraries that might not be detected automatically.

## 5. Locate the Output
Once the process finishes, you will find the executable in the `dist/` folder:
- `dist/HSql.exe`

## 6. Important Notes
- **Database**: The `hsql.db` file will be created in the same directory as the `.exe` when you first run it.
- **Icons**: If you add any icons or external assets later, remember to include them using the `--add-data` flag.
