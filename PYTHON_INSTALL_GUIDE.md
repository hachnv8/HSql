# Python 3.11 Installation & Setup Guide

This guide describes how to install Python 3.11 and set up the `HSql` project environment on a new machine.

## 1. Install Python 3.11.9
1. **Download:** Go to the official [Python 3.11.9 Release Page](https://www.python.org/downloads/release/python-3119/) and download the **Windows installer (64-bit)**. Or use this direct link: [python-3.11.9-amd64.exe](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe).
2. **Run Installer:** Double-click the downloaded `.exe` file.
3. **Critical Step:** Make sure to check the box **"Add Python 3.11 to PATH"** at the bottom of the installer window.
4. **Complete Installation:** Follow the prompts to finish the installation.

## 2. Verify Installation
Open a new terminal (Command Prompt or PowerShell) and run:
```bash
py -3.11 --version
```
It should return `Python 3.11.9`.

## 3. Project Setup
Navigate to the project root directory (`HSql` folder) in your terminal.

### 3.1 Create Virtual Environment
Run the following command to create a virtual environment specifically with Python 3.11:
```bash
py -3.11 -m venv venv
```

### 3.2 Activate Virtual Environment
- **Windows (CMD):**
  ```cmd
  venv\Scripts\activate
  ```
- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Git Bash:**
  ```bash
  source venv/Scripts/activate
  ```

### 3.3 Update Pip
Once activated, run:
```bash
python -m pip install --upgrade pip
```

### 3.4 Install Dependencies
Install all required libraries from the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

## 4. Running the Application
While the `venv` is active, run the main script:
```bash
python main.py
```

---
**Note:** For building the executable, refer to the [BUILD_GUIDE.md](BUILD_GUIDE.md) file.
