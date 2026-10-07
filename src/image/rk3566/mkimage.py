#!/usr/bin/env python3

"""Build and validate minimal Rockchip RK3566 RKNS boot images for FeROS."""

import hashlib
import struct


# Size, in bytes, of one sector used by the Rockchip boot format.
SECTOR_SIZE = 512

# Rockchip new-IDB payloads are aligned to 2048-byte pages.
PAGE_SIZE = 2048

# Physical byte offset where the RKNS structure is placed on boot media.
RKNS_OFFSET = 64 * SECTOR_SIZE

# Total size, in bytes, occupied by the RKNS header.
RKNS_HEADER_SIZE = 4 * SECTOR_SIZE

# Number of bytes covered by the RKNS header SHA-256 digest.
#
# The physical PowKiddy X55 boot image confirms that all first three
# sectors of the RKNS header participate in the digest.
RKNS_HASH_DATA_SIZE = 3 * SECTOR_SIZE

# Offset inside the RKNS header where its SHA-256 digest is stored.
RKNS_HASH_OFFSET = RKNS_HASH_DATA_SIZE

# Size, in bytes, of an SHA-256 digest.
SHA256_SIZE = 32

# Expected RKNS structure signature.
RKNS_MAGIC = b"RKNS"

# RKNS flag selecting SHA-256 hashing.
RKNS_SHA256_FLAG = 1

# Offset of the RKNS flags field.
RKNS_FLAGS_OFFSET = 0x0C

# Control value representing the two-payload layout used by this image.
RKNS_CONTROL = 0x00020180

# Offset of the RKNS control field.
RKNS_CONTROL_OFFSET = 0x08

# Offset inside the RKNS header where the first payload descriptor begins.
DESCRIPTOR_1_OFFSET = 0x78

# Offset inside the RKNS header where the second payload descriptor begins.
DESCRIPTOR_2_OFFSET = 0xD0

# Constant value stored in the second word of each payload descriptor.
DESCRIPTOR_MARKER = 0xFFFFFFFF

# Offset of the descriptor marker.
DESCRIPTOR_MARKER_OFFSET = 0x04

# Offset of the payload image number inside each descriptor.
DESCRIPTOR_IMAGE_NUMBER_OFFSET = 0x0C

# Offset inside each payload descriptor where its SHA-256 digest is stored.
PAYLOAD_HASH_OFFSET = 0x18

# First payload sector relative to the beginning of the RKNS structure.
FIRST_PAYLOAD_SECTOR = 4

# Number of sectors reserved by the known-working X55 RKNS image for its
# second-stage payload. The BootROM contract uses the complete reserved area,
# even when the FeROS Stage 0 binary occupies only its first bytes.
STAGE0_PAYLOAD_SECTORS = 472

# Maximum FeROS Stage 0 size accepted by the X55 RKNS payload descriptor.
STAGE0_PAYLOAD_CAPACITY = STAGE0_PAYLOAD_SECTORS * SECTOR_SIZE

# Maximum value representable by each 16-bit descriptor component.
DESCRIPTOR_FIELD_MAX = 0xFFFF


def align(value: int, alignment: int) -> int:
    """Round a byte count upward to the requested alignment boundary."""
    return (value + alignment - 1) // alignment * alignment


def pad_payload(data: bytes) -> bytes:
    """Pad a payload to the Rockchip new-IDB 2048-byte page boundary."""
    padded_size = align(len(data), PAGE_SIZE)

    return data.ljust(padded_size, b"\0")


def pad_stage0_payload(data: bytes) -> bytes:
    """Pad FeROS Stage 0 to the X55 RKNS second-payload capacity."""
    if len(data) > STAGE0_PAYLOAD_CAPACITY:
        raise ValueError(
            "Stage 0 exceeds the X55 RKNS payload capacity: "
            f"{len(data)} > {STAGE0_PAYLOAD_CAPACITY} bytes"
        )

    return data.ljust(STAGE0_PAYLOAD_CAPACITY, b"\0")


def sha256(data: bytes) -> bytes:
    """Calculate and return the binary SHA-256 digest of a byte sequence."""
    return hashlib.sha256(data).digest()


