"""
System information utilities for job tracker
"""
import os
import subprocess
import json
import logging
import shutil
import platform
import datetime
import re
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logger = logging.getLogger("job_tracker.system_info")

def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information including:
    - CPU usage
    - Memory usage
    - Disk space
    - Network stats
    - System uptime
    - Project folder size
    
    Returns:
        Dict with system information
    """
    info = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": {
            "platform": platform.platform(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "cpu": get_cpu_info(),
        "uptime": get_uptime_info(),
        "network": get_network_info(),
        "project": get_project_info()
    }
    
    return info

def get_memory_info() -> Dict[str, Any]:
    """Get memory usage information"""
    try:
        if platform.system() == "Linux":
            # Use free command on Linux
            output = subprocess.check_output(["free", "-m"]).decode("utf-8")
            memory_lines = output.strip().split("\n")
            
            # Parse the memory line
            if len(memory_lines) >= 2:
                memory_values = re.split(r'\s+', memory_lines[1].strip())
                
                if len(memory_values) >= 7:
                    total = int(memory_values[1])
                    used = int(memory_values[2])
                    free = int(memory_values[3])
                    shared = int(memory_values[4])
                    buff_cache = int(memory_values[5])
                    available = int(memory_values[6])
                    
                    memory_info = {
                        "total_mb": total,
                        "used_mb": used,
                        "free_mb": free,
                        "shared_mb": shared,
                        "buff_cache_mb": buff_cache,
                        "available_mb": available,
                        "used_percent": round((used / total) * 100, 2),
                        "available_percent": round((available / total) * 100, 2)
                    }
                    return memory_info
        
        # Generic fallback approach for all systems
        total, available, percent, used, free = shutil.disk_usage("/")
        
        return {
            "total_mb": total // (1024 * 1024),
            "used_mb": used // (1024 * 1024),
            "free_mb": free // (1024 * 1024),
            "used_percent": percent,
            "available_percent": 100 - percent
        }
    except Exception as e:
        logger.error(f"Error getting memory info: {str(e)}")
        return {"error": str(e)}

def get_disk_info() -> Dict[str, Any]:
    """Get disk usage information"""
    try:
        disk_info = {}
        
        # Get usage of root directory
        total, used, free = shutil.disk_usage("/")
        root_info = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "used_percent": round((used / total) * 100, 2)
        }
        disk_info["root"] = root_info
        
        # In Linux, try to get more detailed filesystem info
        if platform.system() == "Linux":
            try:
                df_output = subprocess.check_output(["df", "-h"]).decode("utf-8")
                df_lines = df_output.strip().split("\n")
                
                filesystems = []
                for line in df_lines[1:]:  # Skip header
                    parts = re.split(r'\s+', line.strip())
                    if len(parts) >= 6:
                        filesystem = {
                            "filesystem": parts[0],
                            "size": parts[1],
                            "used": parts[2],
                            "available": parts[3],
                            "used_percent": parts[4],
                            "mounted_on": parts[5]
                        }
                        filesystems.append(filesystem)
                
                disk_info["filesystems"] = filesystems
            except Exception as e:
                logger.error(f"Error getting filesystem info: {str(e)}")
        
        return disk_info
    except Exception as e:
        logger.error(f"Error getting disk info: {str(e)}")
        return {"error": str(e)}

def get_cpu_info() -> Dict[str, Any]:
    """Get CPU usage information"""
    try:
        cpu_info = {}
        
        if platform.system() == "Linux":
            # Get CPU model
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            cpu_info["model"] = line.split(":")[1].strip()
                            break
            except:
                pass
                
            # Get CPU load
            try:
                with open("/proc/loadavg", "r") as f:
                    load = f.read().strip().split()
                    cpu_info["load_1min"] = float(load[0])
                    cpu_info["load_5min"] = float(load[1])
                    cpu_info["load_15min"] = float(load[2])
            except:
                pass
                
            # Get more detailed CPU usage with top
            try:
                top_output = subprocess.check_output(
                    ["top", "-bn", "1"], 
                    stderr=subprocess.STDOUT
                ).decode("utf-8")
                
                # Extract CPU percentages
                for line in top_output.split("\n"):
                    if line.startswith("%Cpu"):
                        parts = line.split(",")
                        user = float(parts[0].split(":")[1].strip().split()[0])
                        system = float(parts[1].strip().split()[0])
                        idle = float(parts[3].strip().split()[0])
                        
                        cpu_info["user_percent"] = user
                        cpu_info["system_percent"] = system
                        cpu_info["idle_percent"] = idle
                        cpu_info["used_percent"] = 100 - idle
                        break
            except:
                pass
        
        return cpu_info
    except Exception as e:
        logger.error(f"Error getting CPU info: {str(e)}")
        return {"error": str(e)}

def get_uptime_info() -> Dict[str, Any]:
    """Get system uptime information"""
    try:
        uptime_info = {}
        
        if platform.system() == "Linux":
            try:
                with open("/proc/uptime", "r") as f:
                    uptime_seconds = float(f.read().split()[0])
                    days, remainder = divmod(uptime_seconds, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    uptime_info["days"] = int(days)
                    uptime_info["hours"] = int(hours)
                    uptime_info["minutes"] = int(minutes)
                    uptime_info["seconds"] = int(seconds)
                    uptime_info["total_seconds"] = int(uptime_seconds)
                    uptime_info["uptime_formatted"] = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
            except:
                # Alternative: use uptime command
                uptime_output = subprocess.check_output(["uptime"]).decode("utf-8").strip()
                uptime_info["uptime_output"] = uptime_output
        
        return uptime_info
    except Exception as e:
        logger.error(f"Error getting uptime info: {str(e)}")
        return {"error": str(e)}

def get_network_info() -> Dict[str, Any]:
    """Get network usage information"""
    try:
        network_info = {
            "interfaces": []
        }
        
        if platform.system() == "Linux":
            try:
                # Use netstat to get active connections
                netstat_output = subprocess.check_output(
                    ["netstat", "-tn"], 
                    stderr=subprocess.STDOUT
                ).decode("utf-8")
                
                active_connections = len([
                    line for line in netstat_output.split('\n') 
                    if 'ESTABLISHED' in line
                ])
                
                network_info["active_connections"] = active_connections
                
                # Get interfaces information (simplified)
                interfaces_output = subprocess.check_output(
                    ["ip", "-s", "addr"], 
                    stderr=subprocess.STDOUT
                ).decode("utf-8")
                
                interfaces = []
                interface = None
                for line in interfaces_output.split('\n'):
                    if ': ' in line and '<' in line and '>' in line:
                        # Start of a new interface
                        if interface:
                            interfaces.append(interface)
                        interface_name = line.split(': ')[1].split(':')[0]
                        interface = {"name": interface_name, "addresses": []}
                    elif interface and 'inet ' in line:
                        # IP address
                        ip = line.strip().split()[1].split('/')[0]
                        interface["addresses"].append(ip)
                
                if interface:
                    interfaces.append(interface)
                
                network_info["interfaces"] = interfaces
                
                # HTTP traffic (from process listening on port 8000, 8501)
                try:
                    # Check if ports are in use
                    port_check = subprocess.check_output(["netstat", "-tnlp"]).decode("utf-8")
                    
                    api_active = ":8000 " in port_check
                    dashboard_active = ":8501 " in port_check
                    
                    network_info["api_port_active"] = api_active
                    network_info["dashboard_port_active"] = dashboard_active
                except:
                    pass
            except Exception as e:
                logger.error(f"Error in network info subprocess: {str(e)}")
        
        return network_info
    except Exception as e:
        logger.error(f"Error getting network info: {str(e)}")
        return {"error": str(e)}

def get_project_info() -> Dict[str, Any]:
    """Get information about the job-tracker project folder"""
    try:
        project_info = {}
        
        # Determine the project directory
        project_dir = os.path.abspath(os.path.dirname(__file__))
        project_info["path"] = project_dir
        
        # Calculate directory size
        total_size = 0
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(project_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
                    file_count += 1
        
        project_info["size_bytes"] = total_size
        project_info["size_mb"] = round(total_size / (1024 * 1024), 2)
        project_info["file_count"] = file_count
        
        # Check logs size separately
        logs_dir = os.path.join(project_dir, "logs")
        logs_size = 0
        logs_count = 0
        
        if os.path.exists(logs_dir):
            for dirpath, dirnames, filenames in os.walk(logs_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        logs_size += os.path.getsize(fp)
                        logs_count += 1
        
        project_info["logs_size_mb"] = round(logs_size / (1024 * 1024), 2)
        project_info["logs_count"] = logs_count
        
        # Check individual log file sizes
        log_files = {}
        for log_file in ["job_tracker.log", "dashboard.log", "api.log"]:
            file_path = os.path.join(project_dir, log_file)
            if os.path.exists(file_path):
                size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
                log_files[log_file] = {"size_mb": size_mb}
        
        project_info["log_files"] = log_files
        
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
        except:
            pass
        
        project_info["database"] = db_info
        
        return project_info
    except Exception as e:
        logger.error(f"Error getting project info: {str(e)}")
        return {"error": str(e)}

def get_api_stats() -> Dict[str, Any]:
    """Get statistics about API usage if available"""
    try:
        api_stats = {}
        
        # Try to count job entries in the database
        try:
            from app.db.database import get_db
            from app.db.models import Job, ScraperRun
            
            db = next(get_db())
            
            # Count jobs
            total_jobs = db.query(Job).count()
            active_jobs = db.query(Job).filter(Job.is_active == True).count()
            
            # Count companies
            companies = db.query(Job.company).distinct().count()
            
            # Count recent scraper runs
            recent_runs = db.query(ScraperRun).order_by(ScraperRun.id.desc()).limit(100).all()
            
            success_runs = sum(1 for run in recent_runs if run.status == "success")
            failure_runs = sum(1 for run in recent_runs if run.status == "failure")
            
            # Calculate success rate
            if recent_runs:
                success_rate = (success_runs / len(recent_runs)) * 100
            else:
                success_rate = 0
                
            api_stats["database"] = {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "companies": companies,
                "recent_scraper_runs": len(recent_runs),
                "success_rate": round(success_rate, 2)
            }
            
            db.close()
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
        
        return api_stats
    except Exception as e:
        logger.error(f"Error getting API stats: {str(e)}")
        return {"error": str(e)}

def format_system_info(info):
    """Format system information for display"""
    formatted = []
    
    # System Overview
    formatted.append("System Information:")
    formatted.append(f"  Platform: {info['system']['platform']}")
    formatted.append(f"  Hostname: {info['system']['node']}")
    formatted.append(f"  Processor: {info['system']['processor']}")
    formatted.append("")
    
    # CPU
    if "cpu" in info and info["cpu"]:
        formatted.append("CPU:")
        if "model" in info["cpu"]:
            formatted.append(f"  Model: {info['cpu']['model']}")
        if "used_percent" in info["cpu"]:
            formatted.append(f"  Usage: {info['cpu']['used_percent']:.1f}%")
        if "load_1min" in info["cpu"]:
            formatted.append(f"  Load Avg: {info['cpu']['load_1min']} (1m), {info['cpu']['load_5min']} (5m), {info['cpu']['load_15min']} (15m)")
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
        formatted.append("")
    
    # Disk
    if "disk" in info and info["disk"]:
        formatted.append("Disk:")
        if "root" in info["disk"]:
            root = info["disk"]["root"]
            formatted.append(f"  Total: {root['total_gb']} GB")
            formatted.append(f"  Used: {root['used_gb']} GB ({root['used_percent']}%)")
            formatted.append(f"  Free: {root['free_gb']} GB")
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
        
        # Service status
        if "api_port_active" in info["network"]:
            formatted.append(f"  API Service: {'Running' if info['network']['api_port_active'] else 'Not Running'} (Port 8000)")
        if "dashboard_port_active" in info["network"]:
            formatted.append(f"  Dashboard Service: {'Running' if info['network']['dashboard_port_active'] else 'Not Running'} (Port 8501)")
        formatted.append("")
    
    # Uptime
    if "uptime" in info and info["uptime"]:
        formatted.append("Uptime:")
        if "uptime_formatted" in info["uptime"]:
            formatted.append(f"  System up: {info['uptime']['uptime_formatted']}")
        elif "uptime_output" in info["uptime"]:
            formatted.append(f"  {info['uptime']['uptime_output']}")
        formatted.append("")
    
    # Project
    if "project" in info and info["project"]:
        formatted.append("Project Information:")
        formatted.append(f"  Directory: {info['project']['path']}")
        formatted.append(f"  Size: {info['project']['size_mb']} MB")
        formatted.append(f"  Files: {info['project']['file_count']}")
        
        # Log files
        if "log_files" in info["project"] and info["project"]["log_files"]:
            formatted.append("  Log Files:")
            for log_name, log_info in info["project"]["log_files"].items():
                formatted.append(f"    {log_name}: {log_info['size_mb']} MB")
                
        # Database
        if "database" in info["project"] and "files" in info["project"]["database"]:
            formatted.append("  Database Files:")
            for db_file in info["project"]["database"]["files"]:
                formatted.append(f"    {db_file['name']}: {db_file['size_mb']} MB")
        formatted.append("")
    
    return "\n".join(formatted)

if __name__ == "__main__":
    # When run directly, print system information
    info = get_system_info()
    print(format_system_info(info))
