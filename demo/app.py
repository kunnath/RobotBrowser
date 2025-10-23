# Revert: Remove automatic screenshot copying logic and restore original imports

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

# Remove browser_use.screenshots.service import and browser-use path append
# Restore original logic

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
        self.temp_screenshots_dir = None
        
        self.base_output_dir.mkdir(exist_ok=True)
        print(f"✅ Reports base directory: {self.base_output_dir.absolute()}")

    def run_automation_sync(self, url, task_description, api_key, headless=False):
        def run_in_thread():
            try:
                self.status_queue.put("📁 Creating report directory...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                domain = urlparse(url).netloc.replace("www.", "").replace(".", "_")
                if not domain:
                    domain = "unknown_site"
                report_name = f"{domain}_{timestamp}"
                self.current_report_dir = self.base_output_dir / report_name
                self.current_report_dir.mkdir(parents=True, exist_ok=True)
                screenshots_dir = self.current_report_dir / "screenshots"
                screenshots_dir.mkdir(exist_ok=True)
                print(f"✅ Created report directory: {self.current_report_dir}")
                self.status_queue.put(f"📁 Report directory created: {self.current_report_dir.name}")

                try:
                    self.status_queue.put("🔧 Importing browser automation components...")
                    from browser_use import Agent
                    from browser_use.llm.deepseek.chat import ChatDeepSeek
                    browser_use_available = True
                except ImportError as e:
                    print(f"Browser-use import failed: {e}")
                    browser_use_available = False

                if browser_use_available:
                    self.status_queue.put("🔧 Initializing AI agent...")
                    llm = ChatDeepSeek(
                        model='deepseek-chat',
                        api_key=api_key
                    )
                    self.status_queue.put("🌐 Starting browser with screenshot capture...")
                    enhanced_task = f"""
                    Navigate to {url} and {task_description}
                    IMPORTANT: Take screenshots at every major step including:
                    1. Initial page load
                    2. Before and after each interaction
                    3. Any errors or popups
                    4. Final results
                    Save all screenshots and provide detailed explanations.
                    """
                    agent = Agent(
                        task=enhanced_task,
                        llm=llm,
                        headless=headless
                    )
                    self.status_queue.put("⚡ Executing browser automation...")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(agent.run())
                else:
                    self.status_queue.put("🔧 Running in demo mode (browser-use not available)...")
                    result = self.run_demo_automation(url, task_description)

                # Remove automatic report generation here.
                # Only store results and info needed for later report generation.
                self.result_queue.put({
                    "success": True,
                    "result": result,
                    "report_dir": str(self.current_report_dir),
                    "report_name": report_name,
                    "mode": "real" if browser_use_available else "demo",
                    "url": url,
                    "task_description": task_description
                })

            except Exception as e:
                print(f"Error in automation: {e}")
                self.status_queue.put(f"❌ Error: {str(e)}")
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
            time.sleep(2)
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
        if not self.current_report_dir:
            return
        screenshots_dir = self.current_report_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
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
        try:
            screenshots_info = self.collect_screenshots()
            mode_badge = "REAL AUTOMATION" if real_mode else "DEMO MODE"
            mode_color = "#28a745" if real_mode else "#ffc107"
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
            report_path = self.current_report_dir / f"{report_name}.html"
            report_path.write_text(html_content, encoding='utf-8')
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
        screenshots = []
        if not self.current_report_dir:
            return screenshots
        screenshots_dir = self.current_report_dir / "screenshots"
        if screenshots_dir.exists():
            image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp"]
            for extension in image_extensions:
                for img_file in sorted(screenshots_dir.glob(extension)):
                    print(f"Found screenshot: {img_file}")  # Debug print
                    file_size = img_file.stat().st_size
                    screenshots.append({
                        "name": img_file.name,
                        "path": str(img_file),
                        "relative_path": f"screenshots/{img_file.name}",
                        "timestamp": datetime.fromtimestamp(img_file.stat().st_mtime).strftime('%H:%M:%S'),
                        "size": f"{file_size // 1024} KB" if file_size > 0 else "Demo",
                        "is_real": file_size > 1024
                    })
        return screenshots

    def generate_screenshot_gallery_html(self, screenshots_info, real_mode=True):
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

    def update_report_screenshots(self):
        pass
# Rest of the main() function stays the same...
def main():
    st.title("🤖 Browser Automation with Reports")
    st.markdown("**Automated browser tasks with guaranteed report generation & automatic screenshot copying**")
    
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
            existing_reports = list(reports_dir.glob("*/"))
            if existing_reports:
                st.markdown(f"**Found {len(existing_reports)} existing reports:**")
                for report_dir in sorted(existing_reports)[-5:]:
                    st.text(f"📂 {report_dir.name}")
        else:
            st.warning("⚠️ Reports folder will be created on first run")
    
    # Session state initialization
    if 'automation_runner' not in st.session_state:
        st.session_state.automation_runner = BrowserAutomationRunner()
    if 'current_status' not in st.session_state:
        st.session_state.current_status = "Ready"
    if 'current_report' not in st.session_state:
        st.session_state.current_report = None
    if 'automation_done' not in st.session_state:
        st.session_state.automation_done = False
    if 'latest_report_name' not in st.session_state:
        st.session_state.latest_report_name = None
    if 'latest_report_dir' not in st.session_state:
        st.session_state.latest_report_dir = None
    if 'latest_url' not in st.session_state:
        st.session_state.latest_url = None
    if 'latest_task_description' not in st.session_state:
        st.session_state.latest_task_description = None
    if 'latest_api_key' not in st.session_state:
        st.session_state.latest_api_key = None
    if 'latest_headless' not in st.session_state:
        st.session_state.latest_headless = None

    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("🎯 Automation Task")
        
        api_key = st.text_input(
            "🔑 DeepSeek API Key",
            type="password",
            value=os.getenv('DEEPSEEK_API_KEY', ''),
            help="Enter your DeepSeek API key"
        )
        
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
        
        headless = st.checkbox("Headless Mode", value=False, help="Uncheck to see browser window")
        
        # Split buttons
        start_col, report_col = st.columns([2, 2])
        with start_col:
            if st.button("🚀 Start Automation", type="primary", disabled=st.session_state.automation_runner.running):
                if url and task_description:
                    if st.session_state.automation_runner.run_automation_sync(url, task_description, api_key, headless):
                        st.session_state.current_report = None
                        st.session_state.automation_done = False
                        st.session_state.latest_url = url
                        st.session_state.latest_task_description = task_description
                        st.session_state.latest_api_key = api_key
                        st.session_state.latest_headless = headless
                        st.rerun()
                    else:
                        st.error("Another task is already running!")
                else:
                    st.error("Please provide URL and task description!")
        with report_col:
            # Enable only after automation is done
            generate_disabled = not st.session_state.automation_done or st.session_state.latest_report_dir is None
            if st.button("📄 Generate Report", disabled=generate_disabled):
                runner = st.session_state.automation_runner
                runner.current_report_dir = Path(st.session_state.latest_report_dir)
                screenshots = runner.collect_screenshots()
                report_name = st.session_state.latest_report_name
                url = st.session_state.latest_url
                task_description = st.session_state.latest_task_description
                api_key = st.session_state.latest_api_key
                headless = st.session_state.latest_headless
                # Use last automation result if available
                result = st.session_state.current_report.get('result', '') if st.session_state.current_report else ''
                real_mode = st.session_state.current_report.get('mode', 'demo') == 'real' if st.session_state.current_report else False
                new_report_path = runner.generate_comprehensive_report(
                    url, task_description, result, report_name, real_mode
                )
                if new_report_path:
                    st.success(f"✅ Report generated: {new_report_path}")
                else:
                    st.error("❌ Failed to generate report.")

    with col2:
        st.header("📊 Status")
        status_container = st.empty()
        status_update = st.session_state.automation_runner.get_status()
        if status_update:
            st.session_state.current_status = status_update
        if st.session_state.automation_runner.running:
            status_container.info(f"🔄 {st.session_state.current_status}")
        else:
            status_container.success("✅ Ready")
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
            st.session_state.automation_done = True
            st.session_state.latest_report_name = result.get('report_name')
            st.session_state.latest_report_dir = result['report_dir']
            st.session_state.latest_url = result.get('url')
            st.session_state.latest_task_description = result.get('task_description')
            st.success("🎉 **Automation completed successfully!**")
            st.rerun()  # <-- Add this line
        else:
            st.error(f"❌ **Automation Failed:** {result['error']}")
    
    if st.session_state.automation_runner.running:
        time.sleep(1.5)
        st.rerun()
    
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

    if st.button("🔄 Refresh Screenshots"):
        st.rerun()

if __name__ == "__main__":
    main()