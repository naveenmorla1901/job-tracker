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
import psutil
from typing import Dict, Any, List, Optional, Tuple

# Import support module with additional functions
from system_info_utils import get_project_info, get_process_info, format_system_info

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
    - Process information
    
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
            "python_version": platform.python_version(),
        },
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "cpu": get_cpu_info(),
        "uptime": get_uptime_info(),
        "network": get_network_info(),
        "project": get_project_info(),
        "processes": get_process_info()
    }
    
    return info

def get_memory_info() -> Dict[str, Any]:
    """Get memory usage information"""
    try:
        memory_info = {}
        
        # Use psutil for cross-platform memory info
        vm = psutil.virtual_memory()
        memory_info = {
            "total_mb": vm.total // (1024 * 1024),
            "available_mb": vm.available // (1024 * 1024),
            "used_mb": vm.used // (1024 * 1024),
            "free_mb": vm.free // (1024 * 1024),
            "used_percent": vm.percent,
            "available_percent": 100 - vm.percent
        }
        
        # Add swap information
        swap = psutil.swap_memory()
        memory_info["swap"] = {
            "total_mb": swap.total // (1024 * 1024),
            "used_mb": swap.used // (1024 * 1024),
            "free_mb": swap.free // (1024 * 1024),
            "used_percent": swap.percent
        }
        
        return memory_info
    except Exception as e:
        logger.error(f"Error getting memory info: {str(e)}")
        return {"error": str(e)}

def get_disk_info() -> Dict[str, Any]:
    """Get disk usage information"""
    try:
        disk_info = {"partitions": [], "total": {}}
        
        # Get all partitions
        for partition in psutil.disk_partitions():
            try:
                if os.name == 'nt' and 'cdrom' in partition.opts or partition.fstype == '':
                    # Skip CD-ROM drives on Windows
                    continue
                    
                usage = psutil.disk_usage(partition.mountpoint)
                
                partition_info = {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "used_percent": usage.percent
                }
                
                disk_info["partitions"].append(partition_info)
                
                # If this is the root or main partition, use it for total
                if partition.mountpoint == '/' or partition.mountpoint == 'C:\\':
                    disk_info["root"] = partition_info
            except:
                # Skip partitions that can't be accessed
                continue
                
        # If root wasn't set, use the first partition
        if "root" not in disk_info and disk_info["partitions"]:
            disk_info["root"] = disk_info["partitions"][0]
        
        # Add total disk I/O statistics
        io_counters = psutil.disk_io_counters()
        if io_counters:
            disk_info["io"] = {
                "read_mb": io_counters.read_bytes // (1024 * 1024),
                "write_mb": io_counters.write_bytes // (1024 * 1024),
                "read_count": io_counters.read_count,
                "write_count": io_counters.write_count
            }
            
        return disk_info
    except Exception as e:
        logger.error(f"Error getting disk info: {str(e)}")
        return {"error": str(e)}

def get_cpu_info() -> Dict[str, Any]:
    """Get CPU usage information"""
    try:
        cpu_info = {}
        
        # Get CPU count and usage
        cpu_info["count_physical"] = psutil.cpu_count(logical=False)
        cpu_info["count_logical"] = psutil.cpu_count(logical=True)
        
        # Get current CPU utilization (averaged over all cores)
        cpu_info["used_percent"] = psutil.cpu_percent(interval=0.5)
        
        # Get per-CPU utilization
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_info["per_cpu_percent"] = per_cpu
        
        # Get CPU frequency if available
        freq = psutil.cpu_freq()
        if freq:
            cpu_info["frequency_mhz"] = {
                "current": round(freq.current, 2),
                "min": round(freq.min, 2) if freq.min else None,
                "max": round(freq.max, 2) if freq.max else None
            }
        
        # Get CPU load average if on Unix
        if hasattr(psutil, "getloadavg"):
            load1, load5, load15 = psutil.getloadavg()
            cpu_info["load_1min"] = load1
            cpu_info["load_5min"] = load5
            cpu_info["load_15min"] = load15
        
        # Get CPU stats
        stats = psutil.cpu_stats()
        if stats:
            cpu_info["stats"] = {
                "ctx_switches": stats.ctx_switches,
                "interrupts": stats.interrupts,
                "soft_interrupts": stats.soft_interrupts,
                "syscalls": stats.syscalls
            }
        
        # Try to get CPU model information
        if platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            cpu_info["model"] = line.split(":")[1].strip()
                            break
            except:
                pass
        elif platform.system() == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                cpu_info["model"] = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                winreg.CloseKey(key)
            except:
                pass
        elif platform.system() == "Darwin":  # macOS
            try:
                output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode("utf-8").strip()
                cpu_info["model"] = output
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
        
        # Get boot time
        boot_time = psutil.boot_time()
        boot_datetime = datetime.datetime.fromtimestamp(boot_time)
        
        # Calculate uptime
        uptime_seconds = (datetime.datetime.now() - boot_datetime).total_seconds()
        
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_info["boot_time"] = boot_time
        uptime_info["boot_datetime"] = boot_datetime.strftime("%Y-%m-%d %H:%M:%S")
        uptime_info["days"] = int(days)
        uptime_info["hours"] = int(hours)
        uptime_info["minutes"] = int(minutes)
        uptime_info["seconds"] = int(seconds)
        uptime_info["total_seconds"] = int(uptime_seconds)
        uptime_info["uptime_formatted"] = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
        
        return uptime_info
    except Exception as e:
        logger.error(f"Error getting uptime info: {str(e)}")
        return {"error": str(e)}

