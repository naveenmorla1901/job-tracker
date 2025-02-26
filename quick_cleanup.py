"""
Quick cleanup script to remove test and integration files
"""
import os
import sys
import shutil

# Files to be removed
FILES_TO_REMOVE = [
    'test_scraper.py',
    'test_db_integration.py',
    'full_integration_test.py',
    'integration_test.py',
    'setup.py'
]

def quick_cleanup():
    """Remove test files and cleanup pycache"""
    print("\n===== QUICK PROJECT CLEANUP =====")
    
    # Remove test files
    for file in FILES_TO_REMOVE:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Removed: {file}")
            except Exception as e:
                print(f"Error removing {file}: {str(e)}")
    
    # Clean up __pycache__ directories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"Removed: {pycache_path}")
            except Exception as e:
                print(f"Error removing {pycache_path}: {str(e)}")
    
    print("\n===== CLEANUP COMPLETE =====")
    print("Test files and __pycache__ directories have been removed.")

if __name__ == "__main__":
    quick_cleanup()
