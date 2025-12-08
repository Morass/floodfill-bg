""" Floodfill-bg: Background removal tool using flood-fill algorithm.

    CLI driver for removing backgrounds from images by flood-filling
    from seed points or globally purging matching colors.
"""

from __future__ import annotations

from pathlib import Path

import click
from PIL import Image

from libs.common import get_corner_seeds, parse_seed, trim_transparent
from libs.removal import floodfill_remove, global_purge
from libs.validation import validate_input_file, validate_seeds, validate_threshold


def print_header(
    input_path: Path,
    output_path: Path,
    width: int,
    height: int,
    mode: str,
    threshold: int,
    eight_way: bool,
    trim: bool,
    seeds: list[tuple[int, int]],
) -> None:
    """ Print formatted processing header with all parameters.

        Args:
            input_path (Path): Input file path.
            output_path (Path): Output file path.
            width (int): Image width.
            height (int): Image height.
            mode (str): Processing mode string.
            threshold (int): Color threshold value.
            eight_way (bool): Whether 8-way neighbors enabled.
            trim (bool): Whether trim is enabled.
            seeds (list[tuple[int, int]]): List of seed coordinates.
    """
    click.echo("")
    click.echo("=" * 50)
    click.echo("floodfill-bg")
    click.echo("=" * 50)
    click.echo(f"Input:      {input_path}")
    click.echo(f"Output:     {output_path}")
    click.echo(f"Initial:    {width}x{height}")
    click.echo(f"Mode:       {mode}")
    click.echo(f"Threshold:  {threshold}")
    click.echo(f"8-way:      {eight_way}")
    click.echo(f"Trim:       {trim}")
    click.echo(f"Seeds:      {seeds}")
    click.echo("-" * 50)


def print_results(
    removed: int,
    trimmed: bool,
    bbox: tuple[int, int, int, int] | None,
    final_width: int,
    final_height: int,
    output_path: Path,
) -> None:
    """ Print formatted processing results.

        Args:
            removed (int): Number of pixels removed.
            trimmed (bool): Whether image was trimmed.
            bbox (tuple[int, int, int, int] | None): Bounding box if trimmed, None otherwise.
            final_width (int): Final image width.
            final_height (int): Final image height.
            output_path (Path): Output file path.
    """
    click.echo(f"Removed:    {removed:,} pixels")

    if trimmed and bbox:
        left, top, right, bottom = bbox
        click.echo(f"Trimmed:    bbox=({left}, {top}, {right}, {bottom})")

    click.echo(f"Final:      {final_width}x{final_height}")
    click.echo("-" * 50)

    file_size = output_path.stat().st_size
    if file_size > 1024 * 1024:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"
    else:
        size_str = f"{file_size // 1024} KB"

    click.echo(f"Saved:      {output_path} ({size_str})")
    click.echo("=" * 50)


@click.command()
@click.argument("input_path", callback=validate_input_file)
@click.option("-o", "--output", "output_path", type=click.Path(), help="Output path. Default: /tmp/<name>_cleaned.png")
@click.option("-s", "--seed", "seeds", multiple=True, help="Seed point 'x,y' or 'x%%,y%%'. Can repeat.")
@click.option("-c", "--auto-corners", is_flag=True, help="Use all 4 corners as seeds.")
@click.option("-t", "--threshold", default=50, callback=validate_threshold, help="Color distance 0-441. Default: 50")
@click.option("--8-way", "eight_way", is_flag=True, help="Use 8-way neighbors (includes diagonals).")
@click.option("-g", "--global", "global_mode", is_flag=True, help="Global purge: remove ALL matching pixels.")
@click.option("--trim", is_flag=True, help="Trim transparent edges after processing.")
@click.option("-i", "--info", is_flag=True, help="Print image info and exit.")
def main(
    input_path: Path,
    output_path: str | None,
    seeds: tuple[str, ...],
    auto_corners: bool,
    threshold: int,
    eight_way: bool,
    global_mode: bool,
    trim: bool,
    info: bool,
) -> None:
    """ Remove background using flood-fill from seed points.

        Seeds can be absolute coordinates (e.g., --seed 0,0) or percentages
        (e.g., --seed 100%,100% for bottom-right corner).

        \b
        Examples:
            floodfill-bg image.png --auto-corners
            floodfill-bg image.png --seed 0,0 --seed 100%,100%
            floodfill-bg image.png -c -t 30 -o cleaned.png
            floodfill-bg image.png -c --global -t 40
    """
    try:
        image = Image.open(input_path)
    except Exception as e:
        raise click.ClickException(f"Failed to open image: {e}")

    width, height = image.size

    if info:
        click.echo(f"{input_path.name}: {width}x{height}, {image.mode}")
        return

    validate_seeds(seeds, auto_corners)
    if global_mode and eight_way:
        raise click.UsageError("--8-way cannot be used with --global")

    seed_points = []
    if auto_corners:
        seed_points.extend(get_corner_seeds(width, height))
    if seeds:
        seed_points.extend([parse_seed(s, width, height) for s in seeds])

    if output_path is None:
        output_path = f"/tmp/{input_path.stem}_cleaned.png"
    output_as_path = Path(output_path)

    mode_str = "GLOBAL purge" if global_mode else "flood-fill"

    print_header(input_path, output_as_path, width, height, mode_str, threshold, eight_way, trim, seed_points)

    if global_mode:
        result, removed = global_purge(image, seed_points, threshold)
    else:
        result, removed = floodfill_remove(image, seed_points, threshold, eight_way)

    final_width, final_height = result.size
    bbox = None

    if trim:
        result, bbox = trim_transparent(result)
        final_width, final_height = result.size

    result.save(output_as_path, "PNG")

    print_results(removed, trim, bbox, final_width, final_height, output_as_path)


if __name__ == "__main__":
    main()
