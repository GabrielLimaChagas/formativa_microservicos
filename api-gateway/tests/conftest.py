import sys
import os

service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)
