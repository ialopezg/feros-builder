"""Package a tested native Builder with source/build identity and notices."""

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ("README.md", "LICENSE", "CHANGELOG.md", "SECURITY.md",
             "VERSIONING.md", "STABILITY.md", "THIRD_PARTY.md")


def version():
    match = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"\s*$',
                      (ROOT / "pyproject.toml").read_text(), re.MULTILINE)
    if not match:
        raise ValueError("Expected one numeric MAJOR.MINOR.PATCH package version")
    return match.group(1)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def package(binary, tag):
    release_version = version()
    commit = git("rev-parse", "HEAD")
    if tag:
        if tag != "v" + release_version:
            raise ValueError("Release tag does not match pyproject.toml")
        if git("rev-parse", tag + "^{commit}") != commit:
            raise ValueError("Release tag does not point to this checkout")
    if git("status", "--porcelain"):
        raise ValueError("Commit the candidate before packaging; working tree is not clean")
    system = platform.system().lower()
    arch = {"arm64": "aarch64", "amd64": "x86_64"}.get(
        platform.machine().lower(), platform.machine().lower())
    if ((system, arch) not in {("darwin", "aarch64"), ("darwin", "x86_64"),
                              ("linux", "aarch64"), ("linux", "x86_64"),
                              ("windows", "x86_64")}):
        raise ValueError("Unsupported package host")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError("A tested executable is required")
    binary_name = "builder.exe" if system == "windows" else "builder"
    name = f"feros-builder-v{release_version}-{system}-{arch}"
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / (name + ".tar.gz")
    checksum = dist / (archive.name + ".sha256")
    if archive.exists() or checksum.exists():
        raise ValueError("Package already exists; use a fresh checkout/output directory")
    with tempfile.TemporaryDirectory(prefix="builder-package-") as directory:
        stage = Path(directory) / name
        stage.mkdir()
        shutil.copy2(binary, stage / binary_name)
        for filename in DOCUMENTS:
            shutil.copy2(ROOT / filename, stage / filename)
        licenses = stage / "licenses"
        if (ROOT / "licenses").exists():
            shutil.copytree(ROOT / "licenses", licenses)
        else:
            licenses.mkdir()
        python_license = next((path for path in (
            Path(sysconfig.get_path("stdlib")) / "LICENSE.txt",
            Path(sys.base_prefix) / "LICENSE.txt",  # Native Windows Python.
        ) if path.is_file()), None)
        if python_license is None:
            raise ValueError("CPython LICENSE.txt missing from build interpreter")
        shutil.copy2(python_license, licenses / "CPython-LICENSE.txt")
        pyinstaller = metadata.distribution("pyinstaller")
        found = False
        for entry in pyinstaller.files or []:
            if "licenses" in entry.parts or entry.name.upper().startswith(("COPYING", "LICENSE")):
                source = Path(str(pyinstaller.locate_file(entry)))
                if source.is_file():
                    destination = licenses / "PyInstaller" / Path(*entry.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
                    found = True
        if not found:
            raise ValueError("PyInstaller license files not found")
        info = {
            "product": "feros-builder", "version": release_version,
            "commit": commit, "tag": tag, "os": system, "architecture": arch,
            "host": platform.platform(), "python": platform.python_version(),
            "executable_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "build_distributions": sorted(
                [{"name": d.metadata["Name"], "version": d.version}
                 for d in metadata.distributions()], key=lambda d: d["name"].lower()),
            "inventory_scope": "Build environment; not a complete binary SBOM",
        }
        (stage / "BUILD-INFO.json").write_text(json.dumps(info, indent=2) + "\n")
        env = dict(os.environ, BUILDER=str(stage / binary_name))
        subprocess.run([sys.executable, str(ROOT / "scripts/check.py")],
                       cwd=directory, env=env, check=True)
        temporary = Path(directory) / archive.name
        with tarfile.open(temporary, "w:gz") as output:
            output.add(stage, arcname=name)
        # Re-test the actual archive payload, not only the staging directory.
        extracted = Path(directory) / "extracted"
        extracted.mkdir()
        with tarfile.open(temporary) as source:
            for member in source.getmembers():
                path = Path(member.name)
                if path.is_absolute() or ".." in path.parts or not (member.isdir() or member.isfile()):
                    raise ValueError("Unexpected archive entry")
            source.extractall(extracted, **({"filter": "data"}
                              if hasattr(tarfile, "data_filter") else {}))
        env["BUILDER"] = str(extracted / name / binary_name)
        subprocess.run([sys.executable, str(ROOT / "scripts/check.py")],
                       cwd=extracted, env=env, check=True)
        shutil.copy2(temporary, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    print(archive)
    print(checksum)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "target/release" /
                        ("builder.exe" if os.name == "nt" else "builder"))
    parser.add_argument("--tag", help="Existing vMAJOR.MINOR.PATCH tag to verify")
    args = parser.parse_args()
    try:
        package(args.binary.resolve(), args.tag)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Packaging failed: {error}\n")
