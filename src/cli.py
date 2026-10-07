"""Command-line interface for FeROS Builder."""
from importlib.metadata import PackageNotFoundError, version

from parser import create_parser
import repository


def product_version() -> str:
    """Read the installed application version."""
    try:
        return version("feros-builder")
    except PackageNotFoundError:
        return "unknown"


def repository_add() -> None:
    """Collect repository registration details interactively."""
    print("Add repository")
    print()

    try:
        url = input("Repository URL: ").strip()
        name = input(
            "Repository name [leave blank to use default name]: "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nRepository registration cancelled.")
        return

    entry = repository.add(url, name)
    category = "official" if entry["official"] else "unofficial"

    print()
    print(f"Repository added: {entry['name']} [{category}]")
    print(f"URL: {entry['url']}")


def repository_command(arguments) -> None:
    """Display locally registered device-support repositories."""
    if arguments.add:
        repository_add()
        return

    if (
            arguments.info is not None
            or arguments.delete is not None
            or arguments.update is not None
    ):
        raise ValueError("This repository operation is not implemented yet.")

    repositories = repository.available()

    if not repositories:
        print("No repositories registered.")

    print("Repositories:")

    for index, entry in enumerate(repositories, start=1):
        category = "official" if entry["official"] else "unofficial"
        print(f"  {index}. {entry['name']} [{category}]")
        print(f"     {entry['url']}")

    print()
    print("Command help:")
    print("  builder help --repository")


def general_help() -> None:
    """Display the general command menu."""
    print("Usage:")
    print("  builder <command> [options]")
    print()
    print("Commands:")

    commands = (
        ("repository", "List device sources"),
        ("build", "Build a device image"),
        ("validate", "Validate an image"),
        ("help", "Display general or command-specific help"),
        ("update", "Update Builder and repositories"),
        ("version", "Display build and version information"),
    )

    for name, description in commands:
        print(f"  {name:<18} {description}")

    print()
    print("Command help:")

    for name in ("repository", "build", "validate", "update"):
        print(f"  builder help --{name}")


def main_header() -> None:
    """Display the standard application header."""
    print(f"FeROS Builder v{product_version()}")
    print("Build, validate binary images and manage device support.")
    print()


def command_help(topic: str) -> None:
    """Display the syntax and current availability of a command."""
    if topic == "repository":
        print("Usage:")
        print("  builder repository")
        print("  builder repository --add")
        print("  builder repository --info <index|name>")
        print("  builder repository --delete <index|name>")
        print("  builder repository --update [<index|name>]")
        print()
        print("Listing and interactive registration are available.")
        print("Info, delete and update are not implemented yet.")
    elif topic == "build":
        print("Usage:")
        print("  builder build --device-name <NAME> --firmware <PATH> --output <PATH> [--validate]")
        print("This operation is not implemented yet.")
    elif topic == "validate":
        print("Usage:")
        print("  builder validate --image <PATH>")
        print("This operation is not implemented yet.")
    elif topic == "update":
        print("Usage:")
        print("  builder update")
        print("This operation is not implemented yet.")


def main() -> None:
    """Dispatch implemented commands and reject unavailable operations."""
    parser = create_parser()
    arguments = parser.parse_args()

    main_header()

    if arguments.command is None:
        general_help()
    elif arguments.command == "repository":
        try:
            repository_command(arguments)
        except (OSError, ValueError) as error:
            parser.error(str(error))
    elif arguments.command == "help":
        topic = next((name for name in ("repository", "build", "validate", "update")
                      if getattr(arguments, name)), None)
        if topic is None:
            general_help()
        else:
            command_help(topic)
    elif arguments.command == "version":
        return
    else:
        parser.error(f"{arguments.command} is not implemented yet")
