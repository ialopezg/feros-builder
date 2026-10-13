"""Regression tests for device searching and presentation."""

import contextlib
from io import StringIO
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from device.management import search
from device.presentation import display


DEVICES = [
    {
        "id": "x55",
        "device": "PowKiddy X55",
        "soc": "RK3566",
        "repository": "official",
        "status": "Available",
        "update": "—",
    },
    {
        "id": "rgb30",
        "device": "PowKiddy RGB30",
        "soc": "RK3566",
        "repository": "community",
        "status": "Available",
        "update": "—",
    },
    {
        "id": "x55",
        "device": "PowKiddy X55",
        "soc": "RK3566",
        "repository": "community",
        "status": "Installed",
        "update": "No",
    },
]


class DeviceSearchTests(unittest.TestCase):
    def test_search_matches_device_name_case_insensitively(self):
        self.assertEqual(len(search(DEVICES, "powkiddy")), 3)
        self.assertEqual(len(search(DEVICES, "X55")), 2)

    def test_search_matches_device_id(self):
        self.assertEqual(len(search(DEVICES, "rgb30")), 1)

    def test_search_matches_soc(self):
        self.assertEqual(len(search(DEVICES, "rk3566")), 3)

    def test_search_matches_repository(self):
        self.assertEqual(len(search(DEVICES, "COMMUNITY")), 2)

    def test_search_preserves_repository_entries(self):
        matches = search(DEVICES, "x55")
        self.assertEqual([entry["repository"] for entry in matches],
                         ["official", "community"])

    def test_search_no_matches(self):
        self.assertEqual(search(DEVICES, "missing"), [])

    def test_search_rejects_empty_query(self):
        for query in ("", "  "):
            with self.subTest(query=query):
                with self.assertRaises(ValueError):
                    search(DEVICES, query)

    def test_search_does_not_modify_entries(self):
        snapshot = [dict(entry) for entry in DEVICES]
        search(DEVICES, "x55")
        self.assertEqual(DEVICES, snapshot)


class DevicePresentationTests(unittest.TestCase):
    @staticmethod
    def render(rows):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            display(rows)
        return output.getvalue()

    def test_empty_results_have_no_table_header(self):
        output = self.render([])
        self.assertIn("No device found", output)
        self.assertNotIn("Device Support", output)
        self.assertNotIn("STATUS", output)
        self.assertIn("builder help --device", output)

    def test_results_display_table(self):
        output = self.render(DEVICES)
        self.assertIn("Device Support", output)
        for heading in ("STATUS", "DEVICE", "SOC", "REPOSITORY", "UPDATE"):
            self.assertIn(heading, output)
        self.assertIn("PowKiddy X55", output)
        self.assertIn("PowKiddy RGB30", output)
        self.assertIn("community", output)
        self.assertNotIn("No device found", output)


if __name__ == "__main__":
    unittest.main()
