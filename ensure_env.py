"""
Script to ensure proper environment setup for the job tracker application.
This checks for all required modules and directories.
"""
import os
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('job_tracker.env_check')

def check_module(module_name):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def check_directory(directory):
    """Check if a directory exists and create it if it doesn't"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {str(e)}")
            return False
    return True

def check_file(file_path, create_empty=False):
    """Check if a file exists and create an empty one if specified"""
    if not os.path.exists(file_path):
        if create_empty:
            try:
                with open(file_path, 'w') as f:
                    pass
                logger.info(f"Created empty file: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to create file {file_path}: {str(e)}")
                return False
        return False
    return True

def ensure_init_files():
    """Ensure all directories have __init__.py files"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Directories that need __init__.py files
    directories = [
        'dashboard_components',
        'system_metrics',
        'utils',
        'app',
        'app/dashboard',
        'app/api',
        'app/api/endpoints',
        'app/api/endpoints/auth',
        'app/db',
        'app/auth'
    ]
    
    for directory in directories:
        dir_path = os.path.join(project_dir, directory)
        if os.path.exists(dir_path):
            init_file = os.path.join(dir_path, '__init__.py')
            if not os.path.exists(init_file):
                try:
                    with open(init_file, 'w') as f:
                        f.write('"""Package initialization file"""')
                    logger.info(f"Created __init__.py in {directory}")
                except Exception as e:
                    logger.error(f"Failed to create __init__.py in {directory}: {str(e)}")

def update_pythonpath():
    """Update PYTHONPATH to include necessary directories"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add project directories to Python path
    sys.path.insert(0, project_dir)
    
    # Set environment variable for child processes
    os.environ['PYTHONPATH'] = project_dir + os.pathsep + os.environ.get('PYTHONPATH', '')
    
    logger.info(f"Updated PYTHONPATH to include: {project_dir}")

def check_environment():
    """
    Check the environment for everything needed by the job tracker application
    """
    logger.info("Checking job tracker environment...")
    
    # Project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Project directory: {project_dir}")
    
    # Check for required directories
    required_dirs = [
        'dashboard_components',
        'system_metrics',
        'utils',
        'app',
        'static',
        'logs'
    ]
    
    for directory in required_dirs:
        dir_path = os.path.join(project_dir, directory)
        if check_directory(dir_path):
            logger.info(f"Directory found: {directory}")
        else:
            logger.warning(f"Directory missing: {directory}")
    
    # Ensure all __init__.py files exist
    ensure_init_files()
    
    # Update PYTHONPATH
    update_pythonpath()
    
    # Check for required modules
    required_modules = [
        'streamlit',
        'pandas',
        'plotly',
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'psycopg2',
        'psutil',
        'requests'
    ]
    
    missing_modules = []
    for module in required_modules:
        if check_module(module):
            logger.info(f"Module found: {module}")
        else:
            logger.warning(f"Module missing: {module}")
            missing_modules.append(module)
    
    if missing_modules:
        logger.warning(f"Missing modules: {', '.join(missing_modules)}")
        logger.warning("Please install missing modules with: pip install " + " ".join(missing_modules))
    else:
        logger.info("All required modules installed")
    
    logger.info("Environment check completed.")
    return not missing_modules

if __name__ == "__main__":
    # When run directly, check the environment
    if check_environment():
        print("Environment check passed!")
    else:
        print("Environment check failed. Please fix issues above.")
        sys.exit(1)
