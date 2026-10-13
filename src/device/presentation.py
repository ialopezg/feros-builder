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


def display(rows: list[dict]) -> None:
    """Display the device listing."""
    if rows:
        print("Device Support")
        print("-" * 68)
        print(format_table(rows))
    else:
        print("No device found")

    print()
    print("Run 'builder help --device' for available commands.")
