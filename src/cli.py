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


def repository_command(arguments) -> None:
    """Display locally registered device-support repositories."""
    if (
            arguments.add
            or arguments.info is not None
            or arguments.delete is not None
            or arguments.update is not None
    ):
        print("This repository operation is not implemented yet.")
        return

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


def main() -> None:
    """Parse and display arguments without executing operations."""
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
    else:
        print(arguments)
