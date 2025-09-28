#!/usr/bin/env python3
"""
Launch script for Streamlit web interface.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit app."""
    
    # Set PYTHONPATH to current directory
    os.environ['PYTHONPATH'] = str(Path.cwd())
    
    print("🚀 Launching Encrypted LLM Chat (Streamlit)")
    print("=" * 50)
    print("🔧 Setting up environment...")
    print(f"📁 Working directory: {Path.cwd()}")
    print(f"🐍 Python path: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Check if certificates exist
    certs_dir = Path("certs")
    if not certs_dir.exists() or not any(certs_dir.glob("*.pem")):
        print("\n⚠️  Warning: No certificates found!")
        print("Please run: python crypto/generate_certs.py")
        print("Or: python crypto/generate_certs.py --ecc")
        print()
    
    # Launch Streamlit
    try:
        print("🌐 Starting Streamlit server...")
        print("📱 The app will open in your browser automatically")
        print("🔗 Manual URL: http://localhost:8501")
        print("\n💡 Tip: Use Ctrl+C to stop the server")
        print("-" * 50)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "ui/streamlit_app.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Streamlit server stopped.")
    except Exception as e:
        print(f"❌ Failed to launch Streamlit: {e}")
        print("\nTry running manually:")
        print("streamlit run ui/streamlit_app.py")


if __name__ == "__main__":
    main()
