def list_devices() -> list[dict]:
    """Return available device support entries."""
    return []

def search(devices: list[dict], query: str) -> list[dict]:
    query = query.strip().casefold()

    if not query:
        raise ValueError("search query cannot be empty")

    return [
        entry for entry in devices
        if any(query in str(entry.get(field, "")).lower()
               for field in ("id", "device", "soc", "repository"))
    ]
