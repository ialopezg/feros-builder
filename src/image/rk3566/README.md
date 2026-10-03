# RK3566 Boot Image Tool

`mkimage.py` builds and validates Rockchip RK3566 RKNS boot images used
by FeROS targets based on this SoC.

The tool exists to keep binary-format knowledge out of the Makefile and
to make the RKNS construction process explicit, reproducible, and
independently verifiable.

## Location

``` text
tools/image/rk3566/
├── mkimage.py
└── README.md
```

The current RK3566 DDR initialization firmware is maintained separately
as an explicit SoC dependency:

``` text
soc/rockchip/rk3566/firmware/ddr.bin
```

Forensic captures under `research/` are evidence and are not normal
build inputs.

## Purpose

The RK3566 BootROM expects a Rockchip boot-image contract before
FeROS-owned code can execute.

For the current PowKiddy X55 bring-up, the intended path is:

``` text
Power
  |
  v
RK3566 BootROM
  |
  v
RKNS / new-IDB
  |
  +-- DDR initialization payload
  |
  v
FeROS Stage 0
```

`mkimage.py` constructs the RKNS portion of this path without copying
the original X55 boot area or carrying unrelated partition-table or
bootloader data into the generated image.

The generated image contains only the bytes required by the current
bring-up experiment.

## Design Boundary

This tool is specific to the Rockchip RK3566 boot-image contract.

It is not part of the generic FeROS architecture.

``` text
Generic FeROS build
        |
        v
Platform bring-up
        |
        v
RK3566 boot-image preparation
```

Other SoCs may require completely different image builders and boot
contracts.

## Current Image Layout

The generated image begins with a zero-filled area and places the RKNS
structure at sector 64.

With 512-byte sectors:

``` text
Physical offset   Content
---------------   ----------------------------------------
0x00000           Reserved / zero-filled boot area
0x08000           RKNS header
0x08800           DDR initialization payload
...               FeROS Stage 0
```

The RKNS header occupies four sectors:

``` text
4 * 512 = 2048 bytes
```

The DDR payload begins four sectors after the start of RKNS.

FeROS Stage 0 begins at the first sector after the padded DDR payload.

Its physical offset is therefore calculated from the DDR payload size
and must not be treated as a fixed FeROS architectural constant.

For the current DDR firmware:

``` text
DDR size       = 55,296 bytes
DDR sectors    = 108
DDR sector     = 4
Stage 0 sector = 4 + 108 = 112
```

Since RKNS begins at physical sector 64:

``` text
Stage 0 physical sector = 64 + 112 = 176
Stage 0 physical offset = 176 * 512 = 0x16000
```

`0x16000` is therefore a result of the current payload layout, not a
universal RK3566 or FeROS Stage 0 address.

## RKNS Header

The RKNS structure begins at:

``` text
LBA 64
0x8000
```

The current header properties are:

``` text
Magic             RKNS
Header size       2048 bytes
Hash input size   1536 bytes
Hash algorithm    SHA-256
Payload count     2
Control value     0x00020180
```

The SHA-256 digest for the header is stored at offset:

``` text
0x600
```

relative to the beginning of the RKNS header.

The digest covers the first 1536 bytes of the header.

## Payload Descriptors

The current image contains two payload descriptors.

``` text
Descriptor #1   DDR initialization firmware
Descriptor #2   FeROS Stage 0
```

The descriptors begin at RKNS-relative offsets:

``` text
Descriptor #1   0x78
Descriptor #2   0xD0
```

Each descriptor identifies the payload starting sector and sector count
and contains the SHA-256 digest used to validate that payload.

The packed descriptor location/size word is constructed as:

``` text
(sector_count << 16) | starting_sector
```

### DDR Descriptor

For the current DDR firmware:

``` text
Starting sector   4
Sector count      108
Packed value      0x006c0004
Physical offset   0x8800
```

Current DDR SHA-256:

``` text
18260aab4dd77718572898b02c2a2a474fc54fc32ef4822fc6ce948ef0d86d89
```

### Stage 0 Descriptor

Stage 0 starts immediately after the DDR payload.

With the current DDR firmware:

``` text
Starting sector   112
```

The Stage 0 binary is padded to a complete 512-byte sector boundary
before its descriptor size and SHA-256 digest are calculated.

For the current 96-byte Stage 0:

``` text
Original size     96 bytes
Stored size       512 bytes
Sector count      1
Packed value      0x00010070
Physical offset   0x16000
```

The resulting padded Stage 0 SHA-256 is:

``` text
7b8a9c6bbceff911e3275fbea4abded18bdc63cd5418b22e7f9a3e3113458468
```

These values describe the current build and may change when Stage 0 or
its dependencies change.

## Building an Image

The tool exposes an explicit `build` command:

