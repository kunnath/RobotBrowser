import shutil
from pathlib import Path

def get_latest_report_name(reports_base_dir: Path) -> str | None:
    # Find the latest report folder by modification time
    report_folders = [f for f in reports_base_dir.iterdir() if f.is_dir()]
    if not report_folders:
        return None
    latest_report = max(report_folders, key=lambda f: f.stat().st_mtime)
    return latest_report.name

def copy_agent_screenshots_to_report(report_screenshots_dir: Path):
    # 1. Find the latest browser_use_agent_* temp folder
    temp_base = Path("/var/folders/rp/p5482cg53m780jj0yk1cpwyr0000gn/T")
    agent_folders = sorted(temp_base.glob("browser_use_agent_*/screenshots"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not agent_folders:
        print("No agent screenshots folder found.")
        return

    latest_screenshots_dir = agent_folders[0]
    print(f"Copying from: {latest_screenshots_dir}")

    # 2. Ensure the report screenshots directory exists
    report_screenshots_dir.mkdir(parents=True, exist_ok=True)

    # 3. Copy all PNG files
    for png_file in latest_screenshots_dir.glob("*.png"):
        shutil.copy2(png_file, report_screenshots_dir / png_file.name)
        print(f"Copied {png_file} to {report_screenshots_dir / png_file.name}")

# Usage example (run after status == "Ready"):
reports_base_dir = Path("automation_reports")
latest_report_name = get_latest_report_name(reports_base_dir)
if latest_report_name:
    report_screenshots_dir = reports_base_dir / latest_report_name / "screenshots"
    copy_agent_screenshots_to_report(report_screenshots_dir)
else:
    print("No report folders found.")