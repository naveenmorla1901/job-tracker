"""
Utility functions for system_info.py
"""
import os
import subprocess
import datetime
import platform
import psutil
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("job_tracker.system_info_utils")

def get_project_info() -> Dict[str, Any]:
    """Get information about the job-tracker project folder"""
    try:
        project_info = {}
        
        # Determine the project directory
        project_dir = os.path.abspath(os.path.dirname(__file__))
        project_info["path"] = project_dir
        
        # Calculate directory size and structure
        folder_sizes = {}
        total_size = 0
        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(project_dir):
            path_size = 0
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    file_size = os.path.getsize(fp)
                    path_size += file_size
                    total_size += file_size
                    file_count += 1
            
            # Add this directory's size to our structure
            rel_path = os.path.relpath(dirpath, project_dir)
            if rel_path == '.':
                rel_path = 'root'
                
            # Only track immediate subdirectories for clarity
            if rel_path == 'root' or rel_path.count(os.sep) == 0:
                folder_sizes[rel_path] = path_size
        
        project_info["size_bytes"] = total_size
        project_info["size_mb"] = round(total_size / (1024 * 1024), 2)
        project_info["size_gb"] = round(total_size / (1024 * 1024 * 1024), 3)
        project_info["file_count"] = file_count
        
        # Add folder size breakdown
        folder_sizes_mb = {}
        for folder, size in folder_sizes.items():
            folder_sizes_mb[folder] = round(size / (1024 * 1024), 2)
            
        project_info["folder_sizes_mb"] = folder_sizes_mb
        
        # Sort folders by size (descending)
        sorted_folders = sorted(folder_sizes_mb.items(), key=lambda x: x[1], reverse=True)
        project_info["folders_by_size"] = sorted_folders
        
        # Check logs size separately
        logs_dir = os.path.join(project_dir, "logs")
        logs_size = 0
        logs_count = 0
        log_files_info = {}
        
        if os.path.exists(logs_dir):
            for dirpath, dirnames, filenames in os.walk(logs_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        file_size = os.path.getsize(fp)
                        logs_size += file_size
                        logs_count += 1
                        
                        if f.endswith('.log'):
                            log_files_info[f] = {
                                "size_mb": round(file_size / (1024 * 1024), 2),
                                "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M:%S")
                            }
        
        project_info["logs_size_mb"] = round(logs_size / (1024 * 1024), 2)
        project_info["logs_count"] = logs_count
        project_info["log_files"] = log_files_info
        
        # Check individual log file sizes
        main_log_files = {}
        for log_file in ["job_tracker.log", "dashboard.log", "api.log"]:
            file_path = os.path.join(project_dir, log_file)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                main_log_files[log_file] = {
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "size_bytes": file_size,
                    "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                }
        
        project_info["main_log_files"] = main_log_files
        
        # Check Git information if available
        git_info = {}
        git_dir = os.path.join(project_dir, ".git")
        if os.path.exists(git_dir):
            git_info["has_git"] = True
            
            try:
                # Get current branch
                head_file = os.path.join(git_dir, "HEAD")
                if os.path.exists(head_file):
                    with open(head_file, 'r') as f:
                        content = f.read().strip()
                        if content.startswith("ref: refs/heads/"):
                            git_info["current_branch"] = content.replace("ref: refs/heads/", "")
                
                # Count commits if possible
                try:
                    git_log = subprocess.check_output(
                        ["git", "-C", project_dir, "rev-list", "--count", "HEAD"],
                        stderr=subprocess.DEVNULL
                    ).decode().strip()
                    git_info["commit_count"] = int(git_log)
                except:
                    pass
                
                # Get last commit info
                try:
                    last_commit = subprocess.check_output(
                        ["git", "-C", project_dir, "log", "-1", "--pretty=format:%h|%an|%ad|%s"],
                        stderr=subprocess.DEVNULL
                    ).decode().strip()
                    
                    if last_commit:
                        parts = last_commit.split('|')
                        if len(parts) >= 4:
                            git_info["last_commit"] = {
                                "hash": parts[0],
                                "author": parts[1],
                                "date": parts[2],
                                "message": parts[3]
                            }
                except:
                    pass
            except:
                pass
            
            project_info["git"] = git_info
        
        # Get information about virtual environment
        venv_info = {}
        venv_dir = os.path.join(project_dir, "venv")
        if os.path.exists(venv_dir):
            venv_info["exists"] = True
            
            # Calculate venv size
            venv_size = 0
            venv_file_count = 0
            for dirpath, dirnames, filenames in os.walk(venv_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        venv_size += os.path.getsize(fp)
                        venv_file_count += 1
            
            venv_info["size_mb"] = round(venv_size / (1024 * 1024), 2)
            venv_info["file_count"] = venv_file_count
            
            # Try to get Python version used by venv
            python_path = None
            if platform.system() == "Windows":
                python_path = os.path.join(venv_dir, "Scripts", "python.exe")
            else:
                python_path = os.path.join(venv_dir, "bin", "python")
                
            if python_path and os.path.exists(python_path):
                try:
                    version_output = subprocess.check_output(
                        [python_path, "--version"], 
                        stderr=subprocess.STDOUT
                    ).decode().strip()
                    
                    if version_output.startswith("Python "):
                        venv_info["python_version"] = version_output.replace("Python ", "")
                except:
                    pass
        else:
            venv_info["exists"] = False
            
        project_info["venv"] = venv_info
        
        # Get information about database if possible
        db_info = {}
        try:
            # Try to get a list of database files
            db_files = [f for f in os.listdir(project_dir) if f.endswith(".db")]
            
            if db_files:
                db_info["files"] = []
                for db_file in db_files:
                    file_path = os.path.join(project_dir, db_file)
                    size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
                    db_info["files"].append({
                        "name": db_file,
                        "size_mb": size_mb
                    })
                    
            # Check for PostgreSQL database
            db_url_file = os.path.join(project_dir, ".env")
            if os.path.exists(db_url_file):
                with open(db_url_file, 'r') as f:
                    for line in f:
                        if line.startswith("DATABASE_URL="):
                            db_info["has_database_url"] = True
                            db_type = "unknown"
                            if "postgresql://" in line:
                                db_type = "postgresql"
                            elif "sqlite://" in line:
                                db_type = "sqlite"
                            db_info["type"] = db_type
                            break
        except:
            pass
        
        project_info["database"] = db_info
        
        return project_info
    except Exception as e:
        logger.error(f"Error getting project info: {str(e)}")
        return {"error": str(e)}

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

def format_system_info(info):
    """Format system information for display"""
    formatted = []
    
    # System Overview
    formatted.append("System Information:")
    formatted.append(f"  Platform: {info['system']['platform']}")
    formatted.append(f"  Hostname: {info['system']['node']}")
    formatted.append(f"  Processor: {info['system']['processor']}")
    formatted.append(f"  Python Version: {info['system']['python_version']}")
    formatted.append("")
    
    # CPU
    if "cpu" in info and info["cpu"]:
        formatted.append("CPU:")
        if "model" in info["cpu"]:
            formatted.append(f"  Model: {info['cpu']['model']}")
        if "count_physical" in info["cpu"]:
            formatted.append(f"  Physical Cores: {info['cpu']['count_physical']}")
            formatted.append(f"  Logical Cores: {info['cpu']['count_logical']}")
        if "used_percent" in info["cpu"]:
            formatted.append(f"  Usage: {info['cpu']['used_percent']:.1f}%")
        if "load_1min" in info["cpu"]:
            formatted.append(f"  Load Avg: {info['cpu']['load_1min']} (1m), {info['cpu']['load_5min']} (5m), {info['cpu']['load_15min']} (15m)")
        if "frequency_mhz" in info["cpu"]:
            freq = info["cpu"]["frequency_mhz"]
            formatted.append(f"  CPU Frequency: {freq['current']} MHz (Current)")
        formatted.append("")
    
    # Memory
    if "memory" in info and info["memory"]:
        formatted.append("Memory:")
        if "total_mb" in info["memory"]:
            total_gb = info["memory"]["total_mb"] / 1024
            used_gb = info["memory"]["used_mb"] / 1024
            free_gb = info["memory"]["free_mb"] / 1024
            formatted.append(f"  Total: {total_gb:.2f} GB")
            formatted.append(f"  Used: {used_gb:.2f} GB ({info['memory']['used_percent']}%)")
            formatted.append(f"  Free: {free_gb:.2f} GB")
            
        if "swap" in info["memory"]:
            swap = info["memory"]["swap"]
            swap_total_gb = swap["total_mb"] / 1024
            swap_used_gb = swap["used_mb"] / 1024
            formatted.append(f"  Swap: {swap_used_gb:.2f} GB / {swap_total_gb:.2f} GB ({swap['used_percent']}%)")
        formatted.append("")
    
    # Disk
    if "disk" in info and info["disk"]:
        formatted.append("Disk:")
        if "root" in info["disk"]:
            root = info["disk"]["root"]
            formatted.append(f"  Total: {root['total_gb']} GB")
            formatted.append(f"  Used: {root['used_gb']} GB ({root['used_percent']}%)")
            formatted.append(f"  Free: {root['free_gb']} GB")
            
        if "partitions" in info["disk"]:
            formatted.append("  Partitions:")
            for partition in info["disk"]["partitions"]:
                if partition["mountpoint"] != "/" and partition["mountpoint"] != "C:\\":
                    formatted.append(f"    {partition['mountpoint']}: {partition['used_gb']} GB / {partition['total_gb']} GB ({partition['used_percent']}%)")
        formatted.append("")
    
    # Network
    if "network" in info and info["network"]:
        formatted.append("Network:")
        if "active_connections" in info["network"]:
            formatted.append(f"  Active Connections: {info['network']['active_connections']}")
        
        # Interfaces
        if "interfaces" in info["network"]:
            for interface in info["network"]["interfaces"]:
                if "addresses" in interface and interface["addresses"]:
                    formatted.append(f"  Interface: {interface['name']}")
                    formatted.append(f"    IP Addresses: {', '.join(interface['addresses'])}")
                    if "mac" in interface:
                        formatted.append(f"    MAC: {interface['mac']}")
        
        # Service status
        if "api_port_active" in info["network"]:
            formatted.append(f"  API Service: {'Running' if info['network']['api_port_active'] else 'Not Running'} (Port 8000)")
        if "dashboard_port_active" in info["network"]:
            formatted.append(f"  Dashboard Service: {'Running' if info['network']['dashboard_port_active'] else 'Not Running'} (Port 8501)")
        if "nginx_active" in info["network"]:
            formatted.append(f"  Nginx Service: {'Running' if info['network']['nginx_active'] else 'Not Running'} (Port 80/443)")
        
        formatted.append("")
    
    # Uptime
    if "uptime" in info and info["uptime"]:
        formatted.append("Uptime:")
        if "uptime_formatted" in info["uptime"]:
            formatted.append(f"  System up: {info['uptime']['uptime_formatted']}")
        if "boot_datetime" in info["uptime"]:
            formatted.append(f"  Boot time: {info['uptime']['boot_datetime']}")
        formatted.append("")
    
    # Project
    if "project" in info and info["project"]:
        formatted.append("Project Information:")
        formatted.append(f"  Directory: {info['project']['path']}")
        formatted.append(f"  Size: {info['project']['size_mb']} MB ({info['project']['size_gb']} GB)")
        formatted.append(f"  Files: {info['project']['file_count']}")
        
        # Folder sizes
        if "folder_sizes_mb" in info["project"]:
            formatted.append("  Folder Sizes:")
            for folder, size in info["project"]["folders_by_size"]:
                if folder != "root" and size > 0.1:  # Skip very small folders
                    formatted.append(f"    {folder}: {size} MB")
        
        # Log files size
        if "log_files" in info["project"] and info["project"]["log_files"]:
            formatted.append("  Log Files:")
            for log_name, log_info in info["project"]["log_files"].items():
                formatted.append(f"    {log_name}: {log_info['size_mb']} MB (Modified: {log_info['last_modified']})")
        
        # Main log files
        if "main_log_files" in info["project"] and info["project"]["main_log_files"]:
            formatted.append("  Main Log Files:")
            for log_name, log_info in info["project"]["main_log_files"].items():
                formatted.append(f"    {log_name}: {log_info['size_mb']} MB (Modified: {log_info['last_modified']})")
                
        # Database
        if "database" in info["project"]:
            db = info["project"]["database"]
            if "type" in db:
                formatted.append(f"  Database Type: {db['type']}")
            if "files" in db:
                formatted.append("  Database Files:")
                for db_file in db["files"]:
                    formatted.append(f"    {db_file['name']}: {db_file['size_mb']} MB")
        formatted.append("")
        
        # Virtual Environment
        if "venv" in info["project"] and info["project"]["venv"]["exists"]:
            venv = info["project"]["venv"]
            formatted.append("  Virtual Environment:")
            formatted.append(f"    Size: {venv['size_mb']} MB")
            formatted.append(f"    Files: {venv['file_count']}")
            if "python_version" in venv:
                formatted.append(f"    Python Version: {venv['python_version']}")
            formatted.append("")
    
    # Processes
    if "processes" in info and info["processes"]:
        procs = info["processes"]
        formatted.append("Process Information:")
        formatted.append(f"  Total Processes: {procs.get('total_count', 'Unknown')}")
        
        # Application processes
        if "application_processes" in procs:
            formatted.append("  Application Processes:")
            for proc_type, processes in procs["application_processes"].items():
                formatted.append(f"    {proc_type} ({len(processes)} processes):")
                for p in processes:
                    formatted.append(f"      PID {p['pid']}: {p.get('memory_mb', 0)} MB RAM, {p.get('cpu_percent', 0)}% CPU")
                    if "cmdline" in p:
                        # Truncate long command lines
                        cmdline = p["cmdline"]
                        if len(cmdline) > 100:
                            cmdline = cmdline[:97] + "..."
                        formatted.append(f"        {cmdline}")
        
        # Top memory processes
        if "top_by_memory" in procs:
            formatted.append("  Top Processes by Memory:")
            for i, p in enumerate(procs["top_by_memory"]):
                formatted.append(f"    {i+1}. {p['name']} (PID {p['pid']}): {p['memory_mb']} MB")
        
        formatted.append("")
    
    return "\n".join(formatted)
