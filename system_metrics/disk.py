"""
Disk metrics collection for job tracker
"""
import os
import psutil
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("job_tracker.system_metrics.disk")

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
