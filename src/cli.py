"""Command-line interface for FeROS Builder."""

from image.rk3566.mkimage import create_parser


def main() -> None:
    """Run an image operation using explicit caller-provided paths."""
    parser = create_parser()
    parser.prog = "builder"
    arguments = parser.parse_args()
    try:
        arguments.handler(arguments)
    except (OSError, ValueError) as error:
        parser.error(str(error))
