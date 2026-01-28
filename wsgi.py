import sys
import os

# Add your project directory to the path
project_home = '/home/YOUR_USERNAME/cocktails'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the data directory environment variable
os.environ['COCKTAILS_DATA_DIR'] = '/home/YOUR_USERNAME/cocktails/data'

from app import app as application
