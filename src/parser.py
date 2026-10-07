import argparse
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """Define commands and options without executing operations."""
    parser = argparse.ArgumentParser(
        prog="builder",
        add_help=False,
    )

    commands = parser.add_subparsers(dest="command")
    repository = commands.add_parser(
        "repository",
        help="Manage device-support repositories.",
        add_help=False,
    )

    actions = repository.add_mutually_exclusive_group()
    actions.add_argument("--add", action="store_true")
    actions.add_argument("--info", metavar="INDEX|NAME")
    actions.add_argument("--delete", metavar="INDEX|NAME")
    actions.add_argument(
        "--update",
        nargs="?",
        const="",
        metavar="INDEX|NAME",
    )

    commands.add_parser(
        "update",
        help="Update Builder and repositories.",
        add_help=False,
    )

    build = commands.add_parser(
        "build",
        help="Build a device image.",
        add_help=False,
    )

    build.add_argument("--device-name", required=True)
    build.add_argument("--firmware", required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--validate", action="store_true")

    validate = commands.add_parser(
        "validate",
        help="Validate an image.",
        add_help=False,
    )
    validate.add_argument("--image", type=Path, required=True)

    help_parser = commands.add_parser(
        "help",
        help="Display general or command-specific help.",
        add_help=False,
    )
    topics = help_parser.add_mutually_exclusive_group()
    topics.add_argument("--repository", action="store_true")
    topics.add_argument("--build", action="store_true")
    topics.add_argument("--validate", action="store_true")
    topics.add_argument("--update", action="store_true")

    commands.add_parser(
        "version",
        help="Display build and version information.",
        add_help=False,
    )

    return parser
