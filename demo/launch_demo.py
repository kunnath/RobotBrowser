# Create a launch script for easy startup
import subprocess
import sys
import os

def main():
    """Launch the demo Streamlit app"""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    streamlit_app_path = os.path.join(script_dir, "streamlit_browser_agent_async.py")
    
    # Add browser-use to Python path
    browser_use_path = os.path.join(script_dir, 'browser-use')
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{browser_use_path}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = browser_use_path
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Launch the Streamlit app
    print("Launching Browser-Use Demo App...")
    print("App will be available at: http://localhost:8501")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", streamlit_app_path,
        "--server.port", "8501",
        "--server.address", "localhost"
    ], env=env)

if __name__ == "__main__":
    main()