#!/usr/bin/env python3
"""
Browser Use Agent Temp File Cleanup Script
Cleans up old browser_use_agent temporary files and directories
"""

import os
import shutil
import glob
import time
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_browser_use_temp_files(temp_dir="/tmp", days_old=1, dry_run=True):
    """
    Clean up browser_use_agent temporary files and directories
    
    Args:
        temp_dir (str): Temporary directory path (default: /tmp)
        days_old (int): Remove files older than this many days (default: 1)
        dry_run (bool): If True, only show what would be deleted without actually deleting
    """
    
    # For macOS, the temp directory is usually in /var/folders/...
    # We'll check both common locations
    temp_paths = [
        temp_dir,
        "/var/folders/rp/p5482cg53m780jj0yk1cpwyr/T/",
        "/tmp"
    ]
    
    total_size = 0
    total_files = 0
    
    cutoff_time = time.time() - (days_old * 24 * 60 * 60)
    
    print(f"🧹 Browser Use Agent Cleanup Script")
    print(f"{'🔍 DRY RUN MODE - No files will be deleted' if dry_run else '⚠️  LIVE MODE - Files will be deleted'}")
    print(f"📅 Removing files older than {days_old} day(s)")
    print("-" * 60)
    
    for temp_path in temp_paths:
        if not os.path.exists(temp_path):
            continue
            
        print(f"\n📂 Scanning: {temp_path}")
        
        # Look for browser_use_agent files and directories
        pattern = os.path.join(temp_path, "*browser_use_agent*")
        matches = glob.glob(pattern)
        
        for match in matches:
            try:
                # Get file/directory info
                stat_info = os.stat(match)
                file_age = stat_info.st_mtime
                file_size = 0
                
                if os.path.isdir(match):
                    # Calculate directory size
                    for root, dirs, files in os.walk(match):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                file_size += os.path.getsize(file_path)
                            except (OSError, IOError):
                                continue
                    item_type = "📁 DIR "
                else:
                    file_size = stat_info.st_size
                    item_type = "📄 FILE"
                
                # Check if file is old enough
                if file_age < cutoff_time:
                    age_days = (time.time() - file_age) / (24 * 60 * 60)
                    size_mb = file_size / (1024 * 1024)
                    
                    print(f"  {item_type} {os.path.basename(match)} ({size_mb:.1f}MB, {age_days:.1f} days old)")
                    
                    if not dry_run:
                        if os.path.isdir(match):
                            shutil.rmtree(match)
                            print(f"    ✅ Deleted directory")
                        else:
                            os.remove(match)
                            print(f"    ✅ Deleted file")
                    
                    total_size += file_size
                    total_files += 1
                
            except (OSError, IOError) as e:
                print(f"  ❌ Error processing {match}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Summary:")
    print(f"   Files/Directories found: {total_files}")
    print(f"   Total size: {total_size / (1024 * 1024):.1f} MB")
    
    if dry_run:
        print(f"   💡 Run with dry_run=False to actually delete these files")
    else:
        print(f"   ✅ Cleanup completed!")

def setup_automatic_cleanup():
    """
    Create a script for automatic cleanup that can be run via cron
    """
    
    cleanup_script = '''#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(__file__))

# Import and run cleanup
from browser_use_cleanup import cleanup_browser_use_temp_files

# Clean up files older than 1 day
cleanup_browser_use_temp_files(days_old=1, dry_run=False)
'''
    
    script_path = "browser_use_auto_cleanup.py"
    with open(script_path, 'w') as f:
        f.write(cleanup_script)
    
    os.chmod(script_path, 0o755)
    
    print(f"📝 Created automatic cleanup script: {script_path}")
    print(f"💡 You can add this to your crontab to run daily:")
    print(f"   0 2 * * * cd {os.getcwd()} && python3 {script_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up browser_use_agent temporary files")
    parser.add_argument("--days", type=int, default=1, help="Remove files older than N days (default: 1)")
    parser.add_argument("--temp-dir", default="/tmp", help="Temporary directory path")
    parser.add_argument("--execute", action="store_true", help="Actually delete files (default is dry-run)")
    parser.add_argument("--setup-auto", action="store_true", help="Setup automatic cleanup script")
    
    args = parser.parse_args()
    
    if args.setup_auto:
        setup_automatic_cleanup()
    else:
        cleanup_browser_use_temp_files(
            temp_dir=args.temp_dir,
            days_old=args.days,
            dry_run=not args.execute
        )