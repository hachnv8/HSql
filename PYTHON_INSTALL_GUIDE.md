# Python 3.11 Installation & Setup Guide

This guide describes how to install Python 3.11 and set up the `HSql` project environment on any Windows machine (Local or Production).

## 1. Install Python 3.11.9
1. **Download:** [python-3.11.9-amd64.exe](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)
2. **Run Installer:** Double-click the `.exe`.
3. **Critical Step:** Check the box **"Add Python 3.11 to PATH"** at the bottom of the installer window.
4. **Complete Installation.**

## 2. Verify Installation
Open a terminal (CMD, PowerShell, or Git Bash):
```bash
# Try one of these commands
python --version
py -3.11 --version
```
It should return `Python 3.11.9`.

## 3. Project Setup (VENV)
Navigate to the `HSql` folder in your terminal.

### 3.1 Create Virtual Environment
```bash
# Use 'py -3.11' if you have multiple Python versions, or 'python' if 3.11 is your only version
py -3.11 -m venv venv
```

### 3.2 Activate Virtual Environment
- **Git Bash:** `source venv/Scripts/activate`
- **CMD:** `venv\Scripts\activate`
- **PowerShell:** `.\venv\Scripts\Activate.ps1`

### 3.3 Install Dependencies
While the `(venv)` is active:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Run or Build
- **Run:** `python main.py`
- **Build EXE:** See [BUILD_GUIDE.md](BUILD_GUIDE.md) for steps using the `.spec` file.
