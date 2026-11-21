#!/usr/bin/env python3
"""Run the shared `scripts/sync_ready_status.py` (switch items between ready and ready-but-blocked); same arguments.

SKILL.md points here rather than at `<skill-base-dir>/../../scripts/`: the
skill is installed as a symlink, and an agent that normalizes that path
lexically lands outside this repository. This file finds the shared script
from its own real location instead.
"""

import runpy
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SHARED))
runpy.run_path(str(SHARED / "sync_ready_status.py"), run_name="__main__")
