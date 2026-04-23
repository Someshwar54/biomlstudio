import os
import sys
from alembic.config import Config
from alembic import command

def main():
    # Set up the Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Set the Python path to include the current directory
    sys.path.insert(0, os.getcwd())
    
    # Run the autogenerate command
    print("Running alembic revision --autogenerate...")
    command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
    
    # Run the upgrade command
    print("Running alembic upgrade head...")
    command.upgrade(alembic_cfg, "head")
    
    print("Database migration completed successfully!")

if __name__ == "__main__":
    main()
