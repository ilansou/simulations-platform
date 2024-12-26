import os
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FLOODNS_ROOT = str(Path(PROJECT_ROOT, "floodns"))

print("PROJECT_ROOT: ", PROJECT_ROOT)
print("FLOODNS_ROOT: ", FLOODNS_ROOT)
