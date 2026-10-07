"""Test repository persistence and classification without external services."""

from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from repository import management
import cli


class Repositories(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "config/repositories.toml"
        location = patch.object(management, "configuration_path", return_value=self.path)
        location.start()
        self.addCleanup(location.stop)
        opener = patch.object(management, "build_opener")
        self.opener = opener.start()
        self.addCleanup(opener.stop)
        self.opener.return_value.open.side_effect = AssertionError("Unexpected registry request")

    def registry(self, content):
        self.opener.return_value.open.side_effect = None
        self.opener.return_value.open.return_value = BytesIO(content)

    def test_add_defaults_to_domain_and_persists(self):
        self.registry(b'schema_version=1\nrepositories=[]\n')
        entry = management.add("https://EXAMPLE.com:443")
        self.assertEqual(entry["name"], "example.com")
        self.assertEqual(entry["url"], "https://example.com/")
        self.assertFalse(entry["official"])
        self.assertEqual(management.available()[1], entry)
        for field in ("created_at", "updated_at"):
            timestamp = datetime.fromisoformat(entry[field].replace("Z", "+00:00"))
            self.assertEqual(timestamp.utcoffset().total_seconds(), 0)

    def test_interactive_add_passes_optional_name(self):
        self.registry(b'schema_version=1\nrepositories=[]\n')
        with patch("builtins.input", side_effect=["https://example.com", ""]), \
                patch("sys.stdout", new_callable=StringIO) as output:
            cli.repository_add()
        self.assertIn("Repository added: example.com [unofficial]", output.getvalue())
        self.assertEqual(management.available()[1]["name"], "example.com")

    def test_official_membership_uses_url_not_name(self):
        self.registry(b'schema_version=1\n[[repositories]]\nurl="https://example.com/devices"\n')
        entry = management.add("https://example.com/devices", 'Name "with quotes"')
        self.assertTrue(entry["official"])
        self.assertEqual(management.available()[1]["name"], 'Name "with quotes"')

    def test_duplicate_and_invalid_urls_do_not_request_registry(self):
        management.available()
        before = self.path.read_bytes()
        for url, name in (("https://github.com/ialopezg/feros-targets", None),
                          ("https://example.com", "FEROS OFFICIAL REPOSITORY"),
                          ("http://example.com", None),
                          ("https://user:secret@example.com", None)):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    management.add(url, name)
                self.assertEqual(self.path.read_bytes(), before)
        self.opener.assert_not_called()

    def test_failed_registry_lookup_preserves_configuration(self):
        management.available()
        before = self.path.read_bytes()
        self.opener.return_value.open.side_effect = URLError("offline")
        with self.assertRaises(URLError):
            management.add("https://example.com")
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_registry_preserves_configuration(self):
        management.available()
        before = self.path.read_bytes()
        for content in (b"bad TOML [", b"schema_version=2\nrepositories=[]",
                        b"schema_version=1\nrepositories=[{}]"):
            with self.subTest(content=content):
                self.registry(content)
                with self.assertRaises(ValueError):
                    management.add("https://example.com")
                self.assertEqual(self.path.read_bytes(), before)

    def test_failed_atomic_replace_preserves_configuration(self):
        management.available()
        before = self.path.read_bytes()
        self.registry(b'schema_version=1\nrepositories=[]\n')
        with patch.object(management.os, "replace", side_effect=OSError("cannot replace")):
            with self.assertRaisesRegex(OSError, "cannot replace"):
                management.add("https://example.com")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])
