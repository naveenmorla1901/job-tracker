"""
Network metrics collection for job tracker
"""
import socket
import psutil
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger("job_tracker.system_metrics.network")

def get_network_info() -> Dict[str, Any]:
    """Get network usage information"""
    try:
        network_info = {}
        
        # Get network interfaces and addresses
        network_info["interfaces"] = _get_network_interfaces()
        
        # Get network I/O statistics
        network_info["io"] = _get_network_io_stats()
        
        # Get connection information
        connection_info = _get_connection_info()
        network_info.update(connection_info)
        
        # Check service ports
        network_info["api_port_active"] = is_port_in_use(8000)
        network_info["dashboard_port_active"] = is_port_in_use(8501)
        network_info["nginx_active"] = is_port_in_use(80) or is_port_in_use(443)
        
        # Get running services
        network_info["services"] = _get_running_services()
        
        return network_info
    except Exception as e:
        logger.error(f"Error getting network info: {str(e)}")
        return {"error": str(e)}

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use using socket"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def _get_network_interfaces() -> List[Dict[str, Any]]:
    """Get information about network interfaces"""
    interfaces = []
    
    try:
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
                interfaces.append(interface)
    except Exception as e:
        logger.error(f"Error getting network interfaces: {str(e)}")
    
    return interfaces

def _get_network_io_stats() -> Dict[str, Any]:
    """Get network I/O statistics"""
    io_stats = {}
    
    try:
        io_counters = psutil.net_io_counters(pernic=True)
        if io_counters:
            for nic, counters in io_counters.items():
                io_stats[nic] = {
                    "bytes_sent_mb": counters.bytes_sent // (1024 * 1024),
                    "bytes_recv_mb": counters.bytes_recv // (1024 * 1024),
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                    "errin": counters.errin,
                    "errout": counters.errout,
                    "dropin": counters.dropin,
                    "dropout": counters.dropout
                }
    except Exception as e:
        logger.error(f"Error getting network I/O stats: {str(e)}")
    
    return io_stats

def _get_connection_info() -> Dict[str, Any]:
    """Get network connection information"""
    connection_info = {"connections": {}}
    
    try:
        # Count by connection status
        connections = psutil.net_connections()
        by_status = {}
        
        for conn in connections:
            status = conn.status
            if status not in by_status:
                by_status[status] = 0
            by_status[status] += 1
        
        connection_info["connections"]["by_status"] = by_status
        connection_info["connections"]["total"] = len(connections)
        connection_info["active_connections"] = by_status.get("ESTABLISHED", 0)
    except Exception as e:
        # Needs elevated privileges on some systems
        connection_info["connections"]["error"] = f"Insufficient privileges to get connection information: {str(e)}"
    
    return connection_info

def _get_running_services() -> List[Dict[str, Any]]:
    """Get running services related to the application"""
    services = []
    
    try:
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
    except Exception as e:
        logger.error(f"Error getting running services: {str(e)}")
    
    return services