def encode_descriptor(
        header: bytearray,
        descriptor_offset: int,
        payload_sector: int,
        payload: bytes,
        image_number: int,
) -> None:
    """Encode one RKNS payload descriptor and its SHA-256 digest."""

    # RKNS expresses payload sizes in 512-byte sectors even though payload
    # storage itself is aligned to 2048-byte Rockchip pages.
    payload_sector_count = len(payload) // SECTOR_SIZE

    if payload_sector > DESCRIPTOR_FIELD_MAX:
        raise ValueError("RKNS payload offset exceeds descriptor limits")

    if payload_sector_count > DESCRIPTOR_FIELD_MAX:
        raise ValueError("RKNS payload size exceeds descriptor limits")

    # The lower 16 bits contain the starting sector and the upper 16 bits
    # contain the number of sectors occupied by the payload.
    descriptor_word = (
                              payload_sector_count << 16
                      ) | payload_sector

    struct.pack_into(
        "<I",
        header,
        descriptor_offset,
        descriptor_word,
    )

    # This value is present in the known-working X55 RKNS descriptors and
    # matches the Rockchip new-IDB structure used by public implementations.
    struct.pack_into(
        "<I",
        header,
        descriptor_offset + DESCRIPTOR_MARKER_OFFSET,
        DESCRIPTOR_MARKER,
        )

    # Payload descriptors are numbered sequentially beginning with one.
    struct.pack_into(
        "<I",
        header,
        descriptor_offset + DESCRIPTOR_IMAGE_NUMBER_OFFSET,
        image_number,
        )

    payload_digest = sha256(payload)

    digest_offset = descriptor_offset + PAYLOAD_HASH_OFFSET

    header[
        digest_offset:
        digest_offset + SHA256_SIZE
    ] = payload_digest


def decode_descriptor(
        header: bytes,
        descriptor_offset: int,
) -> tuple[int, int, int, int, bytes]:
    """Decode one RKNS payload descriptor from an existing header."""

    descriptor_word = struct.unpack_from(
        "<I",
        header,
        descriptor_offset,
    )[0]

    payload_sector = descriptor_word & 0xFFFF
    payload_sector_count = descriptor_word >> 16

    marker = struct.unpack_from(
        "<I",
        header,
        descriptor_offset + DESCRIPTOR_MARKER_OFFSET,
        )[0]

    image_number = struct.unpack_from(
        "<I",
        header,
        descriptor_offset + DESCRIPTOR_IMAGE_NUMBER_OFFSET,
        )[0]

    digest_offset = descriptor_offset + PAYLOAD_HASH_OFFSET

    payload_digest = header[
        digest_offset:
        digest_offset + SHA256_SIZE
    ]

    return (
        payload_sector,
        payload_sector_count,
        marker,
        image_number,
        payload_digest,
    )


def build_image(ddr_payload: bytes, stage0_payload: bytes) -> bytes:
    """Build an RKNS image containing DDR initialization and FeROS Stage 0."""

    if not ddr_payload or not stage0_payload:
        raise ValueError("DDR and Stage 0 payloads must be non-empty")

    padded_ddr = pad_payload(ddr_payload)
    padded_stage0 = pad_stage0_payload(stage0_payload)

    # The first payload begins immediately after the four-sector RKNS header.
    ddr_sector = FIRST_PAYLOAD_SECTOR

    # The second payload begins after the page-aligned DDR payload.
    stage0_sector = (
            ddr_sector
            + len(padded_ddr) // SECTOR_SIZE
    )

    header = bytearray(RKNS_HEADER_SIZE)

    header[0:4] = RKNS_MAGIC

    # The word at +0x04 remains zero. The physical X55 image confirms that
    # the SHA-256 flag belongs at +0x0C rather than +0x04.
    struct.pack_into(
        "<I",
        header,
        RKNS_CONTROL_OFFSET,
        RKNS_CONTROL,
    )

    struct.pack_into(
        "<I",
        header,
        RKNS_FLAGS_OFFSET,
        RKNS_SHA256_FLAG,
    )

    encode_descriptor(
        header=header,
        descriptor_offset=DESCRIPTOR_1_OFFSET,
        payload_sector=ddr_sector,
        payload=padded_ddr,
        image_number=1,
    )

    encode_descriptor(
        header=header,
        descriptor_offset=DESCRIPTOR_2_OFFSET,
        payload_sector=stage0_sector,
        payload=padded_stage0,
        image_number=2,
    )

    # Authenticate the first three complete RKNS header sectors.
    header_digest = sha256(
        header[:RKNS_HASH_DATA_SIZE]
    )

    header[
        RKNS_HASH_OFFSET:
        RKNS_HASH_OFFSET + SHA256_SIZE
    ] = header_digest

    image_size = (
            RKNS_OFFSET
            + stage0_sector * SECTOR_SIZE
            + len(padded_stage0)
    )

    image = bytearray(image_size)

    image[
        RKNS_OFFSET:
        RKNS_OFFSET + RKNS_HEADER_SIZE
    ] = header

    ddr_offset = (
            RKNS_OFFSET
            + ddr_sector * SECTOR_SIZE
    )

    image[
        ddr_offset:
        ddr_offset + len(padded_ddr)
    ] = padded_ddr

    stage0_offset = (
            RKNS_OFFSET
            + stage0_sector * SECTOR_SIZE
    )

    image[
        stage0_offset:
        stage0_offset + len(padded_stage0)
    ] = padded_stage0

    return bytes(image)


