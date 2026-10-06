from pathlib import Path
import sys

# Keep tests runnable from /mnt/gai, /mnt/gai/agent, or an IDE.
AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))
