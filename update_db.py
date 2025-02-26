"""
Script to update database schema when model changes are made
"""
import os
import subprocess

def run_migration_update():
    """Run the necessary commands to update the database schema"""
    print("Starting database schema update...")
    
    try:
        # 1. Create a new migration
        print("\nCreating new migration...")
        migration_cmd = "alembic revision --autogenerate -m \"Increase job_id column length\""
        migration_result = subprocess.run(
            migration_cmd, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if migration_result.returncode != 0:
            print(f"Error creating migration: {migration_result.stderr}")
            return False
            
        print(migration_result.stdout)
        
        # 2. Apply the migration
        print("\nApplying migration...")
        upgrade_cmd = "alembic upgrade head"
        upgrade_result = subprocess.run(
            upgrade_cmd, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if upgrade_result.returncode != 0:
            print(f"Error applying migration: {upgrade_result.stderr}")
            return False
            
        print(upgrade_result.stdout)
        
        print("\nDatabase schema updated successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating database schema: {str(e)}")
        return False

if __name__ == "__main__":
    run_migration_update()
