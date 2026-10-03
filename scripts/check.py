"""Run the regression suite and fail if no tests were discovered."""

from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[1]
suite = unittest.defaultTestLoader.discover(str(root / "tests"))
if suite.countTestCases() == 0:
    raise SystemExit("No tests discovered; refusing to accept an empty test run")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
