#!/usr/bin/env python3
"""
Simple runner script for the OpenAPI Test Generator.
Works on both Windows and Mac/Linux.

Usage:
    python run.py setup      - Install dependencies
    python run.py api        - Start the FastAPI backend (port 8000)
    python run.py ui         - Start the Streamlit UI (port 8501)
    python run.py example    - Start the example API (port 8001)
    python run.py all        - Start all services (API + UI + Example)
    python run.py test       - Run all tests
    python run.py clean      - Clean generated files
"""

import subprocess
import sys
import os
import shutil
import time
from pathlib import Path

# Change to script directory
os.chdir(Path(__file__).parent)


def run_command(cmd, description=None):
    """Run a command and print output."""
    if description:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print(f"{'='*60}\n")

    # Use shell=True on Windows for better compatibility
    if sys.platform == "win32":
        result = subprocess.run(cmd, shell=True)
    else:
        result = subprocess.run(cmd, shell=True)

    return result.returncode == 0


def setup():
    """Install all dependencies."""
    print("\n" + "="*60)
    print("  Setting up OpenAPI Test Generator")
    print("="*60 + "\n")

    # Check Python version
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or higher is required")
        print(f"Current version: {sys.version}")
        return False

    print(f"Python version: {sys.version}")
    print("\nInstalling dependencies...")

    success = run_command(f"{sys.executable} -m pip install -r requirements.txt")

    if success:
        print("\n" + "="*60)
        print("  Setup complete!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Start the API:     python run.py api")
        print("  2. Start the UI:      python run.py ui")
        print("  3. Or start all:      python run.py all")
        print("\nThe UI will be available at: http://localhost:8501")
    else:
        print("\nSetup failed. Please check the error messages above.")

    return success


def start_api():
    """Start the FastAPI backend."""
    print("\nStarting FastAPI backend on http://localhost:8000 ...")
    print("Press Ctrl+C to stop\n")
    run_command(f"{sys.executable} -m uvicorn app.main:app --reload --port 8000")


def start_ui():
    """Start the Streamlit UI."""
    print("\nStarting Streamlit UI on http://localhost:8501 ...")
    print("Press Ctrl+C to stop\n")
    run_command(f"{sys.executable} -m streamlit run streamlit_app/app.py --server.port 8501")


def start_example():
    """Start the example target API."""
    print("\nStarting Example API on http://localhost:8001 ...")
    print("Press Ctrl+C to stop\n")
    run_command(f"{sys.executable} -m uvicorn example_api.main:app --reload --port 8001")


def start_all():
    """Start all services in separate processes."""
    print("\n" + "="*60)
    print("  Starting All Services")
    print("="*60)
    print("\nThis will start:")
    print("  - FastAPI Backend:  http://localhost:8000")
    print("  - Streamlit UI:     http://localhost:8501")
    print("  - Example API:      http://localhost:8001")
    print("\nPress Ctrl+C to stop all services\n")

    processes = []

    try:
        # Start API
        api_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        processes.append(("API", api_proc))
        print("Started: FastAPI Backend (port 8000)")

        # Start Example API
        example_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "example_api.main:app", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        processes.append(("Example", example_proc))
        print("Started: Example API (port 8001)")

        # Wait a moment for APIs to start
        time.sleep(2)

        # Start Streamlit (this one we let output to console)
        ui_proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "streamlit_app/app.py", "--server.port", "8501"],
        )
        processes.append(("UI", ui_proc))
        print("Started: Streamlit UI (port 8501)")

        print("\n" + "="*60)
        print("  All services running!")
        print("  Open http://localhost:8501 in your browser")
        print("="*60 + "\n")

        # Wait for UI process (main one)
        ui_proc.wait()

    except KeyboardInterrupt:
        print("\n\nStopping all services...")
    finally:
        for name, proc in processes:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            print(f"Stopped: {name}")
        print("All services stopped.")


def run_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("  Running Tests")
    print("="*60 + "\n")

    # Create test-results directory
    Path("test-results").mkdir(exist_ok=True)

    success = run_command(
        f"{sys.executable} -m pytest tests/ -v --tb=short"
    )

    if success:
        print("\n" + "="*60)
        print("  All tests passed!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("  Some tests failed. Check output above.")
        print("="*60)

    return success


def clean():
    """Clean generated files."""
    print("\nCleaning generated files...")

    dirs_to_clean = [
        "generated_tests",
        "data",
        "test-results",
        ".pytest_cache",
        "__pycache__",
    ]

    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)
            print(f"  Removed: {dir_name}/")

    # Clean __pycache__ in subdirectories
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)

    print("\nClean complete!")


def show_help():
    """Show help message."""
    print("""
============================================================
        OpenAPI Test Generator - Quick Start
============================================================

COMMANDS:
  python run.py setup      Install dependencies (run this first!)
  python run.py all        Start all services (recommended)
  python run.py api        Start only the FastAPI backend
  python run.py ui         Start only the Streamlit UI
  python run.py example    Start only the example target API
  python run.py test       Run all tests
  python run.py clean      Clean generated files

QUICK START:
  1. python run.py setup   (install dependencies)
  2. python run.py all     (start everything)
  3. Open http://localhost:8501 in your browser

PORTS:
  - Streamlit UI:     http://localhost:8501
  - FastAPI Backend:  http://localhost:8000
  - Example API:      http://localhost:8001
""")


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    commands = {
        "setup": setup,
        "install": setup,
        "api": start_api,
        "backend": start_api,
        "ui": start_ui,
        "frontend": start_ui,
        "example": start_example,
        "target": start_example,
        "all": start_all,
        "start": start_all,
        "test": run_tests,
        "tests": run_tests,
        "clean": clean,
        "help": show_help,
        "-h": show_help,
        "--help": show_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        show_help()


if __name__ == "__main__":
    main()
