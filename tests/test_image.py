"""Check the image engine independently of unfinished CLI integration."""

from contextlib import redirect_stdout
from io import StringIO
import unittest

from image.rk3566 import mkimage


class ImageEngine(unittest.TestCase):
    def setUp(self):
        self.ddr = bytes(range(256)) * 9
        self.stage = b"synthetic stage zero"
        self.output = StringIO()
        redirect = redirect_stdout(self.output)
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)

    def test_build_validate_and_determinism(self):
        image = mkimage.build_image(self.ddr, self.stage)
        self.assertEqual(image[0x8000:0x8004], b"RKNS")
        mkimage.validate_image(image)
        self.assertIn("RKNS image: VALID", self.output.getvalue())
        self.assertEqual(image, mkimage.build_image(self.ddr, self.stage))

    def test_corrupted_payloads_are_rejected(self):
        original = mkimage.build_image(self.ddr, self.stage)
        for offset in (0x8800, 0x9800):
            with self.subTest(offset=offset):
                image = bytearray(original)
                image[offset] ^= 1
                with self.assertRaisesRegex(ValueError, "payload SHA-256 mismatch"):
                    mkimage.validate_image(bytes(image))

    def test_corrupted_header_is_rejected(self):
        image = bytearray(mkimage.build_image(self.ddr, self.stage))
        image[0x8010] ^= 1
        with self.assertRaisesRegex(ValueError, "header SHA-256 mismatch"):
            mkimage.validate_image(bytes(image))

    def test_truncated_image_is_rejected(self):
        image = mkimage.build_image(self.ddr, self.stage)
        for truncated in (b"RKNS", image[:-1]):
            with self.subTest(size=len(truncated)):
                with self.assertRaises(ValueError):
                    mkimage.validate_image(truncated)

    def test_empty_payloads_are_rejected(self):
        for ddr, stage in ((b"", self.stage), (self.ddr, b"")):
            with self.subTest(ddr_size=len(ddr), stage_size=len(stage)):
                with self.assertRaisesRegex(ValueError, "non-empty"):
                    mkimage.build_image(ddr, stage)

    def test_stage_capacity_boundary(self):
        maximum = b"x" * mkimage.STAGE0_PAYLOAD_CAPACITY
        mkimage.validate_image(mkimage.build_image(self.ddr, maximum))
        with self.assertRaisesRegex(ValueError, "exceeds.*capacity"):
            mkimage.build_image(self.ddr, maximum + b"x")
