import argparse
import sys
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """Define commands and options without executing operations."""
    parser = BuilderArgumentParser(
        prog="builder",
        add_help=False,
        allow_abbrev=False,
    )

    commands = parser.add_subparsers(dest="command", parser_class=BuilderArgumentParser)
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

    device = commands.add_parser(
        "device",
        help="Discover and manage device support.",
        add_help=False,
    )
    device_actions = device.add_mutually_exclusive_group()
    device_actions.add_argument("-l", "--list", action="store_true")
    device_actions.add_argument("-s", "--search", metavar="QUERY")
    device_actions.add_argument("-i", "--info", metavar="DEVICE")
    device_actions.add_argument("-f", "--fetch", metavar="DEVICE")
    device_actions.add_argument("--install", metavar="DEVICE")
    device_actions.add_argument("-u", "--update", metavar="DEVICE")
    device.add_argument("--component", metavar="COMPONENT")
    device.add_argument("--version", metavar="VERSION")

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
    topics.add_argument("--device", action="store_true")
    topics.add_argument("--build", action="store_true")
    topics.add_argument("--validate", action="store_true")
    topics.add_argument("--update", action="store_true")

    commands.add_parser(
        "version",
        help="Display build and version information.",
        add_help=False,
    )

    return parser


class BuilderArgumentParser(argparse.ArgumentParser):
    """Use strict options and consistent, command-aware error messages."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)

    def parse_args(self, args=None, namespace=None):
        parsed, unknown = self.parse_known_args(args, namespace)
        if unknown:
            command = getattr(parsed, "command", None)
            scope = f"{self.prog} {command}" if command and self.prog == "builder" else self.prog
            self._report_error(f"unrecognized arguments: {' '.join(unknown)}", scope)
        return parsed

    def error(self, message: str, scope: str | None = None) -> None:
        self._report_error(message, scope or self.prog)

    def _report_error(self, message: str, scope: str) -> None:
        print(f"usage: {scope} [subcommand ...parameters]", file=sys.stderr)
        print(f"{scope}: error: {message}", file=sys.stderr)
        print(file=sys.stderr)
        command = scope.removeprefix("builder").strip().split(" ")[0]
        help_command = f"builder help --{command}" if command else "builder help"
        print(f"Run '{help_command}' for available commands.", file=sys.stderr)
        self.exit(2)
