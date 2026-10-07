"""Exercise the public CLI with an isolated user configuration."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ([os.environ["BUILDER"]] if os.environ.get("BUILDER")
           else [sys.executable, str(ROOT / "src/main.py")])


class BuilderCLI(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.env = dict(os.environ, HOME=str(self.root), USERPROFILE=str(self.root),
                        APPDATA=str(self.root / "AppData/Roaming"),
                        XDG_CONFIG_HOME=str(self.root / ".config"))
        if sys.platform == "win32":
            config = self.root / "AppData/Roaming/FeROS/Builder"
        elif sys.platform == "darwin":
            config = self.root / "Library/Application Support/FeROS/Builder"
        else:
            config = self.root / ".config/feros/builder"
        self.config = config / "repositories.toml"

    def run_cli(self, *args, success=True, input_text=""):
        result = subprocess.run(COMMAND + list(map(str, args)), cwd=self.root,
                                env=self.env, input=input_text, capture_output=True,
                                text=True, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_general_help_and_version(self):
        with (ROOT / "pyproject.toml").open("rb") as stream:
            version = tomllib.load(stream)["project"]["version"]
        for args in ((), ("help",), ("version",)):
            with self.subTest(args=args):
                output = self.run_cli(*args).stdout
                self.assertEqual(output.count("FeROS Builder v"), 1)
                self.assertIn(f"FeROS Builder v{version}", output)
                self.assertEqual(output.count("Build, validate binary images and manage device support."), 1)
                self.assertNotIn("Namespace(", output)
                if args != ("version",):
                    self.assertIn("Usage:", output)
                    self.assertIn("builder help --repository", output)
        self.assertFalse(self.config.exists())

    def test_command_help(self):
        topics = {"repository": ("--add", "--info", "--delete", "--update"),
                  "build": ("--device-name", "--firmware", "--output", "--validate"),
                  "validate": ("--image",), "update": ("builder update",)}
        for topic, expected in topics.items():
            with self.subTest(topic=topic):
                output = self.run_cli("help", "--" + topic).stdout
                self.assertIn("Usage:", output)
                self.assertNotIn("Namespace(", output)
                for text in expected:
                    self.assertIn(text, output)

    def test_first_list_initializes_once(self):
        output = self.run_cli("repository").stdout
        self.assertIn("FeROS Official Repository [official]", output)
        self.assertIn("builder help --repository", output)
        initial = self.config.read_bytes()
        config = tomllib.loads(initial.decode())
        self.assertEqual(config["schema_version"], "1.0")
        self.assertEqual(len(config["repositories"]), 1)
        self.assertEqual(config["repositories"][0]["id"], "feros-official")
        self.run_cli("repository")
        self.assertEqual(self.config.read_bytes(), initial)

    def test_list_reads_existing_configuration(self):
        self.run_cli("repository")
        with self.config.open("a", encoding="utf-8") as stream:
            stream.write('\n[[repositories]]\nid="custom"\nname="Custom source"\n'
                         'url="https://example.com/"\nofficial=false\n')
        before = self.config.read_bytes()
        output = self.run_cli("repository").stdout
        self.assertIn("Custom source [unofficial]", output)
        self.assertEqual(self.config.read_bytes(), before)

    def test_invalid_add_and_duplicate_preserve_configuration(self):
        self.run_cli("repository")
        before = self.config.read_bytes()
        cases = (("http://example.com\n\n", "HTTPS"),
                 ("https://user:password@example.com\n\n", "credentials"),
                 ("https://github.com/ialopezg/feros-targets\n\n", "already registered"))
        for text, error in cases:
            with self.subTest(error=error):
                result = self.run_cli("repository", "--add", input_text=text, success=False)
                self.assertIn(error, result.stderr)
                self.assertEqual(self.config.read_bytes(), before)

    def test_cancelled_add_does_not_create_configuration(self):
        output = self.run_cli("repository", "--add").stdout
        self.assertIn("cancelled", output)
        self.assertFalse(self.config.exists())

    def test_malformed_configuration_is_preserved(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_bytes(b"not valid TOML [")
        result = self.run_cli("repository", success=False)
        self.assertIn("error:", result.stderr)
        self.assertEqual(self.config.read_bytes(), b"not valid TOML [")

    def test_conflicting_operations_are_rejected(self):
        for args in (("repository", "--add", "--delete", "1"),
                     ("help", "--build", "--validate")):
            with self.subTest(args=args):
                self.assertIn("not allowed", self.run_cli(*args, success=False).stderr)
        self.assertFalse(self.config.exists())

    def test_pending_operations_never_report_success(self):
        image = self.root / "image.img"
        image.write_bytes(b"RKNS")
        output = self.root / "output.img"
        cases = [("build", "--device-name", "test", "--firmware", str(image),
                  "--output", str(output), "--validate"),
                 ("validate", "--image", str(image)), ("update",),
                 ("repository", "--info", "1"), ("repository", "--delete", "1"),
                 ("repository", "--update"), ("repository", "--update", "example.com")]
        for args in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args, success=False)
                self.assertIn("not implemented yet", result.stderr)
                self.assertEqual(image.read_bytes(), b"RKNS")
                self.assertFalse(output.exists())
                self.assertFalse(self.config.exists())
