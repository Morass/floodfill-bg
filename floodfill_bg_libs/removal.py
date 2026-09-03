""" Background removal algorithms.
"""

from collections import deque

from PIL import Image

from .common import color_distance


def floodfill_remove(
    image: Image.Image,
    seeds: list[tuple[int, int]],
    threshold: float,
    eight_way: bool = False,
) -> tuple[Image.Image, int]:
    """ Remove background using flood-fill from seed points.

        Starts from each seed point and spreads to connected pixels within
        the color threshold, making them transparent.

        Algorithm:
            BFS (Breadth-First Search) from all seed points simultaneously.

        Complexity:
            O(W * H * S) where W is width, H is height, S is number of unique seed colors.

        Args:
            image (Image.Image): PIL Image to process.
            seeds (list[tuple[int, int]]): List of (x, y) seed coordinates to start flood-fill from.
            threshold (float): Maximum color distance (0-441) to consider pixels as background.
            eight_way (bool): If True, include diagonal neighbors. Default is 4-way.

        Returns:
            tuple[Image.Image, int]: Tuple of (processed_image, removed_pixel_count).

        Note:
            Only removes pixels that are connected to seed points.
            Disconnected regions matching the color are preserved.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    pixels = image.load()
    width, height = image.size
    visited = [[False] * height for _ in range(width)]

    neighbors = [(0, -1), (-1, 0), (1, 0), (0, 1)]
    if eight_way:
        neighbors += [(-1, -1), (1, -1), (-1, 1), (1, 1)]

    removed = 0

    # Collect unique seed colors
    seed_colors = list(set(pixels[x, y] for x, y in seeds))

    # Initialize queue with all seeds
    queue = deque(seeds)

    while queue:
        x, y = queue.popleft()

        if visited[x][y]:
            continue
        visited[x][y] = True

        current_color = pixels[x, y]
        if not any(color_distance(sc, current_color) <= threshold for sc in seed_colors):
            continue

        pixels[x, y] = (0, 0, 0, 0)
        removed += 1

        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                queue.append((nx, ny))

    return image, removed


def global_purge(
    image: Image.Image,
    seeds: list[tuple[int, int]],
    threshold: float,
) -> tuple[Image.Image, int]:
    """ Remove all pixels matching seed colors globally.

        Scans every pixel in the image and makes it transparent if within
        threshold of any seed color. Does not require connectivity.

        Args:
            image (Image.Image): PIL Image to process.
            seeds (list[tuple[int, int]]): List of (x, y) coordinates to sample target colors from.
            threshold (float): Maximum color distance (0-441) to consider as match.

        Returns:
            tuple[Image.Image, int]: Tuple of (processed_image, removed_pixel_count).

        Note:
            Unlike flood-fill, this removes ALL matching pixels regardless
            of whether they are connected to the seed points.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    pixels = image.load()
    width, height = image.size

    seed_colors = [pixels[x, y] for x, y in seeds]

    removed = 0

    for y in range(height):
        for x in range(width):
            current_color = pixels[x, y]
            if any(color_distance(sc, current_color) <= threshold for sc in seed_colors):
                pixels[x, y] = (0, 0, 0, 0)
                removed += 1

    return image, removed
