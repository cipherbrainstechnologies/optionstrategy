#!/usr/bin/env python3
"""
Setup script for Institutional AI Trade Engine.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Institutional AI Trade Engine...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create virtual environment
    if not run_command("python -m venv .venv", "Creating virtual environment"):
        sys.exit(1)
    
    # Determine activation script
    if os.name == 'nt':  # Windows
        activate_script = ".venv\\Scripts\\activate"
        pip_command = ".venv\\Scripts\\pip"
        python_command = ".venv\\Scripts\\python"
    else:  # Unix/Linux/MacOS
        activate_script = ".venv/bin/activate"
        pip_command = ".venv/bin/pip"
        python_command = ".venv/bin/python"
    
    # Upgrade pip
    if not run_command(f"{pip_command} install --upgrade pip", "Upgrading pip"):
        sys.exit(1)
    
    # Install dependencies
    if not run_command(f"{pip_command} install -e .", "Installing dependencies"):
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created. Please update with your credentials.")
    
    # Initialize database
    if not run_command(f"{python_command} -m src.storage.db", "Initializing database"):
        print("⚠️  Database initialization failed, but continuing...")
    
    # Seed instruments
    if not run_command(f"{python_command} scripts/seed_instruments.py --list nifty50", "Seeding Nifty 50 instruments"):
        print("⚠️  Instrument seeding failed, but continuing...")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your API credentials")
    print("2. Test Telegram connection: python -m src.alerts.telegram")
    print("3. Test scanner: python -m src.exec.scanner --dry")
    print("4. Start daemon: python -m src.daemon")
    print("\n🔧 Configuration files:")
    print("- .env: Environment variables and API keys")
    print("- trading_engine.log: Application logs")
    print("- trading_engine.db: SQLite database")

if __name__ == "__main__":
    main()