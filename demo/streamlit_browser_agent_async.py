# streamlit_browser_agent_async.py - Real Browser Automation
import streamlit as st
import asyncio
import os
import sys
import time
from datetime import datetime
import threading
import queue
from pathlib import Path

# Add browser-use to path
sys.path.append(str(Path(__file__).parent / "browser-use"))

# Page configuration
st.set_page_config(
    page_title="Real Browser Automation",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class BrowserAutomationRunner:
    def __init__(self):
        self.result_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.running = False
        self.thread = None
        
    def run_automation_sync(self, url, task_description, api_key, headless=False):
        """Run browser automation in a separate thread"""
        def run_in_thread():
            try:
                # Import browser-use components
                from browser_use import Agent
                from browser_use.llm.deepseek.chat import ChatDeepSeek
                
                self.status_queue.put("🔧 Initializing AI agent...")
                
                # Initialize LLM
                llm = ChatDeepSeek(
                    model='deepseek-chat',
                    api_key=api_key
                )
                
                self.status_queue.put("🌐 Starting browser...")
                
                # Create agent with task
                full_task = f"""
                Navigate to {url} and {task_description}
                
                Please:
                1. Take screenshots at key moments
                2. Explain what you're doing at each step
                3. Handle any popups or cookies dialogs
                4. Provide a summary of what you accomplished
                """
                
                agent = Agent(
                    task=full_task,
                    llm=llm,
                    headless=headless
                )
                
                self.status_queue.put("⚡ Executing automation task...")
                
                # Run the automation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(agent.run())
                
                self.status_queue.put("✅ Automation completed successfully!")
                self.result_queue.put({"success": True, "result": result})
                
            except ImportError as e:
                self.status_queue.put("❌ Browser-use library not found!")
                self.result_queue.put({
                    "success": False, 
                    "error": f"Import Error: {str(e)}. Please install browser-use library."
                })
            except Exception as e:
                self.status_queue.put(f"❌ Automation failed: {str(e)}")
                self.result_queue.put({"success": False, "error": str(e)})
            finally:
                self.running = False
        
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=run_in_thread)
            self.thread.start()
            return True
        return False
    
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
    st.title("🤖 Real Browser Automation")
    st.markdown("**Watch the browser perform tasks automatically!**")
    
    # Initialize session state
    if 'automation_runner' not in st.session_state:
        st.session_state.automation_runner = BrowserAutomationRunner()
    if 'current_status' not in st.session_state:
        st.session_state.current_status = "Ready"
    if 'task_history' not in st.session_state:
        st.session_state.task_history = []
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key (using from .env if available)
        default_key = os.getenv('DEEPSEEK_API_KEY', '')
        api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            value=default_key,
            help="Enter your DeepSeek API key"
        )
        
        # Browser settings
        headless = st.checkbox(
            "Headless Mode", 
            value=False,
            help="Uncheck to see the browser window"
        )
        
        st.markdown("---")
        st.markdown("### 🎯 Quick Tasks")
        
        if st.button("📰 News Search"):
            st.session_state.quick_url = "https://news.ycombinator.com"
            st.session_state.quick_task = "Browse the front page, read headlines, and take screenshots of interesting articles"
        
        if st.button("🛒 Shopping Demo"):
            st.session_state.quick_url = "https://demo.opencart.com"
            st.session_state.quick_task = "Browse products, add items to cart, and navigate through the shopping process"
        
        if st.button("🔍 Search Example"):
            st.session_state.quick_url = "https://www.google.com"
            st.session_state.quick_task = "Search for 'browser automation' and explore the first few results"
    
    # Main interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("🎯 Automation Task")
        
        # URL input
        default_url = getattr(st.session_state, 'quick_url', 'https://example.com')
        url = st.text_input(
            "🌐 Target Website",
            value=default_url,
            placeholder="https://example.com"
        )
        
        # Task description
        default_task = getattr(st.session_state, 'quick_task', '')
        task_description = st.text_area(
            "📋 What should the browser do?",
            value=default_task,
            placeholder="Example: Navigate to the homepage, click on the products link, and take screenshots of the product catalog",
            height=120
        )
        
        # Control buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button(
                "🚀 Start Browser Automation",
                type="primary",
                disabled=st.session_state.automation_runner.running
            ):
                if url and task_description and api_key:
                    if st.session_state.automation_runner.run_automation_sync(
                        url, task_description, api_key, headless
                    ):
                        st.session_state.task_history.append({
                            'url': url,
                            'task': task_description,
                            'timestamp': datetime.now(),
                            'status': 'running'
                        })
                        st.rerun()
                    else:
                        st.error("Another task is already running!")
                else:
                    st.error("Please fill in all fields!")
        
        with col_btn2:
            if st.button(
                "⏹️ Stop",
                disabled=not st.session_state.automation_runner.running
            ):
                st.session_state.automation_runner.running = False
                st.warning("Stopping automation...")
    
    with col2:
        st.header("📊 Status")
        
        # Status updates
        status_container = st.empty()
        
        # Check for new status
        status_update = st.session_state.automation_runner.get_status()
        if status_update:
            st.session_state.current_status = status_update
        
        # Display current status
        if st.session_state.automation_runner.running:
            status_container.info(f"🔄 {st.session_state.current_status}")
        else:
            status_container.success("✅ Ready")
        
        # Browser info
        if not headless and st.session_state.automation_runner.running:
            st.info("👁️ **Browser Window Open**\nYou should see a browser window performing the automation!")
        
        # Progress info
        if st.session_state.automation_runner.running:
            st.markdown("### 🎬 What to Watch For:")
            st.markdown("""
            - Browser window opening
            - Navigation to your URL
            - Automatic interactions
            - Screenshots being taken
            - Task completion
            """)
    
    # Check for results
    result = st.session_state.automation_runner.get_result()
    if result:
        if result["success"]:
            st.success("🎉 **Automation Completed Successfully!**")
            st.markdown("**Result Summary:**")
            st.text(str(result.get("result", "Task completed")))
            
            # Update history
            if st.session_state.task_history:
                st.session_state.task_history[-1]['status'] = 'completed'
        else:
            st.error(f"❌ **Automation Failed:** {result['error']}")
            
            # Show troubleshooting tips
            if "Import Error" in result['error']:
                with st.expander("🛠️ Setup Instructions", expanded=True):
                    st.markdown("""
                    **To enable real browser automation:**
                    
                    1. Install browser-use library:
                    ```bash
                    cd /Users/kunnath/Projects/aieasy/demo/browser-use
                    pip install -e .
                    ```
                    
                    2. Install playwright browsers:
                    ```bash
                    playwright install chromium
                    ```
                    
                    3. Make sure your DeepSeek API key is set
                    """)
            
            # Update history
            if st.session_state.task_history:
                st.session_state.task_history[-1]['status'] = 'failed'
    
    # Auto-refresh during automation
    if st.session_state.automation_runner.running:
        time.sleep(1)
        st.rerun()
    
    # Task history
    if st.session_state.task_history:
        st.markdown("---")
        st.subheader("📋 Recent Tasks")
        
        for i, task in enumerate(reversed(st.session_state.task_history[-5:])):
            status_icon = {
                'running': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(task['status'], '❓')
            
            with st.expander(f"{status_icon} {task['timestamp'].strftime('%H:%M:%S')} - {task['url']}", expanded=False):
                st.write(f"**Task:** {task['task']}")
                st.write(f"**Status:** {task['status'].title()}")
    
    # Instructions
    st.markdown("---")
    st.markdown("""
    ### 🎯 How to Use:
    1. **Enter a website URL** you want to automate
    2. **Describe the task** in detail (what should the browser do?)
    3. **Add your DeepSeek API key** in the sidebar
    4. **Click "Start Browser Automation"**
    5. **Watch the browser window** perform the task automatically!
    
    ### 💡 Tips:
    - **Uncheck "Headless Mode"** to see the browser in action
    - **Be specific** in your task descriptions
    - **Start with simple websites** like example.com
    - **The AI will take screenshots** and explain its actions
    """)

if __name__ == "__main__":
    main()