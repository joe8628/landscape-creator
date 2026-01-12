"""Decoration generation with rocks, mushrooms, and flowers."""

import numpy as np
from typing import Set, Tuple

from ..core.voxel_grid import VoxelGrid
from ..core.materials import MaterialType


class DecorationGenerator:
    """Generates decorative elements: rocks, mushrooms, and flowers."""

    def __init__(self, seed: int):
        """Initialize decoration generator with a seed.

        Args:
            seed: Integer seed for reproducible generation
        """
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        self._tree_positions: Set[Tuple[int, int]] = set()

    def generate(self, grid: VoxelGrid, tree_positions: Set[Tuple[int, int]] = None) -> None:
        """Generate decorations on the terrain.

        Args:
            grid: VoxelGrid with existing terrain and plants
            tree_positions: Set of (x, y) positions where trees exist
        """
        self._tree_positions = tree_positions or set()

        self._place_rocks(grid)
        self._place_mushrooms(grid)
        self._place_flowers(grid)

    def _place_rocks(self, grid: VoxelGrid) -> None:
        """Place scattered rocks and boulders."""
        num_rocks = grid.width * grid.depth // 200

        for _ in range(num_rocks):
            x = self._rng.integers(0, grid.width)
            y = self._rng.integers(0, grid.depth)
            z = grid.get_surface_height(x, y)

            surface = grid.get(x, y, z)
            if surface == MaterialType.WATER:
                continue

            # Keep distance from plants
            if self._near_plant(x, y, 2):
                continue

            # Create rock cluster
            size = self._rng.integers(1, 4)
            for dx in range(size):
                for dy in range(size):
                    for dz in range(size):
                        if self._rng.random() > 0.4:
                            grid.set(x + dx, y + dy, z + 1 + dz, MaterialType.STONE)

    def _place_mushrooms(self, grid: VoxelGrid) -> None:
        """Place mushrooms near trees."""
        num_mushrooms = grid.width * grid.depth // 500

        for _ in range(num_mushrooms):
            x = self._rng.integers(0, grid.width)
            y = self._rng.integers(0, grid.depth)
            z = grid.get_surface_height(x, y)

            # Mushrooms only in mid-range heights
            if z < 26 or z > 90:
                continue

            surface = grid.get(x, y, z)
            if surface not in (MaterialType.GRASS, MaterialType.DIRT):
                continue

            # Must be near trees
            if not self._near_plant(x, y, 5):
                continue

            # Create mushroom (stem + cap)
            height = self._rng.integers(2, 5)

            # Stem
            for h in range(height - 1):
                grid.set(x, y, z + 1 + h, MaterialType.DECORATION)

            # Cap (cross pattern)
            cap_z = z + height
            grid.set(x, y, cap_z, MaterialType.DECORATION)
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                grid.set(x + dx, y + dy, cap_z, MaterialType.DECORATION)

    def _place_flowers(self, grid: VoxelGrid) -> None:
        """Place flowers in grassy areas."""
        for x in range(0, grid.width, 4):
            for y in range(0, grid.depth, 4):
                # Random offset within cell
                fx = x + self._rng.integers(0, 4)
                fy = y + self._rng.integers(0, 4)

                if fx >= grid.width or fy >= grid.depth:
                    continue

                z = grid.get_surface_height(fx, fy)

                # Flowers only at mid elevations
                if z < 26 or z > 77:
                    continue

                surface = grid.get(fx, fy, z)
                if surface != MaterialType.GRASS:
                    continue

                if self._rng.random() > 0.3:
                    continue

                # Create flower
                height = self._rng.integers(1, 3)
                for h in range(height):
                    grid.set(fx, fy, z + 1 + h, MaterialType.DECORATION)

    def _near_plant(self, x: int, y: int, distance: int) -> bool:
        """Check if position is near a tree."""
        for tx, ty in self._tree_positions:
            if abs(x - tx) <= distance and abs(y - ty) <= distance:
                return True
        return False
