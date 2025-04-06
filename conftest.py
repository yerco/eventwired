import sys
import os
import warnings

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
warnings.simplefilter("error", UserWarning)