def validate_payload(
        image: bytes,
        header: bytes,
        descriptor_offset: int,
        payload_name: str,
        expected_image_number: int,
) -> None:
    """Validate one RKNS payload descriptor, bounds, and SHA-256 digest."""

    (
        payload_sector,
        payload_sector_count,
        marker,
        image_number,
        expected_digest,
    ) = decode_descriptor(
        header=header,
        descriptor_offset=descriptor_offset,
    )

    if payload_sector_count == 0:
        raise ValueError(f"{payload_name} payload has zero sectors")

    if marker != DESCRIPTOR_MARKER:
        raise ValueError(
            f"{payload_name} descriptor marker is invalid: "
            f"0x{marker:08x}"
        )

    if image_number != expected_image_number:
        raise ValueError(
            f"{payload_name} descriptor image number is invalid: "
            f"{image_number}"
        )

    payload_offset = (
            RKNS_OFFSET
            + payload_sector * SECTOR_SIZE
    )

    payload_size = payload_sector_count * SECTOR_SIZE
    payload_end = payload_offset + payload_size

    if payload_end > len(image):
        raise ValueError(
            f"{payload_name} payload exceeds image bounds"
        )

    payload = image[payload_offset:payload_end]
    actual_digest = sha256(payload)

    if actual_digest != expected_digest:
        raise ValueError(
            f"{payload_name} payload SHA-256 mismatch"
        )

    print(
        f"{payload_name}: "
        f"image={image_number} "
        f"sector={payload_sector} "
        f"sectors={payload_sector_count} "
        f"offset=0x{payload_offset:x} "
        f"SHA-256 OK"
    )


def validate_image(image: bytes) -> None:
    """Validate the structure and cryptographic integrity of an RKNS image."""

    minimum_image_size = RKNS_OFFSET + RKNS_HEADER_SIZE

    if len(image) < minimum_image_size:
        raise ValueError("Image is too small to contain an RKNS header")

    header = image[
        RKNS_OFFSET:
        RKNS_OFFSET + RKNS_HEADER_SIZE
    ]

    if header[0:4] != RKNS_MAGIC:
        raise ValueError("Invalid RKNS signature")

    control = struct.unpack_from(
        "<I",
        header,
        RKNS_CONTROL_OFFSET,
    )[0]

    if control != RKNS_CONTROL:
        raise ValueError(
            f"Unexpected RKNS control value: 0x{control:08x}"
        )

    hash_flag = struct.unpack_from(
        "<I",
        header,
        RKNS_FLAGS_OFFSET,
    )[0]

    if hash_flag != RKNS_SHA256_FLAG:
        raise ValueError(
            f"Unsupported RKNS hash flag: 0x{hash_flag:08x}"
        )

    expected_header_digest = header[
        RKNS_HASH_OFFSET:
        RKNS_HASH_OFFSET + SHA256_SIZE
    ]

    actual_header_digest = sha256(
        header[:RKNS_HASH_DATA_SIZE]
    )

    if actual_header_digest != expected_header_digest:
        raise ValueError("RKNS header SHA-256 mismatch")

    print("RKNS header: SHA-256 OK")

    validate_payload(
        image=image,
        header=header,
        descriptor_offset=DESCRIPTOR_1_OFFSET,
        payload_name="DDR",
        expected_image_number=1,
    )

    validate_payload(
        image=image,
        header=header,
        descriptor_offset=DESCRIPTOR_2_OFFSET,
        payload_name="Stage 0",
        expected_image_number=2,
    )

    print("RKNS image: VALID")
