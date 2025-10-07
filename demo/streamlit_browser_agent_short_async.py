# streamlit_browser_agent_short_async.py - Working Version
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
from urllib.parse import urlparse

# Add browser-use to path
current_dir = Path(__file__).parent
browser_use_path = current_dir / "browser-use"
sys.path.append(str(browser_use_path))

# Page configuration
st.set_page_config(
    page_title="Browser Automation",
    page_icon="🤖", 
    layout="wide"
)

class BrowserAutomationRunner:
    def __init__(self, base_output_dir="automation_reports"):
        self.result_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.current_report_dir = None
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        
    def run_automation_sync(self, url, task_description, api_key, headless=False):
        """Run browser automation in a separate thread"""
        def run_in_thread():
            try:
                # Create report directory
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
                
                # Try to import and run browser-use
                try:
                    self.status_queue.put("🔧 Loading browser automation...")
                    from browser_use import Agent
                    from browser_use.llm.deepseek.chat import ChatDeepSeek
                    
                    # Real browser automation
                    result, screenshots = self.run_real_automation(
                        url, task_description, api_key, headless, screenshots_dir
                    )
                    
                except ImportError as e:
                    # Demo mode fallback
                    self.status_queue.put("⚠️ Running in demo mode...")
                    result, screenshots = self.run_demo_automation(url, task_description, screenshots_dir)
                
                # Generate report
                self.status_queue.put("📊 Generating report...")
                report_path = self.generate_report(url, task_description, result, report_name, screenshots)
                
                self.status_queue.put("✅ Completed!")
                self.result_queue.put({
                    "success": True,
                    "result": result,
                    "screenshots": screenshots,
                    "report_path": str(report_path),
                    "report_dir": str(self.current_report_dir),
                    "screenshot_count": len(screenshots)
                })
                
            except Exception as e:
                self.status_queue.put(f"❌ Error: {str(e)}")
                self.result_queue.put({"success": False, "error": str(e)})
            finally:
                self.running = False
        
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=run_in_thread)
            self.thread.start()
            return True
        return False
    
    def run_real_automation(self, url, task_description, api_key, headless, screenshots_dir):
        """Run real browser automation synchronously"""
        from browser_use import Agent
        from browser_use.llm.deepseek.chat import ChatDeepSeek
        
        self.status_queue.put("🤖 Initializing AI agent...")
        
        # Create LLM
        llm = ChatDeepSeek(model='deepseek-chat', api_key=api_key)
        
        # Enhanced task with screenshot instructions
        enhanced_task = f"""
        Navigate to {url} and {task_description}
        
        Please take screenshots at every major step:
        - Initial page load
        - Before and after clicking elements
        - When navigating to new pages
        - Before and after form interactions
        - Final results
        
        Be thorough with screenshot documentation!
        """
        
        self.status_queue.put("🌐 Starting browser automation...")
        
        # Create and run agent
        agent = Agent(task=enhanced_task, llm=llm, headless=headless)
        
        # Run in asyncio loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.run())
        finally:
            loop.close()
        
        # Collect screenshots
        screenshots = self.collect_screenshots(screenshots_dir)
        
        return result, screenshots
    
    def run_demo_automation(self, url, task_description, screenshots_dir):
        """Demo automation with simulated screenshots"""
        screenshots = []
        
        demo_steps = [
            ("01_browser_start", "Browser initialization"),
            ("02_navigate", f"Loading {url}"),
            ("03_page_loaded", "Page loaded successfully"),
            ("04_analyze", "Analyzing page content"),
            ("05_interact", "Performing interactions"),
            ("06_complete", "Task completed")
        ]
        
        for i, (step_name, description) in enumerate(demo_steps, 1):
            self.status_queue.put(f"📸 Step {i}: {description}")
            
            # Create demo screenshot
            filename = f"{step_name}_{datetime.now().strftime('%H%M%S')}.png"
            screenshot_path = screenshots_dir / filename
            
            # Simple demo PNG data
            demo_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x06\x00\x00\x00p\xe2\x95T\x00\x00\x00\x0eIDATx\xdab\x00\x02\x00\x00\x05\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82'
            screenshot_path.write_bytes(demo_png)
            
            screenshots.append({
                "filename": filename,
                "path": str(screenshot_path),
                "step": step_name,
                "description": description,
                "timestamp": datetime.now().isoformat()
            })
            
            time.sleep(1)
        
        result = f"Demo automation completed for {url}\nTask: {task_description}\nCaptured {len(screenshots)} screenshots"
        return result, screenshots
    
    def collect_screenshots(self, screenshots_dir):
        """Collect actual screenshots from browser automation"""
        screenshots = []
        
        # Check multiple locations for screenshots
        locations = [
            screenshots_dir,
            Path.cwd() / "screenshots",
            Path.cwd() / "browser_use_screenshots"
        ]
        
        for location in locations:
            if location.exists():
                for img_file in location.glob("*.png"):
                    # Copy to our directory if needed
                    if location != screenshots_dir:
                        dest_path = screenshots_dir / img_file.name
                        try:
                            import shutil
                            shutil.copy2(img_file, dest_path)
                        except:
                            pass
                    
                    screenshots.append({
                        "filename": img_file.name,
                        "path": str(screenshots_dir / img_file.name),
                        "step": img_file.stem,
                        "description": f"Screenshot: {img_file.name}",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return screenshots
    
    def generate_report(self, url, task_description, result, report_name, screenshots):
        """Generate HTML report"""
        
        # Screenshot gallery HTML
        if screenshots:
            gallery_html = "<h3>📸 Screenshots</h3>"
            for i, screenshot in enumerate(screenshots, 1):
                relative_path = f"screenshots/{screenshot['filename']}"
                gallery_html += f"""
                <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                    <h4>Step {i}: {screenshot.get('step', 'Unknown').replace('_', ' ').title()}</h4>
                    <img src="{relative_path}" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;">
                    <p>{screenshot.get('description', '')}</p>
                    <small>📁 {screenshot['filename']} | ⏰ {screenshot.get('timestamp', '')[:19]}</small>
                </div>
                """
        else:
            gallery_html = "<p>No screenshots available</p>"
        
        # Create HTML report
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Browser Automation Report - {report_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .section {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 10px; }}
        .result {{ background: #e9ecef; padding: 15px; border-radius: 8px; white-space: pre-wrap; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Browser Automation Report</h1>
            <h2>{report_name}</h2>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="section">
            <h3>🎯 Task Details</h3>
            <p><strong>URL:</strong> <a href="{url}">{url}</a></p>
            <p><strong>Task:</strong> {task_description}</p>
            <p><strong>Screenshots:</strong> {len(screenshots)} captured</p>
        </div>
        
        <div class="section">
            <h3>📊 Results</h3>
            <div class="result">{result}</div>
        </div>
        
        <div class="section">
            {gallery_html}
        </div>
    </div>
</body>
</html>"""
        
        # Save files
        report_path = self.current_report_dir / f"{report_name}.html"
        report_path.write_text(html_content, encoding='utf-8')
        
        # Save JSON data
        json_data = {
            "report_name": report_name,
            "url": url,
            "task": task_description,
            "result": str(result),
            "screenshots": screenshots,
            "timestamp": datetime.now().isoformat()
        }
        
        json_path = self.current_report_dir / "report_data.json"
        json_path.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
        
        return report_path
    
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

def main():
    st.title("🤖 Browser Automation")
    st.markdown("**Automate web tasks with AI and generate reports with screenshots**")
    
    # Initialize session state
    if 'automation_runner' not in st.session_state:
        st.session_state.automation_runner = BrowserAutomationRunner()
    if 'current_status' not in st.session_state:
        st.session_state.current_status = "Ready"
    if 'current_report' not in st.session_state:
        st.session_state.current_report = None
    
    # Main interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("🎯 Automation Setup")
        
        # API Key
        api_key = st.text_input(
            "🔑 DeepSeek API Key",
            type="password",
            value=os.getenv('DEEPSEEK_API_KEY', ''),
            help="Enter your API key for browser automation"
        )
        
        # URL and Task
        url = st.text_input(
            "🌐 Website URL",
            value="https://example.com",
            placeholder="https://example.com"
        )
        
        task_description = st.text_area(
            "📋 What should the browser do?",
            placeholder="Example: Navigate to the homepage, search for information, take screenshots of key pages",
            height=100
        )
        
        # Settings
        headless = st.checkbox("Headless Mode (background)", value=False)
        
        # Start button
        if st.button(
            "🚀 Start Automation", 
            type="primary", 
            disabled=st.session_state.automation_runner.running
        ):
            if url and task_description:
                if st.session_state.automation_runner.run_automation_sync(url, task_description, api_key, headless):
                    st.session_state.current_report = None
                    st.rerun()
                else:
                    st.error("Task already running!")
            else:
                st.error("Please provide URL and task description!")
    
    with col2:
        st.header("📊 Status")
        
        # Status display
        status_container = st.empty()
        
        # Update status
        status_update = st.session_state.automation_runner.get_status()
        if status_update:
            st.session_state.current_status = status_update
        
        # Show current status
        if st.session_state.automation_runner.running:
            status_container.info(f"🔄 {st.session_state.current_status}")
        else:
            status_container.success("✅ Ready")
    
    # Check for results
    result = st.session_state.automation_runner.get_result()
    if result:
        if result["success"]:
            st.session_state.current_report = result
            
            screenshot_count = result.get("screenshot_count", 0)
            st.success(f"🎉 **Task Complete!** Generated {screenshot_count} screenshots")
            
            if result.get("report_path"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button("📖 Open Report"):
                        try:
                            import webbrowser
                            webbrowser.open(f"file://{result['report_path']}")
                            st.success("Report opened!")
                        except:
                            st.code(result['report_path'])
                
                with col_b:
                    if st.button("📁 Open Folder"):
                        try:
                            import subprocess
                            subprocess.run(["open", result['report_dir']])
                            st.success("Folder opened!")
                        except:
                            st.code(result['report_dir'])
        else:
            st.error(f"❌ **Failed:** {result['error']}")
    
    # Auto-refresh during automation
    if st.session_state.automation_runner.running:
        time.sleep(1.5)
        st.rerun()
    
    # Instructions
    st.markdown("---")
    st.markdown("""
    ### 🎯 How to Use:
    1. **Enter your DeepSeek API key** (or it will run in demo mode)
    2. **Provide a website URL** to automate
    3. **Describe the task** you want the browser to perform
    4. **Click "Start Automation"** and watch the progress
    5. **View the report** with screenshots when complete
    
    ### 📸 Features:
    - Automatic screenshot capture at each step
    - Beautiful HTML reports with timeline view
    - Real browser automation or demo mode fallback
    - All files organized in timestamped folders
    """)