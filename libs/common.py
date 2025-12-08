""" Common utilities for color manipulation, coordinate parsing, and image operations.
"""

from PIL import Image


def color_distance(color1: tuple, color2: tuple) -> float:
    """ Calculate Euclidean distance between two RGB(A) colors.

        Formula:
            sqrt((r1-r2)² + (g1-g2)² + (b1-b2)²)

        Args:
            color1 (tuple): First color as (R, G, B) or (R, G, B, A) tuple.
            color2 (tuple): Second color as (R, G, B) or (R, G, B, A) tuple.

        Returns:
            float: Euclidean distance between colors (0-441 for RGB).

        Note:
            Alpha channel is ignored in distance calculation.
    """
    r1, g1, b1 = color1[:3]
    r2, g2, b2 = color2[:3]
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def parse_seed(seed_str: str, width: int, height: int) -> tuple[int, int]:
    """ Parse seed string to (x, y) pixel coordinates.

        Args:
            seed_str (str): Coordinate string in format "x,y" or "x%,y%".
            width (int): Image width in pixels.
            height (int): Image height in pixels.

        Returns:
            tuple[int, int]: Tuple of (x, y) pixel coordinates.

        Raises:
            ValueError: If seed format is invalid or coordinates out of range.

        Note:
            Percentage values are converted to pixel coordinates.
            "100%" maps to (dimension - 1) to stay within bounds.
    """
    def _parse_number(s: str) -> float:
        try:
            return float(s)
        except ValueError as e:
            raise ValueError(f"Invalid number: {s}") from e

    parts = seed_str.strip().split(",")
    if len(parts) != 2:
        raise ValueError(f"Seed must be \"x,y\" or \"x%,y%\" format, got: {seed_str}")

    coords: list[float] = []
    for i, part in enumerate(parts):
        part = part.strip()
        max_val = width if i == 0 else height

        if part.endswith("%"):
            pct = _parse_number(part[:-1])
            if not 0 <= pct <= 100:
                raise ValueError(f"Percentage must be 0-100, got: {part}")
            coords.append((pct / 100) * (max_val - 1))
        else:
            val = _parse_number(part)
            if not 0 <= val < max_val:
                raise ValueError(f"Coordinate {val} out of range 0-{max_val-1}")
            coords.append(val)

    return int(coords[0]), int(coords[1])


def get_corner_seeds(width: int, height: int) -> list[tuple[int, int]]:
    """ Get pixel coordinates for all 4 image corners.

        Args:
            width (int): Image width in pixels.
            height (int): Image height in pixels.

        Returns:
            list[tuple[int, int]]: List of 4 corner coordinates: [top-left, top-right, bottom-left, bottom-right].
    """
    return [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
    ]


def trim_transparent(image: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """ Trim transparent edges from image.

        Args:
            image (Image.Image): PIL Image to trim.

        Returns:
            tuple[Image.Image, tuple[int, int, int, int]]: Tuple of (trimmed_image, bounding_box).
            Bounding box is (left, top, right, bottom) of non-transparent area.

        Note:
            If entire image is transparent, returns original image with full bounds.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    bbox = image.getbbox()

    if bbox is None:
        return image, (0, 0, image.width, image.height)

    trimmed = image.crop(bbox)
    return trimmed, bbox
