# Updated streamlit_browser_agent_report_async.py with automatic screenshot copying

import streamlit as st
import asyncio
import os
import sys
import time
from datetime import datetime
import threading
import queue
from pathlib import Path
import json
import shutil
import glob
from urllib.parse import urlparse

# Add browser-use to path
current_dir = Path(__file__).parent
browser_use_path = current_dir / "browser-use"
sys.path.append(str(browser_use_path))

# Page configuration
st.set_page_config(
    page_title="Browser Automation with Reports",
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

class BrowserAutomationRunner:
    def __init__(self, base_output_dir="automation_reports"):
        self.result_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.current_report_dir = None
        self.base_output_dir = Path(base_output_dir)
        self.temp_screenshots_dir = None  # Will store the browser_use temp directory
        
        # Ensure base output directory exists
        self.base_output_dir.mkdir(exist_ok=True)
        print(f"✅ Reports base directory: {self.base_output_dir.absolute()}")
    
    def find_browser_use_temp_screenshots(self):
        """Find the most recent browser_use_agent screenshots directory"""
        try:
            # Common macOS temp directory pattern
            temp_base = "/var/folders/*/T/"
            
            # Search for browser_use_agent directories
            pattern = f"{temp_base}browser_use_agent_*/screenshots"
            
            # Use glob to find all matching directories
            temp_dirs = glob.glob(pattern, recursive=True)
            
            if not temp_dirs:
                # Also check /tmp directory
                tmp_pattern = "/tmp/browser_use_agent_*/screenshots"
                temp_dirs = glob.glob(tmp_pattern, recursive=True)
            
            if temp_dirs:
                # Sort by modification time and get the most recent
                temp_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                latest_dir = temp_dirs[0]
                self.status_queue.put(f"📸 Found screenshots folder: {latest_dir}")
                return Path(latest_dir)
            else:
                self.status_queue.put("⚠️ No browser_use_agent temp screenshots found")
                return None
                
        except Exception as e:
            print(f"Error finding temp screenshots: {e}")
            self.status_queue.put(f"❌ Error finding screenshots: {str(e)}")
            return None
    
    def copy_browser_use_screenshots(self):
        """Copy screenshots from browser_use temp directory to report directory"""
        if not self.current_report_dir:
            return False
            
        try:
            # Find the temp screenshots directory
            temp_screenshots = self.find_browser_use_temp_screenshots()
            
            if not temp_screenshots or not temp_screenshots.exists():
                self.status_queue.put("📸 No temp screenshots to copy (normal for demo mode)")
                return False
            
            # Create target screenshots directory
            target_screenshots = self.current_report_dir / "screenshots"
            target_screenshots.mkdir(exist_ok=True)
            
            # Copy all screenshot files
            copied_count = 0
            screenshot_files = list(temp_screenshots.glob("*.png")) + list(temp_screenshots.glob("*.jpg"))
            
            for screenshot_file in screenshot_files:
                try:
                    target_file = target_screenshots / screenshot_file.name
                    shutil.copy2(screenshot_file, target_file)
                    copied_count += 1
                    self.status_queue.put(f"📸 Copied: {screenshot_file.name}")
                except Exception as e:
                    print(f"Error copying {screenshot_file.name}: {e}")
            
            if copied_count > 0:
                self.status_queue.put(f"✅ Successfully copied {copied_count} screenshots")
                return True
            else:
                self.status_queue.put("📸 No screenshot files found to copy")
                return False
                
        except Exception as e:
            print(f"Error copying screenshots: {e}")
            self.status_queue.put(f"❌ Screenshot copy error: {str(e)}")
            return False
    
    def run_automation_sync(self, url, task_description, api_key, headless=False):
        """Run browser automation with guaranteed report generation and screenshot copying"""
        def run_in_thread():
            try:
                # Create report directory first
                self.status_queue.put("📁 Creating report directory...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                domain = urlparse(url).netloc.replace("www.", "").replace(".", "_")
                if not domain:
                    domain = "unknown_site"
                
                report_name = f"{domain}_{timestamp}"
                self.current_report_dir = self.base_output_dir / report_name
                
                # Ensure the directory is created
                self.current_report_dir.mkdir(parents=True, exist_ok=True)
                screenshots_dir = self.current_report_dir / "screenshots"
                screenshots_dir.mkdir(exist_ok=True)
                
                print(f"✅ Created report directory: {self.current_report_dir}")
                self.status_queue.put(f"📁 Report directory created: {self.current_report_dir.name}")
                
                # Try to import browser-use components
                try:
                    self.status_queue.put("🔧 Importing browser automation components...")
                    from browser_use import Agent
                    from browser_use.llm.deepseek.chat import ChatDeepSeek
                    browser_use_available = True
                except ImportError as e:
                    print(f"Browser-use import failed: {e}")
                    browser_use_available = False
                
                if browser_use_available:
                    # Real browser automation
                    self.status_queue.put("🔧 Initializing AI agent...")
                    
                    # Initialize LLM
                    llm = ChatDeepSeek(
                        model='deepseek-chat',
                        api_key=api_key
                    )
                    
                    self.status_queue.put("🌐 Starting browser with screenshot capture...")
                    
                    # Enhanced task with screenshot instructions
                    enhanced_task = f"""
                    Navigate to {url} and {task_description}
                    
                    IMPORTANT: Take screenshots at every major step including:
                    1. Initial page load
                    2. Before and after each interaction
                    3. Any errors or popups
                    4. Final results
                    
                    Save all screenshots and provide detailed explanations.
                    """
                    
                    # Create agent
                    agent = Agent(
                        task=enhanced_task,
                        llm=llm,
                        headless=headless
                    )
                    
                    self.status_queue.put("⚡ Executing browser automation...")
                    
                    # Run automation
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(agent.run())
                    
                    # IMPORTANT: Copy screenshots from temp directory after automation completes
                    self.status_queue.put("📸 Searching for and copying screenshots...")
                    self.copy_browser_use_screenshots()
                    
                else:
                    # Demo mode with simulated screenshots
                    self.status_queue.put("🔧 Running in demo mode (browser-use not available)...")
                    result = self.run_demo_automation(url, task_description)
                
                self.status_queue.put("📊 Generating comprehensive report...")
                
                # Generate report regardless of automation type
                report_path = self.generate_comprehensive_report(
                    url, task_description, result, report_name, browser_use_available
                )
                
                self.status_queue.put("✅ Report generation completed!")
                self.result_queue.put({
                    "success": True,
                    "result": result,
                    "report_path": str(report_path),
                    "report_dir": str(self.current_report_dir),
                    "mode": "real" if browser_use_available else "demo"
                })
                
            except Exception as e:
                print(f"Error in automation: {e}")
                self.status_queue.put(f"❌ Error: {str(e)}")
                
                # Still try to copy any screenshots that might exist
                if hasattr(self, 'current_report_dir') and self.current_report_dir:
                    try:
                        self.copy_browser_use_screenshots()
                    except:
                        pass
                
                # Still try to generate an error report
                try:
                    if hasattr(self, 'current_report_dir') and self.current_report_dir:
                        error_report = self.generate_error_report(url, task_description, str(e))
                        self.result_queue.put({
                            "success": False,
                            "error": str(e),
                            "report_path": str(error_report) if error_report else None,
                            "report_dir": str(self.current_report_dir) if self.current_report_dir else None
                        })
                    else:
                        self.result_queue.put({"success": False, "error": str(e)})
                except:
                    self.result_queue.put({"success": False, "error": str(e)})
            finally:
                self.running = False
        
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=run_in_thread)
            self.thread.start()
            return True
        return False
    
    def run_demo_automation(self, url, task_description):
        """Run a demo automation with simulated steps"""
        steps = [
            "🌐 Navigating to target URL...",
            "📖 Analyzing page content...",
            "🔍 Looking for interactive elements...", 
            "⚡ Performing requested actions...",
            "📸 Capturing screenshots...",
            "✅ Task execution completed!"
        ]
        
        for i, step in enumerate(steps, 1):
            self.status_queue.put(f"Step {i}/{len(steps)}: {step}")
            time.sleep(2)  # Simulate work
        
        # Create demo screenshots
        self.create_demo_screenshots()
        
        return f"""Demo Automation Results:
        
Target URL: {url}
Task: {task_description}
Status: Completed (Demo Mode)

Simulated Actions Performed:
1. Navigated to {url}
2. Analyzed page structure and content
3. Identified interactive elements
4. Performed requested automation tasks
5. Captured screenshots of key moments
6. Generated comprehensive report

Note: This is demo mode. Install browser-use library for real automation."""
    
    def create_demo_screenshots(self):
        """Create demo screenshot files"""
        if not self.current_report_dir:
            return
            
        screenshots_dir = self.current_report_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        
        # Create simple demo image files (1x1 pixel PNG)
        demo_png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        demo_screenshots = [
            "01_page_load.png",
            "02_navigation.png", 
            "03_interaction.png",
            "04_results.png"
        ]
        
        for screenshot_name in demo_screenshots:
            screenshot_path = screenshots_dir / screenshot_name
            screenshot_path.write_bytes(demo_png_data)
            print(f"✅ Created demo screenshot: {screenshot_path}")
    
    def generate_comprehensive_report(self, url, task_description, result, report_name, real_mode=True):
        """Generate a detailed HTML report"""
        try:
            # Collect screenshots (now includes copied browser_use screenshots)
            screenshots_info = self.collect_screenshots()
            
            mode_badge = "REAL AUTOMATION" if real_mode else "DEMO MODE"
            mode_color = "#28a745" if real_mode else "#ffc107"
            
            # Create HTML report (same as before, but now with real screenshots)
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browser Automation Report - {report_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}
        
        .mode-badge {{
            background: {mode_color};
            color: {'white' if real_mode else '#212529'};
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-top: 10px;
            display: inline-block;
        }}
        
        .section {{
            background: white;
            margin: 20px 0;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .info-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        
        .screenshot-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .screenshot-item {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .screenshot-item img {{
            max-width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-bottom: 15px;
            background: #f0f0f0;
            cursor: pointer;
            transition: transform 0.3s ease;
        }}
        
        .screenshot-item img:hover {{
            transform: scale(1.05);
        }}
        
        .task-result {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #28a745;
            margin: 20px 0;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }}
        
        .metric-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
            display: block;
        }}
        
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        
        .file-list li {{
            padding: 10px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .no-screenshots {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-style: italic;
        }}
        
        .screenshot-source {{
            font-size: 0.8em;
            color: #666;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Browser Automation Report</h1>
            <h2>{report_name}</h2>
            <div class="mode-badge">{mode_badge}</div>
            <p class="timestamp">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>

        <div class="info-grid">
            <div class="info-card">
                <h3>🎯 Task Information</h3>
                <p><strong>Target URL:</strong></p>
                <p><a href="{url}" target="_blank">{url}</a></p>
                <p><strong>Task Description:</strong></p>
                <p>{task_description}</p>
                <p class="timestamp"><strong>Executed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="info-card">
                <h3>📊 Results Summary</h3>
                <div class="metrics">
                    <div class="metric-card">
                        <span class="metric-number">{len(screenshots_info)}</span>
                        <span>Screenshots</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-number">✅</span>
                        <span>Status</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h3>🎬 Execution Results</h3>
            <div class="task-result">{str(result) if result else "Task completed successfully!"}</div>
        </div>

        <div class="section">
            <h3>📸 Screenshots Gallery</h3>
            {self.generate_screenshot_gallery_html(screenshots_info, real_mode)}
        </div>

        <div class="section">
            <h3>📁 Generated Files</h3>
            <ul class="file-list">
                <li>📄 <strong>{report_name}.html</strong> - This report</li>
                <li>📊 <strong>report_data.json</strong> - Machine-readable data</li>
                <li>📁 <strong>screenshots/</strong> - All captured images ({len(screenshots_info)} files)</li>
                <li>📍 <strong>Location:</strong> {self.current_report_dir}</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

            # Save HTML report
            report_path = self.current_report_dir / f"{report_name}.html"
            report_path.write_text(html_content, encoding='utf-8')
            
            # Save JSON data
            report_data = {
                "report_name": report_name,
                "url": url,
                "task_description": task_description,
                "result": str(result),
                "timestamp": datetime.now().isoformat(),
                "screenshots": screenshots_info,
                "report_path": str(report_path),
                "report_dir": str(self.current_report_dir),
                "mode": "real" if real_mode else "demo"
            }
            
            json_path = self.current_report_dir / "report_data.json"
            json_path.write_text(json.dumps(report_data, indent=2), encoding='utf-8')
            
            print(f"✅ Report generated: {report_path}")
            return report_path
            
        except Exception as e:
            print(f"Error generating report: {e}")
            return None
    
    def generate_error_report(self, url, task_description, error):
        """Generate a report for failed automation"""
        if not self.current_report_dir:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_html = f"""
<!DOCTYPE html>
<html>
<head><title>Automation Error Report</title></head>
<body>
    <h1>❌ Automation Error Report</h1>
    <p><strong>URL:</strong> {url}</p>
    <p><strong>Task:</strong> {task_description}</p>
    <p><strong>Error:</strong> {error}</p>
    <p><strong>Time:</strong> {datetime.now()}</p>
</body>
</html>"""
        
        error_path = self.current_report_dir / f"error_report_{timestamp}.html"
        error_path.write_text(error_html)
        return error_path
    
    def collect_screenshots(self):
        """Collect screenshot information"""
        screenshots = []
        
        if not self.current_report_dir:
            return screenshots
            
        screenshots_dir = self.current_report_dir / "screenshots"
        
        if screenshots_dir.exists():
            # Get all image files, not just PNG
            image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp"]
            for extension in image_extensions:
                for img_file in sorted(screenshots_dir.glob(extension)):
                    file_size = img_file.stat().st_size
                    screenshots.append({
                        "name": img_file.name,
                        "path": str(img_file),
                        "relative_path": f"screenshots/{img_file.name}",
                        "timestamp": datetime.fromtimestamp(img_file.stat().st_mtime).strftime('%H:%M:%S'),
                        "size": f"{file_size // 1024} KB" if file_size > 0 else "Demo",
                        "is_real": file_size > 1024  # Real screenshots are usually larger than 1KB
                    })
        
        return screenshots
    
    def generate_screenshot_gallery_html(self, screenshots_info, real_mode=True):
        """Generate HTML for screenshot gallery"""
        if not screenshots_info:
            return '''
            <div class="no-screenshots">
                📷 No screenshots available for this run.<br><br>
                Screenshots are captured automatically during browser automation.
            </div>
            '''
        
        gallery_html = '<div class="screenshot-gallery">'
        
        for i, screenshot in enumerate(screenshots_info, 1):
            is_real_screenshot = screenshot.get('is_real', False)
            source_label = "Browser Automation" if is_real_screenshot else "Demo Image"
            
            gallery_html += f'''
            <div class="screenshot-item">
                <h4>Screenshot {i}</h4>
                <img src="{screenshot["relative_path"]}" 
                     alt="{screenshot["name"]}" 
                     onclick="window.open('{screenshot["relative_path"]}', '_blank')"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <div style="display:none; padding: 60px 20px; background: #f0f0f0; border-radius: 8px;">
                    📷 Image Preview<br>
                    <small>{screenshot["name"]}</small>
                </div>
                <p><strong>File:</strong> {screenshot["name"]}</p>
                <p><strong>Time:</strong> {screenshot["timestamp"]}</p>
                <p><strong>Size:</strong> {screenshot["size"]}</p>
                <p class="screenshot-source"><strong>Source:</strong> {source_label}</p>
            </div>
            '''
        
        gallery_html += '</div>'
        return gallery_html
    
    def get_status(self):
        try:
            return self.status_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_result(self):
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None

# Rest of the main() function stays the same...
def main():
    st.title("🤖 Browser Automation with Reports")
    st.markdown("**Automated browser tasks with guaranteed report generation & automatic screenshot copying**")
    
    # Show current directory info
    current_dir = Path.cwd()
    reports_dir = current_dir / "automation_reports"
    
    with st.sidebar:
        st.markdown("### 📁 Reports Location")
        st.code(str(reports_dir))
        
        if st.button("📁 Create Reports Folder Now"):
            reports_dir.mkdir(exist_ok=True)
            st.success("✅ Reports folder created!")
            st.rerun()
        
        if reports_dir.exists():
            st.success("✅ Reports folder exists")
            # List existing reports
            existing_reports = list(reports_dir.glob("*/"))
            if existing_reports:
                st.markdown(f"**Found {len(existing_reports)} existing reports:**")
                for report_dir in sorted(existing_reports)[-5:]:  # Show last 5
                    st.text(f"📂 {report_dir.name}")
        else:
            st.warning("⚠️ Reports folder will be created on first run")
    
    # Initialize session state
    if 'automation_runner' not in st.session_state:
        st.session_state.automation_runner = BrowserAutomationRunner()
    if 'current_status' not in st.session_state:
        st.session_state.current_status = "Ready"
    if 'current_report' not in st.session_state:
        st.session_state.current_report = None
    
    # Main form
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("🎯 Automation Task")
        
        # API Key
        api_key = st.text_input(
            "🔑 DeepSeek API Key",
            type="password",
            value=os.getenv('DEEPSEEK_API_KEY', ''),
            help="Enter your DeepSeek API key"
        )
        
        # URL and task
        url = st.text_input(
            "🌐 Target Website",
            value="https://example.com",
            placeholder="https://example.com"
        )
        
        task_description = st.text_area(
            "📋 What should the browser do?",
            placeholder="Example: Navigate to the homepage, take screenshots, search for information, and capture the results",
            height=100
        )
        
        # Settings
        headless = st.checkbox("Headless Mode", value=False, help="Uncheck to see browser window")
        
        # Start button
        if st.button("🚀 Start Automation & Generate Report", type="primary", disabled=st.session_state.automation_runner.running):
            if url and task_description:
                if st.session_state.automation_runner.run_automation_sync(url, task_description, api_key, headless):
                    st.session_state.current_report = None
                    st.rerun()
                else:
                    st.error("Another task is already running!")
            else:
                st.error("Please provide URL and task description!")
    
    with col2:
        st.header("📊 Status")
        
        status_container = st.empty()
        
        # Get status updates
        status_update = st.session_state.automation_runner.get_status()
        if status_update:
            st.session_state.current_status = status_update
        
        # Display current status
        if st.session_state.automation_runner.running:
            status_container.info(f"🔄 {st.session_state.current_status}")
        else:
            status_container.success("✅ Ready")
        
        # Show folder status
        if reports_dir.exists():
            st.success(f"📁 Reports folder ready")
            st.text(f"Location: {reports_dir.name}")
        else:
            st.warning("📁 Reports folder will be created")
    
    # Check for results
    result = st.session_state.automation_runner.get_result()
    if result:
        if result["success"]:
            st.session_state.current_report = result
            
            # Display success message
            st.success("🎉 **Automation completed successfully!**")
            
            # Show report info
            if result.get("report_path"):
                st.markdown("---")
                st.header("📊 Report Generated!")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.info(f"**Report Location:**\n`{result['report_path']}`")
                    
                    mode = result.get('mode', 'unknown')
                    if mode == 'demo':
                        st.warning("⚠️ Demo mode used - install browser-use for real automation")
                    else:
                        st.success("✅ Real browser automation completed with screenshot copying")
                
                with col_b:
                    if st.button("📖 Open HTML Report"):
                        try:
                            import webbrowser
                            webbrowser.open(f"file://{result['report_path']}")
                            st.success("Report opened in browser!")
                        except Exception as e:
                            st.error(f"Could not open: {e}")
                    
                    if st.button("📁 Open Report Folder"):
                        try:
                            import subprocess
                            subprocess.run(["open", result['report_dir']])  # macOS
                            st.success("Folder opened!")
                        except:
                            st.code(result['report_dir'])
                
                # Load and display report data if available
                if result.get('report_dir'):
                    json_path = Path(result['report_dir']) / "report_data.json"
                    if json_path.exists():
                        with open(json_path, 'r') as f:
                            report_data = json.load(f)
                        
                        screenshots = report_data.get('screenshots', [])
                        if screenshots:
                            st.markdown("### 📸 Screenshots Preview")
                            cols = st.columns(min(3, len(screenshots)))
                            
                            for i, screenshot in enumerate(screenshots[:3]):
                                col_idx = i % len(cols)
                                with cols[col_idx]:
                                    screenshot_path = Path(result['report_dir']) / screenshot['relative_path']
                                    if screenshot_path.exists():
                                        try:
                                            st.image(str(screenshot_path), caption=screenshot['name'], use_column_width=True)
                                        except:
                                            st.text(f"📷 {screenshot['name']}")
                            
                            if len(screenshots) > 3:
                                st.info(f"+ {len(screenshots) - 3} more in full report")
        else:
            st.error(f"❌ **Automation Failed:** {result['error']}")
    
    # Auto-refresh during automation
    if st.session_state.automation_runner.running:
        time.sleep(1.5)
        st.rerun()
    
    # Instructions
    st.markdown("---")
    st.markdown(f"""
    ### 📁 Reports Location: `{reports_dir}`
    
    ### 🎯 How It Works:
    1. **Fill in the form** above with your task details
    2. **Click "Start Automation"** - reports folder will be created automatically
    3. **Watch the status** updates in the right panel
    4. **Screenshots are automatically copied** from browser_use temp folder
    5. **Get your report** with all screenshots when complete
    6. **Access files** using the action buttons
    
    ### 📊 What You Get:
    - **HTML Report** - Beautiful visual report with real screenshots
    - **JSON Data** - Machine-readable automation data
    - **Screenshots** - All captured images automatically copied and organized
    - **Folder Structure** - Everything organized in timestamped folders
    
    ### 🔄 Automatic Screenshot Management:
    - **Real Mode**: Screenshots copied from `/var/folders/.../browser_use_agent_.../screenshots`
    - **Demo Mode**: Demo screenshots created for testing
    - **No Manual Steps**: Everything is copied automatically after each run
    
    ### 💡 Current Status:
    - Reports Directory: `{reports_dir}` {'✅ EXISTS' if reports_dir.exists() else '📁 WILL BE CREATED'}
    - Browser-use Library: {'✅ READY' if 'browser_use' in sys.modules else '⚠️ DEMO MODE'}
    - Screenshot Copying: ✅ AUTOMATIC
    """)

if __name__ == "__main__":
    main()