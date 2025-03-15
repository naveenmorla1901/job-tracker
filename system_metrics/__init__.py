"""
System metrics collection package for job tracker
"""
import os
import sys

# Fix for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try imports with error handling
try:
    from system_metrics.memory import get_memory_info
except ImportError:
    # Fallback function if import fails
    def get_memory_info():
        return {"error": "Module not available", "total": 0, "available": 0, "percent": 0}

try:
    from system_metrics.disk import get_disk_info
except ImportError:
    def get_disk_info():
        return {"error": "Module not available", "total": 0, "used": 0, "free": 0, "percent": 0}

try:
    from system_metrics.cpu import get_cpu_info
except ImportError:
    def get_cpu_info():
        return {"error": "Module not available", "percent": 0, "count": 0}

try:
    from system_metrics.uptime import get_uptime_info
except ImportError:
    def get_uptime_info():
        return {"error": "Module not available", "uptime_seconds": 0, "uptime_str": "Unknown"}

try:
    from system_metrics.network import get_network_info, is_port_in_use
except ImportError:
    def get_network_info():
        return {"error": "Module not available"}
    
    def is_port_in_use(port):
        return False

__all__ = [
    'get_memory_info',
    'get_disk_info',
    'get_cpu_info',
    'get_uptime_info',
    'get_network_info',
    'is_port_in_use'
]
