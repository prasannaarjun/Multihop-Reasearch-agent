#!/usr/bin/env python3
"""
Development setup script for Multi-hop Research Agent
This script helps set up both the backend and frontend for development.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=shell, cwd=cwd, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def setup_frontend():
    """Set up the React frontend."""
    print("Setting up React frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("Frontend directory not found!")
        return False
    
    # Install npm dependencies
    print("Installing npm dependencies...")
    result = run_command("npm install", cwd=frontend_dir)
    if result is None:
        print("Failed to install npm dependencies")
        return False
    
    print("Frontend setup complete!")
    return True

def build_frontend():
    """Build the React frontend for production."""
    print("Building React frontend...")
    
    frontend_dir = Path("frontend")
    result = run_command("npm run build", cwd=frontend_dir)
    if result is None:
        print("Failed to build frontend")
        return False
    
    print("Frontend build complete!")
    return True

def main():
    """Main setup function."""
    print("Multi-hop Research Agent Development Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("Frontend setup failed!")
        sys.exit(1)
    
    # Build frontend
    if not build_frontend():
        print("Frontend build failed!")
        sys.exit(1)
    
    print("\nSetup complete!")
    print("\nTo start development:")
    print("1. Start the backend: python app.py")
    print("2. Start the frontend dev server: cd frontend && npm start")
    print("\nFor production:")
    print("1. Build the frontend: cd frontend && npm run build")
    print("2. Start the backend: python app.py")

if __name__ == "__main__":
    main()
