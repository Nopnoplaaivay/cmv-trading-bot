"""
Startup script to run both FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def check_python():
    """Check if Python is available"""
    try:
        result = subprocess.run(
            [sys.executable, "--version"], capture_output=True, text=True
        )
        print(f"Python found: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"Python not found: {e}")
        return False


def install_requirements():
    """Install required packages"""
    requirements_file = Path("streamlit_requirements.txt")
    if requirements_file.exists():
        print("Installing Streamlit requirements...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "streamlit_requirements.txt"]
        )

    backend_requirements = Path("requirements.txt")
    if backend_requirements.exists():
        print("Installing backend requirements...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )


def start_backend():
    """Start FastAPI backend"""
    print("Starting FastAPI backend on http://localhost:8000...")
    try:
        backend_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.app:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ]
        )
        return backend_process
    except Exception as e:
        print(f"Failed to start backend: {e}")
        return None


def start_frontend():
    """Start Streamlit frontend"""
    print("Starting Streamlit frontend on http://localhost:8501...")
    try:
        frontend_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "streamlit_enhanced.py",
                "--server.port",
                "8501",
                "--server.address",
                "0.0.0.0",
            ]
        )
        return frontend_process
    except Exception as e:
        print(f"Failed to start frontend: {e}")
        return None


def main():
    """Main startup function"""
    print("CMV Trading Bot - Full Stack Startup")
    print("=" * 50)

    # Check Python
    if not check_python():
        input("Press Enter to exit...")
        return

    # Install requirements
    # try:
    #     install_requirements()
    # except Exception as e:
    #     print(f"Warning: Failed to install some requirements: {e}")

    print("\n Starting services...")

    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("Failed to start backend. Exiting...")
        input("Press Enter to exit...")
        return

    # Wait a bit for backend to start
    print("Waiting for backend to start...")
    time.sleep(20)

    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("Failed to start frontend. Stopping backend...")
        backend_process.terminate()
        input("Press Enter to exit...")
        return

    # Wait a bit for frontend to start
    print("Waiting for frontend to start...")
    time.sleep(3)

    print("\nBoth services started successfully!")
    print("Backend API: http://localhost:8000")
    print("Frontend UI: http://localhost:8501")
    print("API Docs: http://localhost:8000/docs")

    # Open browser
    try:
        print("\nOpening browser...")
        webbrowser.open("http://localhost:8501")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

    print("\nTips:")
    print("  - Use Ctrl+C to stop both services")
    print("  - Backend runs on port 8000, Frontend on port 8501")
    print("  - Check the terminal for any error messages")

    try:
        # Keep the script running
        print("\nServices are running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")

        # Terminate processes
        if frontend_process:
            frontend_process.terminate()
            print("Frontend stopped")

        if backend_process:
            backend_process.terminate()
            print("Backend stopped")

        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
