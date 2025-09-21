#!/usr/bin/env python3
"""
Setup script for Ollama integration with the multi-hop research agent.
This script helps users install and configure Ollama for use with the research agent.
"""

import subprocess
import sys
import os
import requests
import time


def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_ollama():
    """Install Ollama based on the operating system."""
    print("Installing Ollama...")
    
    if sys.platform == "win32":
        print("Please download and install Ollama from: https://ollama.ai/download")
        print("After installation, restart your terminal and run this script again.")
        return False
    elif sys.platform == "darwin":
        # macOS
        subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh', '|', 'sh'], shell=True)
    else:
        # Linux
        subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh', '|', 'sh'], shell=True)
    
    return True


def start_ollama_service():
    """Start the Ollama service."""
    print("Starting Ollama service...")
    try:
        if sys.platform == "win32":
            # On Windows, Ollama should start automatically after installation
            subprocess.run(['ollama', 'serve'], check=True)
        else:
            subprocess.run(['ollama', 'serve'], check=True)
    except subprocess.CalledProcessError:
        print("Failed to start Ollama service. Please start it manually.")
        return False
    return True


def check_ollama_running():
    """Check if Ollama service is running."""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except:
        return False


def pull_model(model_name="llama3.2"):
    """Pull a model from Ollama."""
    print(f"Pulling model: {model_name}")
    print("This may take several minutes depending on your internet connection...")
    
    try:
        subprocess.run(['ollama', 'pull', model_name], check=True)
        print(f"Successfully pulled {model_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to pull model: {e}")
        return False


def list_available_models():
    """List available models."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Available models:")
            print(result.stdout)
        else:
            print("No models available")
    except Exception as e:
        print(f"Error listing models: {e}")


def test_ollama_integration():
    """Test the Ollama integration."""
    print("Testing Ollama integration...")
    
    try:
        from ollama_client import OllamaClient
        client = OllamaClient()
        
        if client.is_available():
            print("✅ Ollama integration test successful!")
            
            # Test a simple generation
            response = client.generate_text("Hello, how are you?")
            print(f"Test response: {response[:100]}...")
            return True
        else:
            print("❌ Ollama integration test failed")
            return False
    except Exception as e:
        print(f"❌ Error testing Ollama integration: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up Ollama for Multi-hop Research Agent")
    print("=" * 50)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("Ollama is not installed.")
        if sys.platform == "win32":
            print("Please download and install Ollama from: https://ollama.ai/download")
            print("After installation, restart your terminal and run this script again.")
            return
        else:
            install_ollama()
    
    # Check if Ollama service is running
    if not check_ollama_running():
        print("Ollama service is not running. Starting it...")
        if not start_ollama_service():
            print("Please start Ollama manually: ollama serve")
            return
    
    # List current models
    print("\nCurrent models:")
    list_available_models()
    
    # Ask user which model to use
    print("\nRecommended models for research tasks:")
    print("1. llama3.2 (default, good balance of speed and quality)")
    print("2. llama3.2:13b (better quality, slower)")
    print("3. mistral (fast and efficient)")
    print("4. codellama (good for technical content)")
    
    choice = input("\nEnter model name (or press Enter for llama3.2): ").strip()
    model_name = choice if choice else "llama3.2"
    
    # Pull the model
    if not pull_model(model_name):
        print("Failed to pull model. Please try again.")
        return
    
    # Test integration
    print("\nTesting integration...")
    if test_ollama_integration():
        print("\n✅ Setup complete!")
        print(f"Your research agent is now configured to use {model_name}")
        print("\nTo start the research agent:")
        print("1. Activate your virtual environment: .venv\\Scripts\\activate")
        print("2. Start the API server: python app.py")
        print("3. Open frontend/index.html in your browser")
        
        # Create environment file
        with open('.env', 'w') as f:
            f.write(f"USE_OLLAMA=true\n")
            f.write(f"OLLAMA_MODEL={model_name}\n")
        print(f"\nConfiguration saved to .env file")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")


if __name__ == "__main__":
    main()

