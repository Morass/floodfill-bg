""" Input validation utilities for CLI arguments.
"""

from pathlib import Path

import click

VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
THRESHOLD_MIN = 0
THRESHOLD_MAX = 441


def validate_threshold(ctx: click.Context, param: click.Parameter, value: int) -> int:
    """ Validate threshold is within valid color distance range.

        Args:
            ctx (click.Context): Click context (unused, required by Click).
            param (click.Parameter): Click parameter (unused, required by Click).
            value (int): Threshold value to validate.

        Returns:
            int: Validated threshold value.

        Raises:
            click.BadParameter: If threshold is outside valid range.

        Note:
            Valid range is 0-441 (maximum Euclidean distance in RGB space).
    """
    if not THRESHOLD_MIN <= value <= THRESHOLD_MAX:
        raise click.BadParameter(f"Threshold must be {THRESHOLD_MIN}-{THRESHOLD_MAX}, got: {value}")
    return value


def validate_input_file(ctx: click.Context, param: click.Parameter, value: str) -> Path:
    """ Validate input file exists and has supported image extension.

        Args:
            ctx (click.Context): Click context (unused, required by Click).
            param (click.Parameter): Click parameter (unused, required by Click).
            value (str): File path string to validate.

        Returns:
            Path: Validated Path object.

        Raises:
            click.BadParameter: If file not found or unsupported format.
    """
    path = Path(value)

    if not path.exists():
        raise click.BadParameter(f"File not found: {value}")

    if path.suffix.lower() not in VALID_IMAGE_EXTENSIONS:
        raise click.BadParameter(
            f"Unsupported format: {path.suffix}. Supported: {', '.join(sorted(VALID_IMAGE_EXTENSIONS))}"
        )

    return path


def validate_seeds(seeds: tuple[str, ...], auto_corners: bool, trim: bool) -> None:
    """ Validate that at least one seed source is provided (unless trim-only mode).

        Args:
            seeds (tuple[str, ...]): Tuple of seed coordinate strings.
            auto_corners (bool): Whether auto-corners flag is set.
            trim (bool): Whether trim flag is set.

        Raises:
            click.UsageError: If neither seeds nor auto_corners provided and trim is not set.
    """
    if not seeds and not auto_corners and not trim:
        raise click.UsageError("Must specify at least one --seed and/or use --auto-corners (or use --trim for trim-only mode)")
