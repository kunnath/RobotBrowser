#!/usr/bin/env python3
"""
setup_demo.py - Setup script for Browser-Use Demo
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"Running: {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")

def install_dependencies():
    """Install Python dependencies from requirements.txt"""
    print("\n📦 Installing Python dependencies...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    success = run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing dependencies from requirements.txt"
    )
    
    if success:
        print("✓ Dependencies installed successfully")
    else:
        print("❌ Failed to install dependencies")
    
    return success

def setup_environment():
    """Setup environment file"""
    print("\n🔧 Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from .env.example")
    else:
        # Create a basic .env file
        env_content = """# Browser-Use Demo Configuration

# DeepSeek API Key (required)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Alternative LLM providers (optional)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Browser Configuration
BROWSER_TYPE=chromium
HEADLESS=false
TIMEOUT=30000
LOG_LEVEL=INFO

# Optional: Local LLM
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✓ Created basic .env file")
    
    return True

def setup_browser_use():
    """Setup browser-use package"""
    print("\n🌐 Setting up browser-use...")
    
    browser_use_dir = Path("browser-use")
    if browser_use_dir.exists() and (browser_use_dir / "pyproject.toml").exists():
        print("Found browser-use directory, installing as editable package...")
        success = run_command(
            f"{sys.executable} -m pip install -e browser-use/",
            "Installing browser-use package"
        )
        if success:
            print("✓ Browser-use installed successfully")
        return success
    else:
        print("⚠️  browser-use directory not found, assuming it's installed via pip")
        return True

def create_launch_script():
    """Create launch_demo.py if it doesn't exist"""
    print("\n🚀 Creating launch script...")
    
    launch_file = Path("launch_demo.py")
    if launch_file.exists():
        print("✓ launch_demo.py already exists")
        return True
    
    launch_content = '''#!/usr/bin/env python3
"""
launch_demo.py - Launch the Browser-Use Demo Streamlit app
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the demo Streamlit app"""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    streamlit_app = script_dir / "streamlit_browser_agent_async.py"
    
    if not streamlit_app.exists():
        print("❌ streamlit_browser_agent_async.py not found!")
        print("Please make sure the demo files are in the same directory.")
        sys.exit(1)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✓ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    
    # Launch the Streamlit app
    print("🚀 Launching Browser-Use Demo App...")
    print("📱 App will be available at: http://localhost:8501")
    print("🔄 Starting Streamlit server...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(streamlit_app),
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\\n⏹️  Demo stopped by user")
    except Exception as e:
        print(f"❌ Error launching demo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open(launch_file, 'w') as f:
        f.write(launch_content)
    
    # Make it executable
    launch_file.chmod(0o755)
    print("✓ Created launch_demo.py")
    return True

def verify_setup():
    """Verify that setup was successful"""
    print("\n🔍 Verifying setup...")
    
    # Check required files
    required_files = [".env", "requirements.txt"]
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    # Check if streamlit is available
    try:
        import streamlit
        print("✓ Streamlit is available")
    except ImportError:
        print("❌ Streamlit not available")
        return False
    
    # Check if browser_use is available
    try:
        import browser_use
        print("✓ browser_use is available")
    except ImportError:
        print("❌ browser_use not available")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🔧 Browser-Use Demo Setup")
    print("=" * 40)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working in: {script_dir.absolute()}")
    
    # Run setup steps
    try:
        check_python_version()
        
        if not install_dependencies():
            print("❌ Failed to install dependencies")
            sys.exit(1)
        
        if not setup_environment():
            print("❌ Failed to setup environment")
            sys.exit(1)
        
        if not setup_browser_use():
            print("❌ Failed to setup browser-use")
            sys.exit(1)
        
        if not create_launch_script():
            print("❌ Failed to create launch script")
            sys.exit(1)
        
        if verify_setup():
            print("\n✅ Setup completed successfully!")
            print("\n📋 Next steps:")
            print("1. Edit .env file and add your API keys (especially DEEPSEEK_API_KEY)")
            print("2. Run: python launch_demo.py")
            print("   OR")
            print("   Run: streamlit run streamlit_browser_agent_async.py")
        else:
            print("\n❌ Setup verification failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()