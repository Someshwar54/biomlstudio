"""
BioMLStudio Backend Application

An AI-powered no-code platform for bioinformatics researchers.
Enables easy protein and DNA sequence analysis through machine learning.
"""

__version__ = "1.0.0"
__description__ = "AI-powered no-code platform for bioinformatics researchers"
__author__ = "BioMLStudio Team"
__email__ = "contact@biomlstudio.com"

import logging
import sys
from pathlib import Path

# Ensure the app directory is in the Python path
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log", mode="a"),
    ],
)

logger = logging.getLogger(__name__)
logger.info(f"BioMLStudio v{__version__} initialized")
