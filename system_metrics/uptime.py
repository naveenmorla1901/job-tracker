"""
Uptime metrics collection for job tracker
"""
import datetime
import psutil
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("job_tracker.system_metrics.uptime")

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
