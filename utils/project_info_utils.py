"""
Utility functions for project information and metrics
"""
import os
import subprocess
import datetime
import platform
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("job_tracker.utils.project_info")

def get_project_info() -> Dict[str, Any]:
    """Get information about the job-tracker project folder"""
    try:
        project_info = {}
        
        # Determine the project directory
        project_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        project_info["path"] = project_dir
        
        # Calculate directory size and structure
        folder_sizes = {}
        subfolder_sizes = {}  # Track subdirectories too
        total_size = 0
        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(project_dir):
            path_size = 0
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    file_size = os.path.getsize(fp)
                    path_size += file_size
                    total_size += file_size
                    file_count += 1
            
            # Add this directory's size to our structure
            rel_path = os.path.relpath(dirpath, project_dir)
            if rel_path == '.':
                rel_path = 'root'
                
            # Track all subdirectories for more detailed view
            parts = rel_path.split(os.sep)
            
            # Store first level directories
            if rel_path == 'root' or len(parts) == 1:
                folder_sizes[rel_path] = path_size
                
            # Store second level directories too
            if len(parts) == 2:
                parent = parts[0]
                subfolder_name = f"{parent}/{parts[1]}"
                subfolder_sizes[subfolder_name] = path_size
        
        project_info["size_bytes"] = total_size
        project_info["size_mb"] = round(total_size / (1024 * 1024), 2)
        project_info["size_gb"] = round(total_size / (1024 * 1024 * 1024), 3)
        project_info["file_count"] = file_count
        
        # Add folder size breakdown
        folder_sizes_mb = {}
        for folder, size in folder_sizes.items():
            folder_sizes_mb[folder] = round(size / (1024 * 1024), 2)
            
        # Add subfolder size breakdown
        subfolder_sizes_mb = {}
        for folder, size in subfolder_sizes.items():
            subfolder_sizes_mb[folder] = round(size / (1024 * 1024), 2)
            
        project_info["folder_sizes_mb"] = folder_sizes_mb
        project_info["subfolder_sizes_mb"] = subfolder_sizes_mb
        
        # Sort folders by size (descending)
        sorted_folders = sorted(folder_sizes_mb.items(), key=lambda x: x[1], reverse=True)
        project_info["folders_by_size"] = sorted_folders
        
        # Sort subfolders by size (descending)
        sorted_subfolders = sorted(subfolder_sizes_mb.items(), key=lambda x: x[1], reverse=True)
        project_info["subfolders_by_size"] = sorted_subfolders
        
        # Check logs size separately
        logs_dir = os.path.join(project_dir, "logs")
        logs_size = 0
        logs_count = 0
        log_files_info = {}
        
        if os.path.exists(logs_dir):
            for dirpath, dirnames, filenames in os.walk(logs_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        file_size = os.path.getsize(fp)
                        logs_size += file_size
                        logs_count += 1
                        
                        if f.endswith('.log'):
                            log_files_info[f] = {
                                "size_mb": round(file_size / (1024 * 1024), 2),
                                "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M:%S")
                            }
        
        project_info["logs_size_mb"] = round(logs_size / (1024 * 1024), 2)
        project_info["logs_count"] = logs_count
        project_info["log_files"] = log_files_info
        
        # Check individual log file sizes
        main_log_files = {}
        for log_file in ["job_tracker.log", "dashboard.log", "api.log"]:
            file_path = os.path.join(project_dir, log_file)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                main_log_files[log_file] = {
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "size_bytes": file_size,
                    "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                }
        
        project_info["main_log_files"] = main_log_files
        
        # Add Git and environment information
        project_info.update(_get_git_info(project_dir))
        project_info.update(_get_environment_info(project_dir))
        
        return project_info
    except Exception as e:
        logger.error(f"Error getting project info: {str(e)}")
        return {"error": str(e)}

def _get_git_info(project_dir):
    """Get Git repository information"""
    git_info = {}
    try:
        # Check Git information if available
        git_dir = os.path.join(project_dir, ".git")
        if os.path.exists(git_dir):
            git_info["git"] = {"has_git": True}
            
            try:
                # Get current branch
                head_file = os.path.join(git_dir, "HEAD")
                if os.path.exists(head_file):
                    with open(head_file, 'r') as f:
                        content = f.read().strip()
                        if content.startswith("ref: refs/heads/"):
                            git_info["git"]["current_branch"] = content.replace("ref: refs/heads/", "")
                
                # Count commits if possible
                try:
                    git_log = subprocess.check_output(
                        ["git", "-C", project_dir, "rev-list", "--count", "HEAD"],
                        stderr=subprocess.DEVNULL
                    ).decode().strip()
                    git_info["git"]["commit_count"] = int(git_log)
                except:
                    pass
                
                # Get last commit info
                try:
                    last_commit = subprocess.check_output(
                        ["git", "-C", project_dir, "log", "-1", "--pretty=format:%h|%an|%ad|%s"],
                        stderr=subprocess.DEVNULL
                    ).decode().strip()
                    
                    if last_commit:
                        parts = last_commit.split('|')
                        if len(parts) >= 4:
                            git_info["git"]["last_commit"] = {
                                "hash": parts[0],
                                "author": parts[1],
                                "date": parts[2],
                                "message": parts[3]
                            }
                except:
                    pass
            except Exception as e:
                logger.error(f"Error getting git info details: {str(e)}")
                pass
    except Exception as e:
        logger.error(f"Error getting git info: {str(e)}")
    
    return git_info

def _get_environment_info(project_dir):
    """Get virtual environment and database information"""
    env_info = {}
    
    try:
        # Get information about virtual environment
        venv_info = {}
        venv_dir = os.path.join(project_dir, "venv")
        if os.path.exists(venv_dir):
            venv_info["exists"] = True
            
            # Calculate venv size
            venv_size = 0
            venv_file_count = 0
            for dirpath, dirnames, filenames in os.walk(venv_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        venv_size += os.path.getsize(fp)
                        venv_file_count += 1
            
            venv_info["size_mb"] = round(venv_size / (1024 * 1024), 2)
            venv_info["file_count"] = venv_file_count
            
            # Try to get Python version used by venv
            python_path = None
            if platform.system() == "Windows":
                python_path = os.path.join(venv_dir, "Scripts", "python.exe")
            else:
                python_path = os.path.join(venv_dir, "bin", "python")
                
            if python_path and os.path.exists(python_path):
                try:
                    version_output = subprocess.check_output(
                        [python_path, "--version"], 
                        stderr=subprocess.STDOUT
                    ).decode().strip()
                    
                    if version_output.startswith("Python "):
                        venv_info["python_version"] = version_output.replace("Python ", "")
                except:
                    pass
        else:
            venv_info["exists"] = False
            
        env_info["venv"] = venv_info
        
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
                    
            # Check for PostgreSQL database
            db_url_file = os.path.join(project_dir, ".env")
            if os.path.exists(db_url_file):
                with open(db_url_file, 'r') as f:
                    for line in f:
                        if line.startswith("DATABASE_URL="):
                            db_info["has_database_url"] = True
                            db_type = "unknown"
                            if "postgresql://" in line:
                                db_type = "postgresql"
                            elif "sqlite://" in line:
                                db_type = "sqlite"
                            db_info["type"] = db_type
                            break
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            
        env_info["database"] = db_info
    except Exception as e:
        logger.error(f"Error getting environment info: {str(e)}")
    
    return env_info
