"""Exercise source and packaged CLIs without firmware or physical devices."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ([os.environ["BUILDER"]] if os.environ.get("BUILDER")
           else [sys.executable, str(ROOT / "src/main.py")])


class ImageCLI(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.ddr = self.root / "test ddr.bin"
        self.stage = self.root / "test stage.bin"
        self.output = self.root / "output image.img"
        self.ddr.write_bytes(bytes(range(256)) * 9)
        self.stage.write_bytes(b"synthetic stage zero")

    def run_cli(self, *args, success=True):
        result = subprocess.run(COMMAND + list(map(str, args)), cwd=self.root,
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def build(self, success=True):
        return self.run_cli("build", "--ddr", self.ddr, "--stage0", self.stage,
                            "--output", self.output, success=success)

    def test_help(self):
        self.assertIn("builder", self.run_cli("--help").stdout)
        self.run_cli("build", "--help")
        self.run_cli("validate", "--help")

    def test_build_validate_and_determinism(self):
        self.build()
        first = self.output.read_bytes()
        self.assertEqual(first[0x8000:0x8004], b"RKNS")
        self.assertIn("RKNS image: VALID",
                      self.run_cli("validate", "--image", self.output).stdout)
        self.build()
        self.assertEqual(first, self.output.read_bytes())

    def test_corrupted_payload_is_rejected(self):
        self.build()
        image = bytearray(self.output.read_bytes())
        image[0x8800] ^= 1
        self.output.write_bytes(image)
        result = self.run_cli("validate", "--image", self.output, success=False)
        self.assertIn("SHA-256 mismatch", result.stderr)

    def test_truncated_image_is_rejected(self):
        self.output.write_bytes(b"RKNS")
        self.run_cli("validate", "--image", self.output, success=False)

    def test_empty_input_is_rejected(self):
        self.ddr.write_bytes(b"")
        self.build(success=False)
        self.assertFalse(self.output.exists())

    def test_oversized_stage_is_rejected(self):
        self.stage.write_bytes(b"x" * (472 * 512 + 1))
        self.build(success=False)
        self.assertFalse(self.output.exists())

    def test_missing_input_is_rejected(self):
        self.ddr.unlink()
        self.build(success=False)
        self.assertFalse(self.output.exists())
