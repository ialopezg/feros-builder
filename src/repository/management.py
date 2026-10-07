"""Read locally registered device-support repositories."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def initialize(path: Path):
    """Create the initial registry without replacing an existing file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content = f'''schema_version = "1.0"

[[repositories]]
id = "feros-official"
name = "FeROS Official Repository"
url = "https://github.com/ialopezg/feros-targets"
official = true
created_at = "{timestamp}"
updated_at = "{timestamp}"
'''

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
    except FileExistsError:
        pass

def configuration_path():
    """Locate the persistent per-user repository configuration."""
    if sys.platform == "win32":
        root = Path(
            os.environ.get("APPDATA", Path.home() / "AppData/Local")
        ) / "FeROS/Builder"
    elif sys.platform == "darwin":
        root = Path().home() / "Library/Application Support/FeROS/Builder"
    else:
        root = Path(
            os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
        ) / "feros/builder"

    return root / "repositories.toml"

def available() -> list[dict]:
    """Load registered repositories without accessing the network."""
    path = configuration_path()

    if not path.exists():
        initialize(path)

    with path.open("rb") as stream:
        configuration = tomllib.load(stream)

    if configuration.get("schema_version") != "1.0":
        raise ValueError("unsupported repository configuration schema")

    repositories = configuration.get("repositories")

    if not isinstance(repositories, list):
        raise ValueError("invalid repository configuration")

    for entry in repositories:
        if not isinstance(entry, dict):
            raise ValueError("invalid repository entry")

        for field in ("id", "name", "url"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f"invalid repository field: {field}")

        if not isinstance(entry.get("official"), bool):
            raise ValueError("invalid repository classification")

    return repositories
