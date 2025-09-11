#!/usr/bin/env python3

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False
    return True

def run_app():
    """Run the Flask application"""
    try:
        from app import app, init_db
        print("Starting Bread & Butter Flask Backend...")
        print("Admin panel will be available at: http://localhost:5002/admin/")
        print("API endpoints available at: http://localhost:5002/api/")
        app.run(debug=True, host='0.0.0.0', port=5002)
    except ImportError as e:
        print(f"Error importing app: {e}")
        print("Please make sure all requirements are installed.")
        return False
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("Bread & Butter Flask Backend Setup")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Run the application
    run_app()