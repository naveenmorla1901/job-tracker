"""
Utility functions for process information and monitoring
"""
import psutil
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("job_tracker.utils.process_info")

def get_process_info() -> Dict[str, Any]:
    """Get information about running processes"""
    try:
        process_info = {}
        
        # Get total process count
        process_count = len(list(psutil.process_iter()))
        process_info["total_count"] = process_count
        
        # Look for specific processes
        target_processes = [
            "python", "python3", "uvicorn", "streamlit", 
            "nginx", "postgresql", "postgres", "gunicorn"
        ]
        
        found_processes = {}
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username', 'memory_info', 'cpu_percent']):
            try:
                pinfo = proc.info
                pname = pinfo['name'].lower()
                
                # Check for target processes
                is_target = False
                for target in target_processes:
                    if target in pname:
                        is_target = True
                        break
                
                # For Python processes, check if they're related to our application
                if "python" in pname and pinfo.get('cmdline'):
                    cmdline = " ".join(pinfo['cmdline'])
                    if any(app_cmd in cmdline for app_cmd in ["uvicorn main:app", "streamlit run dashboard.py", "job_tracker"]):
                        is_target = True
                        for app_name in ["uvicorn", "streamlit"]:
                            if app_name in cmdline:
                                pname = app_name
                
                if is_target:
                    if pname not in found_processes:
                        found_processes[pname] = []
                    
                    memory_mb = 0
                    if pinfo.get('memory_info'):
                        memory_mb = pinfo['memory_info'].rss // (1024 * 1024)
                    
                    process_detail = {
                        "pid": pinfo['pid'],
                        "username": pinfo.get('username', ''),
                        "memory_mb": memory_mb,
                        "cpu_percent": pinfo.get('cpu_percent', 0),
                    }
                    
                    if pinfo.get('cmdline'):
                        process_detail["cmdline"] = " ".join(pinfo['cmdline'])
                    
                    found_processes[pname].append(process_detail)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        process_info["application_processes"] = found_processes
        
        # Count processes by user
        users = {}
        for proc in psutil.process_iter(['username']):
            try:
                username = proc.info['username']
                if username not in users:
                    users[username] = 0
                users[username] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        process_info["processes_by_user"] = users
        
        # Get top processes by memory usage
        top_processes_by_memory = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if proc.info.get('memory_info'):
                    memory_mb = proc.info['memory_info'].rss // (1024 * 1024)
                    if memory_mb > 1:  # Only include processes using > 1MB
                        top_processes_by_memory.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "memory_mb": memory_mb
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by memory usage (descending) and take top 10
        top_processes_by_memory = sorted(top_processes_by_memory, key=lambda x: x["memory_mb"], reverse=True)[:10]
        process_info["top_by_memory"] = top_processes_by_memory
        
        return process_info
    except Exception as e:
        logger.error(f"Error getting process info: {str(e)}")
        return {"error": str(e)}