def get_network_info() -> Dict[str, Any]:
    """Get network usage information"""
    try:
        network_info = {}
        
        # Get network interfaces and addresses
        network_info["interfaces"] = []
        
        # Get all network interfaces
        addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in addrs.items():
            interface = {"name": interface_name, "addresses": []}
            
            for addr in interface_addresses:
                if addr.family == psutil.AF_LINK:
                    interface["mac"] = addr.address
                elif addr.family in (2, 30):  # IPv4 or IPv6
                    interface["addresses"].append(addr.address)
            
            if "addresses" in interface and interface["addresses"]:
                network_info["interfaces"].append(interface)
        
        # Get network I/O statistics
        io_counters = psutil.net_io_counters(pernic=True)
        if io_counters:
            network_info["io"] = {}
            
            for nic, counters in io_counters.items():
                network_info["io"][nic] = {
                    "bytes_sent_mb": counters.bytes_sent // (1024 * 1024),
                    "bytes_recv_mb": counters.bytes_recv // (1024 * 1024),
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                    "errin": counters.errin,
                    "errout": counters.errout,
                    "dropin": counters.dropin,
                    "dropout": counters.dropout
                }
        
        # Get connection information
        network_info["connections"] = {}
        
        try:
            # Count by connection status
            connections = psutil.net_connections()
            by_status = {}
            
            for conn in connections:
                status = conn.status
                if status not in by_status:
                    by_status[status] = 0
                by_status[status] += 1
            
            network_info["connections"]["by_status"] = by_status
            network_info["connections"]["total"] = len(connections)
            network_info["active_connections"] = by_status.get("ESTABLISHED", 0)
        except:
            # Needs elevated privileges on some systems
            network_info["connections"]["error"] = "Insufficient privileges to get connection information"
        
        # Check if specific ports are in use for our services
        network_info["api_port_active"] = is_port_in_use(8000)
        network_info["dashboard_port_active"] = is_port_in_use(8501)
        network_info["nginx_active"] = is_port_in_use(80) or is_port_in_use(443)
        
        # Get running services using psutil
        services = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if this process is related to our application
                if any(service in proc.info['name'].lower() for service in ['uvicorn', 'streamlit', 'nginx']):
                    services.append({
                        "name": proc.info['name'],
                        "pid": proc.info['pid'],
                        "cmdline": " ".join(proc.info.get('cmdline', [])) if proc.info.get('cmdline') else ""
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        network_info["services"] = services
        
        return network_info
    except Exception as e:
        logger.error(f"Error getting network info: {str(e)}")
        return {"error": str(e)}

def is_port_in_use(port):
    """Check if a port is in use using socket"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_api_stats() -> Dict[str, Any]:
    """Get statistics about API usage if available"""
    try:
        api_stats = {}
        
        # Try to count job entries in the database
        try:
            from app.db.database import get_db
            from app.db.models import Job, ScraperRun, Role, job_roles
            from sqlalchemy import func
            
            db = next(get_db())
            
            # Count jobs
            total_jobs = db.query(Job).count()
            active_jobs = db.query(Job).filter(Job.is_active == True).count()
            inactive_jobs = db.query(Job).filter(Job.is_active == False).count()
            
            # Count companies
            companies = db.query(Job.company).distinct().count()
            
            # Count roles
            roles = db.query(Role).count()
            
            # Count recent scraper runs
            recent_runs = db.query(ScraperRun).order_by(ScraperRun.id.desc()).limit(100).all()
            
            success_runs = sum(1 for run in recent_runs if run.status == "success")
            failure_runs = sum(1 for run in recent_runs if run.status == "failure")
            
            # Calculate success rate
            if recent_runs:
                success_rate = (success_runs / len(recent_runs)) * 100
            else:
                success_rate = 0
                
            # Count jobs by posting date
            jobs_by_date = []
            dates_query = db.query(Job.date_posted, func.count(Job.id)).group_by(Job.date_posted).order_by(Job.date_posted.desc()).limit(7).all()
            
            for date, count in dates_query:
                jobs_by_date.append({
                    "date": date.strftime("%Y-%m-%d") if date else "Unknown",
                    "count": count
                })
                
            # Count jobs by role
            jobs_by_role = []
            try:
                roles_query = db.query(Role.name, func.count(job_roles.c.job_id)).join(
                    job_roles, Role.id == job_roles.c.role_id
                ).group_by(Role.name).order_by(func.count(job_roles.c.job_id).desc()).limit(10).all()
                
                for role, count in roles_query:
                    jobs_by_role.append({
                        "role": role,
                        "count": count
                    })
            except Exception as e:
                logger.error(f"Error getting jobs by role: {str(e)}")
                
            api_stats["database"] = {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "inactive_jobs": inactive_jobs,
                "companies": companies,
                "roles": roles,
                "recent_scraper_runs": len(recent_runs),
                "success_rate": round(success_rate, 2),
                "jobs_by_date": jobs_by_date,
                "jobs_by_role": jobs_by_role
            }
            
            db.close()
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            api_stats["database_error"] = str(e)
        
        return api_stats
    except Exception as e:
        logger.error(f"Error getting API stats: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    # When run directly, print system information
    info = get_system_info()
    print(format_system_info(info))
