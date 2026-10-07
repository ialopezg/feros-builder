"""Run source regressions or isolated executable CLI checks."""

import os
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[1]
# A frozen executable is checked through its public CLI, not source imports.
if os.environ.get("BUILDER"):
    pattern = "test_cli.py"
    print("Checking executable CLI", flush=True)
else:
    sys.path.insert(0, str(root / "src"))
    pattern = "test_*.py"
    print("Checking source CLI, repositories, and image engine", flush=True)
suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern=pattern)
if suite.countTestCases() == 0:
    raise SystemExit("No tests discovered; refusing to accept an empty test run")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
