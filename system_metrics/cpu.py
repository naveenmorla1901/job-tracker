"""
CPU metrics collection for job tracker
"""
import platform
import subprocess
import psutil
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("job_tracker.system_metrics.cpu")

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
        
        # Get CPU model information based on platform
        cpu_info.update(_get_cpu_model_info())
                
        return cpu_info
    except Exception as e:
        logger.error(f"Error getting CPU info: {str(e)}")
        return {"error": str(e)}

def _get_cpu_model_info() -> Dict[str, Any]:
    """Get CPU model information based on platform"""
    cpu_model_info = {}
    
    try:
        if platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            cpu_model_info["model"] = line.split(":")[1].strip()
                            break
            except Exception as e:
                logger.error(f"Error reading /proc/cpuinfo: {str(e)}")
                
        elif platform.system() == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                cpu_model_info["model"] = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                winreg.CloseKey(key)
            except Exception as e:
                logger.error(f"Error reading Windows registry: {str(e)}")
                
        elif platform.system() == "Darwin":  # macOS
            try:
                output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode("utf-8").strip()
                cpu_model_info["model"] = output
            except Exception as e:
                logger.error(f"Error reading macOS CPU info: {str(e)}")
    except Exception as e:
        logger.error(f"Error determining CPU model: {str(e)}")
        
    return cpu_model_info
