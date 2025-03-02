"""
Memory metrics collection for job tracker
"""
import psutil
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("job_tracker.system_metrics.memory")

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
