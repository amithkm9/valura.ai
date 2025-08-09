# ===== 3. Installation Script =====
"""
install_dependencies.py
Script to install required dependencies and setup Ollama
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install all required Python packages"""
    
    print("Installing Python dependencies...")
    
    packages = [
        "gradio==4.16.0",
        "python-docx==1.1.0",
        "langchain==0.2.0",
        "langchain-community==0.0.20",
        "chromadb==0.4.22",
        "sentence-transformers==2.2.2",
        "ollama==0.1.7",
        "numpy==1.24.3",
        "faiss-cpu==1.7.4",
        "tiktoken==0.5.2",
        "torch==2.0.1",
        "transformers==4.30.0"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("\n✅ All dependencies installed successfully!")
    
    # Check if Ollama is installed
    print("\n🔍 Checking Ollama installation...")
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        print(f"✅ Ollama is installed: {result.stdout}")
    except FileNotFoundError:
        print("❌ Ollama is not installed!")
        print("Please install Ollama from: https://ollama.ai")
        print("After installation, run: ollama pull llama2")
        return False
    
    # Check if llama2 model is available
    print("\n🔍 Checking for llama2 model...")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "llama2" in result.stdout:
            print("✅ llama2 model is available")
        else:
            print("⚠️ llama2 model not found. Pulling model...")
            subprocess.run(["ollama", "pull", "llama2"])
            print("✅ llama2 model downloaded")
    except Exception as e:
        print(f"Error checking models: {e}")
    
    return True

if __name__ == "__main__":
    if install_dependencies():
        print("\n🎉 Setup complete! You can now run the application with:")
        print("python app.py")
    else:
        print("\n⚠️ Setup incomplete. Please install missing components.")