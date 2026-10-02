"""CLI entry point: `uv run python scripts/collect_data.py`"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cs703.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, SOCRATA_APP_TOKEN
from cs703.data.collect import run_collection

if __name__ == "__main__":
    manifest = run_collection(DATA_RAW_DIR, DATA_PROCESSED_DIR, app_token=SOCRATA_APP_TOKEN)
    print(json.dumps(manifest, indent=2))
