import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(r"C:\Users\PMLS\Documents\IDE Remote")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.antigravity_companion.permissions import cleanup_single_use
    cleanup_single_use()
except Exception:
    pass

print(json.dumps({}))
