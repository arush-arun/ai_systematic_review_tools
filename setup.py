#!/usr/bin/env python3
"""
Setup script for AI-Powered Systematic Review Tools
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_requirements():
    """Install required packages."""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def create_sample_files():
    """Create sample input files."""
    print("📄 Creating sample input files...")
    
    # Create sample papers_to_screen.txt
    if not os.path.exists("papers_to_screen.txt"):
        with open("papers_to_screen.txt", "w") as f:
            f.write("# List your PDF files here for screening\n")
            f.write("# One filename per line, e.g.:\n")
            f.write("# fw_001.pdf\n")
            f.write("# fw_002.pdf\n")
        print("✅ Created papers_to_screen.txt")
    
    # Create sample files_to_process.txt
    if not os.path.exists("files_to_process.txt"):
        with open("files_to_process.txt", "w") as f:
            f.write("# List your PDF files here for data extraction\n")
            f.write("# One filename per line, e.g.:\n")
            f.write("# fw_003.pdf\n")
            f.write("# fw_004.pdf\n")
        print("✅ Created files_to_process.txt")

def check_api_setup():
    """Check if API keys are configured."""
    print("🔑 Checking API key configuration...")
    
    api_keys = {
        'ANTHROPIC_API_KEY': 'Claude',
        'OPENAI_API_KEY': 'OpenAI',
        'GEMINI_API_KEY': 'Gemini'
    }
    
    configured_keys = []
    for env_var, model_name in api_keys.items():
        if os.getenv(env_var):
            configured_keys.append(model_name)
            print(f"✅ {model_name} API key found")
        else:
            print(f"⚠️  {model_name} API key not found (set {env_var})")
    
    if configured_keys:
        print(f"✅ API keys configured for: {', '.join(configured_keys)}")
    else:
        print("⚠️  No API keys found in environment variables")
        print("   You can set them manually when running the scripts")

def main():
    """Main setup function."""
    print("🚀 AI-Powered Systematic Review Tools Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create sample files
    create_sample_files()
    
    # Check API setup
    check_api_setup()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n⚠️  IMPORTANT COST WARNING:")
    print("   These tools make API calls that consume credits/tokens.")
    print("   START WITH SMALL BATCHES (5-10 papers) to test costs.")
    print("   Monitor your API usage dashboards regularly!")
    print("\nNext steps:")
    print("1. Set up your API keys (see README.md)")
    print("2. Add 5-10 PDF filenames to papers_to_screen.txt (start small!)")
    print("3. Run: python3 systematic_review_ai.py")
    print("4. Choose Gemini for cost-effective testing")
    print("\nFor detailed instructions and cost estimates, see README.md")

if __name__ == "__main__":
    main()