``` bash
python3 tools/image/rk3566/mkimage.py build \
  --ddr soc/rockchip/rk3566/firmware/ddr.bin \
  --stage0 build/x55/feros.bin \
  --output build/x55/boot/feros-x55.img
```

The builder:

1.  Reads the DDR initialization firmware.
2.  Reads the FeROS Stage 0 binary.
3.  Pads payloads to complete 512-byte sectors.
4.  Calculates the payload locations dynamically.
5.  Constructs both RKNS payload descriptors.
6.  Calculates the SHA-256 digest for each stored payload.
7.  Constructs the RKNS header.
8.  Calculates and stores the RKNS header SHA-256.
9.  Writes a clean boot image containing the required structures and
    payloads.

The normal repository workflow performs this operation through:

``` bash
make prepare-x55
```

The Makefile orchestrates the operation. `mkimage.py` owns the RKNS
binary format.

## Validating an Image

Validate an existing image with:

``` bash
python3 tools/image/rk3566/mkimage.py validate \
  --image build/x55/boot/feros-x55.img
```

Validation checks include:

-   Minimum image size.
-   RKNS magic.
-   Expected hash flag.
-   Expected control value.
-   RKNS header SHA-256.
-   Payload descriptor bounds.
-   Payload locations.
-   Payload SHA-256 digests.

A successful validation ends with:

``` text
RKNS image: VALID
```

Validation proves that the generated image is internally consistent with
the RKNS structure understood by the tool.

It does not by itself prove that the RK3566 BootROM has executed FeROS
Stage 0 on physical hardware.

## Current Verified Build

For the current X55 Stage 0 and DDR firmware, image generation produces:

``` text
RKNS offset:  0x8000
DDR size:     55296 bytes
Stage 0 size: 96 bytes
Image size:   90624 bytes
```

The resulting layout is:

``` text
0x00000  zero-filled boot area
0x08000  RKNS header          2048 bytes
0x08800  DDR payload         55296 bytes
0x16000  FeROS Stage 0         512 bytes padded
0x16200  end
```

The current clean RKNS header SHA-256 is:

``` text
96a440018165d00396eecf125843cdd34798bb5d6cc5f4d5a9251bc450902857
```

These values are useful for regression verification, but the builder
derives layout values from its inputs rather than relying on the current
Stage 0 offset as a permanent constant.

## Firmware Dependency

The current image uses:

``` text
soc/rockchip/rk3566/firmware/ddr.bin
```

This binary is the known-working DDR initialization payload identified
during X55 boot-media research.

Its current SHA-256 is:

``` text
18260aab4dd77718572898b02c2a2a474fc54fc32ef4822fc6ce948ef0d86d89
```

It is a temporary early-boot dependency while FeROS investigates how
much of the RK3566 initialization path can eventually be owned directly.

The dependency belongs to the RK3566 SoC layer rather than the PowKiddy
X55 board layer.

## Research vs. Build Inputs

FeROS deliberately separates forensic evidence from normal build
dependencies.

``` text
research/powkiddy/x55/boot/
```

contains preserved material used to understand the original hardware
boot contract.

Normal image generation must not read those forensic captures.

The relationship is:

``` text
Original hardware evidence
          |
          v
       research/
          |
          | one-time analysis / extraction
          v
Explicit SoC dependency
soc/rockchip/rk3566/firmware/ddr.bin
          |
          v
Normal FeROS image build
```

This prevents an original commercial boot image from becoming an
implicit dependency of FeROS.

## Safety

`mkimage.py` creates and validates regular image files.

It does not need to know which physical microSD device is connected and
should not contain device-selection or destructive media-writing logic.

Physical-media preparation belongs to a separate workflow with explicit
device discovery, verification, confirmation, writing, and read-back
validation.

This separation is intentional:

``` text
Build
  |
  v
Inspect
  |
  v
Validate
  |
  v
Prepare boot image
  |
  v
Prepare target media
  |
  v
Run / boot
```

## Engineering Rules

When modifying this tool:

-   Keep RKNS format knowledge in the image tool, not in the Makefile.
-   Calculate payload placement from actual payload sizes.
-   Work in sectors where the RKNS format defines values in sectors.
-   Pad stored payloads before calculating their stored hashes.
-   Validate every generated hash.
-   Reject malformed or out-of-bounds descriptors.
-   Keep forensic captures out of normal build inputs.
-   Document binary-format constants and non-obvious operations in
    English.
-   Do not turn current X55 observations into generic FeROS architecture
    rules.

## Future Work

Potential future work includes:

-   Stronger descriptor validation.
-   Additional RK3566 image diagnostics.
-   More explicit image metadata reporting.
-   Regression tests for known-good RKNS structures.
-   Integration with safe target-media preparation.
-   Investigation of the temporary DDR initialization dependency.

Physical X55 execution remains a separate bring-up milestone.

------------------------------------------------------------------------

FeROS --- Ferrite Retro Operating System

**Close to the metal.**
