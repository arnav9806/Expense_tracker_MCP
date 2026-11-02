# Expense Tracker MCP

An Expense Tracker application powered by the Model Context Protocol (MCP), built using Python and FastMCP.

This README explains how to set up the development environment, install dependencies using `uv`, activate the virtual environment, and run the project on Windows.

## 1. Prerequisites

Before starting, make sure you have:

- Windows 10 or Windows 11
- Python 3.10 or newer
- pip (Python package manager)
- uv (Python package and project manager)
- Git (optional)

Check Python installation:

```powershell
python --version
```

If Python is not recognized, try:

```powershell
py --version
```

If neither command works, locate your Python installation and use its full executable path.

## 2. Install uv

`uv` is a fast Python package and project manager. We use it to create virtual environments and install project dependencies.

Install uv using pip:

```powershell
python -m pip install uv
```

If Python is not recognized, use the full Python executable path:

```powershell
& "C:\Users\developer\AppData\Local\Python\pythoncore-3.15-64\python.exe" -m pip install uv
```

Verify the installation:

```powershell
python -m uv --version
```

Alternatively, if `uv` is available in PATH:

```powershell
uv --version
```

## 3. Clone or Open the Project

Navigate to your project directory:

```powershell
cd C:\Users\developer\Downloads\Expense_tracker_MCP-main\Expense_tracker_MCP-main
```

Make sure the project contains the following file:

```text
requirements.txt
```

## 4. Create a Virtual Environment

A virtual environment keeps project dependencies isolated from other Python projects.

Create the environment using:

```powershell
python -m uv venv
```

If Python is not recognized, use:

```powershell
& "C:\Users\developer\AppData\Local\Python\pythoncore-3.15-64\python.exe" -m uv venv
```

This creates a `.venv` directory inside the project.

Expected structure:

```text
Expense_tracker_MCP/
│
├── .venv/
├── requirements.txt
├── README.md
└── project files...
```

## 5. Activate the Virtual Environment

For Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

After activation, your terminal should look similar to:

```text
(.venv) PS C:\Users\developer\Downloads\Expense_tracker_MCP-main>
```

### If PowerShell blocks activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```

This changes the execution policy only for the current PowerShell session.

## 6. Configure requirements.txt

Add the following dependency to your `requirements.txt`:

```text
fastmcp==2.11.3
```

This ensures that the project uses FastMCP version 2.11.3.

Keep the other dependencies required by your project in this file.

## 7. Install Project Dependencies Using uv

With the virtual environment activated, install all dependencies:

```powershell
uv pip install -r requirements.txt
```

### Important: If uv is not recognized

On some Windows systems, `uv` is installed but its executable directory is not added to PATH.

In that case, use the full executable path:

```powershell
& "C:\Users\developer\AppData\Local\Python\pythoncore-3.15-64\Scripts\uv.exe" pip install -r requirements.txt
```

This installs dependencies into the currently activated virtual environment.

## 8. Verify FastMCP Installation

Check the installed FastMCP version:

```powershell
python -m pip show fastmcp
```

Expected output:

```text
Name: fastmcp
Version: 2.11.3
```

You can also verify it through Python:

```powershell
python -c "from fastmcp import FastMCP; print('FastMCP installed successfully')"
```

Expected output:

```text
FastMCP installed successfully
```

## 9. Basic FastMCP Example

You can create a basic MCP server using FastMCP.

Create a file named `server.py`:

```python
from fastmcp import FastMCP

mcp = FastMCP("Expense Tracker MCP")


@mcp.tool()
def add_expense(amount: float, category: str, description: str):
    """Add a new expense."""
    return {
        "amount": amount,
        "category": category,
        "description": description,
        "status": "Expense added successfully"
    }


if __name__ == "__main__":
    mcp.run()
```

Run the server:

```powershell
python server.py
```

This is a basic example to verify FastMCP functionality. Adapt it to your existing project structure and tools.

## 10. Common Commands

| Task | Command |
|---|---|
| Check Python version | `python --version` |
| Check uv version | `python -m uv --version` |
| Create virtual environment | `uv venv` |
| Activate environment | `.venv\Scripts\Activate.ps1` |
| Install requirements | `uv pip install -r requirements.txt` |
| Install FastMCP | `uv pip install fastmcp==2.11.3` |
| Check FastMCP | `python -m pip show fastmcp` |
| Deactivate environment | `deactivate` |

## 11. Troubleshooting

### Issue 1: Python is not recognized

Error:

```text
Python was not found; run without arguments to install from the Microsoft Store.
```

Solution:

Use the full Python executable path:

```powershell
& "C:\Users\developer\AppData\Local\Python\pythoncore-3.15-64\python.exe" --version
```

You can also add your Python installation directory to the Windows PATH environment variable.

### Issue 2: uv is not recognized

Error:

```text
uv : The term 'uv' is not recognized as the name of a cmdlet.
```

Solution:

Use the full uv executable path:

```powershell
& "C:\Users\developer\AppData\Local\Python\pythoncore-3.15-64\Scripts\uv.exe" --version
```

For dependency installation:

```powershell
& "C:\Users\developer\AppData\Local\Python\pythoncore-3.15-64\Scripts\uv.exe" pip install -r requirements.txt
```

### Issue 3: Virtual environment activation is blocked

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.venv\Scripts\Activate.ps1
```

### Issue 4: FastMCP version mismatch

Run:

```powershell
uv pip install fastmcp==2.11.3
```

Verify:

```powershell
python -m pip show fastmcp
```

## 12. Recommended Setup Workflow

Every time you start working on the project:

**First: Open PowerShell and navigate to the project.**

```powershell
cd C:\Users\developer\Downloads\Expense_tracker_MCP-main\Expense_tracker_MCP-main
```

**Second: Activate the virtual environment.**

```powershell
.venv\Scripts\Activate.ps1
```

**Third: Install dependencies if requirements have changed.**

```powershell
& "C:\Users\developer\AppData\Local\Python\pythoncore-3.15-64\Scripts\uv.exe" pip install -r requirements.txt
```

**Fourth: Start your application.**

```powershell
python server.py
```

Replace `server.py` with your actual application entry-point filename if it is different.

---

## Important Notes

- Always activate the virtual environment before installing or running project dependencies.
- Keep `fastmcp==2.11.3` pinned in `requirements.txt`.
- Do not commit `.venv/` to Git.
- Keep `requirements.txt` updated when adding new dependencies.
- Do not commit API keys, database credentials, or other secrets.
- Use the project's actual entry point when starting the MCP server.

## Useful Resources

- Python: https://www.python.org/
- uv Documentation: https://docs.astral.sh/uv/
- FastMCP Documentation: https://gofastmcp.com/
- MCP Documentation: https://modelcontextprotocol.io/