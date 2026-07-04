from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    root = Path(os.getenv("DATA_ROOT", "/data"))
    state_dir = root / os.getenv("STATE_SUBDIR", "state")
    heartbeat = state_dir / "heartbeat.json"
    max_age = float(os.getenv("HEALTHCHECK_MAX_AGE_SECONDS", "60"))

    try:
        age = time.time() - heartbeat.stat().st_mtime
        payload = json.loads(heartbeat.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 1

    if payload.get("status") != "running" or age > max_age:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
