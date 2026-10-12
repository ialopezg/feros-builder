"""Present device support entries; Sources catalog integration is pending."""

COLUMNS = ("STATUS", "DEVICE", "SOC", "REPOSITORY", "UPDATE")


def format_table(rows):
    """Align all columns, including when no entries are available."""
    records = [COLUMNS]
    for row in rows:
        records.append(tuple(str(row.get(key.lower(), "")) for key in COLUMNS))

    widths = [max(len(record[i]) for record in records)
              for i in range(len(COLUMNS))]
    return "\n".join(
        "  ".join(value.ljust(width) for value, width in zip(record, widths)).rstrip()
        for record in records
    )


def list_devices():
    """Return known entries once FeROS Sources discovery is implemented."""
    return []


def display() -> None:
    """Display the device listing."""
    print("No device found")
    print()
    print("Run 'builder help --device' for available commands.")
