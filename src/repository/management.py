"""Manage locally registered device-support repositories."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, build_opener
from uuid import uuid4

import tomli_w


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

    return _load_configuration()["repositories"]


def _load_configuration() -> dict:
    """Read and validate the existing store without creating or changing it."""
    with configuration_path().open("rb") as stream:
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

    return configuration


REGISTRY_URL = "https://raw.githubusercontent.com/ialopezg/feros-targets/main/repository.toml"

def normalize_url(address: str) -> str:
    """Validate and normalize an HTTPS repository URL."""
    address = address.strip()
    if any(character.isspace() or ord(character) < 32 for character in address):
        raise ValueError("repository URL must not contain whitespace or control characters")
    url = urlsplit(address)
    if url.scheme != "https" or not url.hostname:
        raise ValueError("repository URL must use HTTPS and contain a host")
    if url.username is not None or url.password is not None:
        raise ValueError("repository URL must not contain credentials")
    if url.query or url.fragment:
        raise ValueError("repository URL must not contain a query or fragment")
    host = url.hostname.encode("idna").decode("ascii").lower()
    if ":" in host:
        host = f"[{host}]"
    if url.port not in (None, 443):
        host = f"{host}:{url.port}"
    return urlunsplit(("https", host, url.path or "/", "", ""))


class _NoRedirect(HTTPRedirectHandler):
    """Require the registry to respond at its configured endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def is_official(url: str) -> bool:
    """Classify a URL using the official registry, never self-declaration."""
    with build_opener(_NoRedirect()).open(REGISTRY_URL, timeout=15) as response:
        content = response.read(1024 * 1024 + 1)
    if len(content) > 1024 * 1024:
        raise ValueError("official registry exceeds size limit")
    registry = tomllib.loads(content.decode("utf-8"))
    if type(registry.get("schema_version")) is not int or registry["schema_version"] != 1:
        raise ValueError("unsupported official registry schema")
    entries = registry.get("repositories")
    if not isinstance(entries, list):
        raise ValueError("invalid official registry")
    urls = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("url"), str):
            raise ValueError("invalid official registry entry")
        urls.add(normalize_url(entry["url"]))
    return normalize_url(url) in urls


def _save(configuration: dict) -> None:
    """Replace the store atomically after serialization succeeds."""
    path = configuration_path()
    content = tomli_w.dumps(configuration).encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def add(uri: str, name: str | None = None) -> dict:
    """Validate, classify, and persist a repository subscription."""
    url = normalize_url(uri)
    name = (name or "").strip() or urlsplit(url).hostname
    repositories = available()
    if any(normalize_url(entry["url"]) == url for entry in repositories):
        raise ValueError("repository URL already registered")
    if any(entry["name"].casefold() == name.casefold() for entry in repositories):
        raise ValueError("repository name already registered")
    official = is_official(url)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "id": str(uuid4()),
        "name": name,
        "url": url,
        "official": official,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    with configuration_path().open("rb") as stream:
        configuration = tomllib.load(stream)
    configuration["repositories"].append(entry)
    _save(configuration)
    return entry

def delete(selector: str) -> dict:
    """Remove a subscription by its displayed index or case-insensitive name."""
    selector = selector.strip()
    hint = "Run 'builder repository' to list registered repositories."
    if not selector:
        raise ValueError(f"repository index or name is required. {hint}")
    if not configuration_path().exists():
        raise ValueError(f"no repository configuration exists. {hint}")

    configuration = _load_configuration()
    repositories = configuration["repositories"]
    if selector.isascii() and selector.isdecimal():
        index = int(selector) - 1
        if index < 0 or index >= len(repositories):
            raise ValueError(f"repository index out of range: {selector}. {hint}")
    else:
        matches = [index for index, entry in enumerate(repositories)
                   if entry["name"].casefold() == selector.casefold()]
        if not matches:
            raise ValueError(f"repository not found: {selector}. {hint}")
        if len(matches) > 1:
            raise ValueError(f"repository name is ambiguous: {selector}; use its index. {hint}")
        index = matches[0]

    removed = repositories.pop(index)
    _save(configuration)
    return removed
