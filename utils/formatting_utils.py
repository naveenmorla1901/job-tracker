"""
Utility functions for formatting and displaying system information
"""

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
        if "folders_by_size" in info["project"]:
            formatted.append("  Folder Sizes:")
            for folder, size in info["project"]["folders_by_size"]:
                if folder != "root" and size > 0.1:  # Skip very small folders
                    formatted.append(f"    {folder}: {size} MB")
        
        # Subfolder sizes
        if "subfolders_by_size" in info["project"]:
            formatted.append("  Subfolder Sizes:")
            for folder, size in info["project"]["subfolders_by_size"]:
                if size > 0.1:  # Skip very small folders
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
