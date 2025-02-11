import os
<<<<<<< HEAD

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FLOODNS_ROOT = os.path.join(PROJECT_ROOT, "floodns")
=======
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FLOODNS_ROOT = str(Path(PROJECT_ROOT, "floodns"))
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5

print("PROJECT_ROOT: ", PROJECT_ROOT)
print("FLOODNS_ROOT: ", FLOODNS_ROOT)
