import sys
from pathlib import Path
# Prepend this section's directory so 'import schema' finds the local schema.py,
# not a previously cached one from another section.
sys.path.insert(0, str(Path(__file__).parent))
for mod in ["schema", "data"]:
    sys.modules.pop(mod, None)
