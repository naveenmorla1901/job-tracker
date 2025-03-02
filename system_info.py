"""
System information utilities for job tracker
"""
import platform
import datetime
import logging
from typing import Dict, Any

# Import system metrics modules
from system_metrics import (
    get_memory_info, 
    get_disk_info, 
    get_cpu_info, 
    get_uptime_info, 
    get_network_info
)

# Import API stats
from api_stats import get_api_stats

# Import utility functions
from utils.project_info_utils import get_project_info
from utils.process_info_utils import get_process_info
from utils.formatting_utils import format_system_info

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

if __name__ == "__main__":
    # When run directly, print system information
    info = get_system_info()
    print(format_system_info(info))
