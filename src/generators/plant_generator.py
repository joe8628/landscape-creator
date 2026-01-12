"""Plant generation with trees, grass, and bushes."""

import numpy as np
from typing import List, Tuple, Optional

from ..core.voxel_grid import VoxelGrid
from ..core.materials import MaterialType


class PlantGenerator:
    """Generates vegetation including trees, grass, and bushes.

    Plant types:
    - Trees: Pine (conical), Oak (rounded), Palm (thin with crown)
    - Grass: Short (1 voxel), Tall (2-3 voxels)
    - Bushes: Small (3x3x2), Large (5x5x3)
    """

    def __init__(self, seed: int):
        """Initialize plant generator with a seed.

        Args:
            seed: Integer seed for reproducible generation
        """
        self.seed = seed
        self._rng = np.random.default_rng(seed)

        # Placement tracking to prevent overlap
        self._occupied_positions: set = set()

    def generate(self, grid: VoxelGrid) -> None:
        """Generate plants on the terrain.

        Args:
            grid: VoxelGrid with existing terrain to add plants to
        """
        self._occupied_positions.clear()

        # Generate in order: trees first (largest), then bushes, then grass
        self._place_trees(grid)
        self._place_bushes(grid)
        self._place_grass(grid)

    def _place_trees(self, grid: VoxelGrid) -> None:
        """Place trees on suitable terrain."""
        # Grid-based placement (8x8 cells)
        cell_size = 8

        for cx in range(0, grid.width, cell_size):
            for cy in range(0, grid.depth, cell_size):
                # Random position within cell
                x = cx + self._rng.integers(0, cell_size)
                y = cy + self._rng.integers(0, cell_size)

                if x >= grid.width or y >= grid.depth:
                    continue

                z = grid.get_surface_height(x, y)

                if self._can_place_tree(grid, x, y, z):
                    tree_type = self._select_tree_type(z)
                    if tree_type is not None:
                        self._create_tree(grid, x, y, z + 1, tree_type)

    def _can_place_tree(self, grid: VoxelGrid, x: int, y: int, z: int) -> bool:
        """Check if a tree can be placed at this location."""
        # Check surface material
        surface = grid.get(x, y, z)
        if surface not in (MaterialType.GRASS, MaterialType.DIRT, MaterialType.SAND):
            return False

        # Check height constraints (10-95% of max height)
        if z < 13 or z > 122:
            return False

        # Check for overlap with existing plants
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if (x + dx, y + dy) in self._occupied_positions:
                    return False

        # Random chance based on height
        placement_chance = 0.3 if z < 77 else 0.15
        return self._rng.random() < placement_chance

    def _select_tree_type(self, height: int) -> Optional[str]:
        """Select tree type based on elevation."""
        if height < 51:  # Low elevation (palm zone)
            return self._rng.choice(["palm", "oak"], p=[0.4, 0.6])
        elif height < 90:  # Mid elevation
            return "oak"
        elif height < 115:  # High elevation
            return "pine"
        return None  # Too high for trees

    def _create_tree(self, grid: VoxelGrid, x: int, y: int, z: int, tree_type: str) -> None:
        """Create a tree at the specified position."""
        # Mark position as occupied
        self._occupied_positions.add((x, y))

        if tree_type == "pine":
            self._create_pine_tree(grid, x, y, z)
        elif tree_type == "oak":
            self._create_oak_tree(grid, x, y, z)
        elif tree_type == "palm":
            self._create_palm_tree(grid, x, y, z)

    def _create_pine_tree(self, grid: VoxelGrid, x: int, y: int, z: int) -> None:
        """Create a conical pine tree."""
        height = self._rng.integers(8, 16)

        # Trunk
        for h in range(height):
            grid.set(x, y, z + h, MaterialType.WOOD)

        # Foliage (conical layers)
        foliage_start = height // 3
        layer_size = 1

        for h in range(height - 1, foliage_start, -1):
            radius = min(layer_size, 3)
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) <= radius + 1:
                        grid.set(x + dx, y + dy, z + h, MaterialType.LEAVES)
            layer_size += 0.5

    def _create_oak_tree(self, grid: VoxelGrid, x: int, y: int, z: int) -> None:
        """Create a rounded oak tree."""
        height = self._rng.integers(6, 13)

        # Trunk
        trunk_height = height // 2
        for h in range(trunk_height):
            grid.set(x, y, z + h, MaterialType.WOOD)

        # Foliage (rounded blob)
        foliage_radius = self._rng.integers(2, 4)
        foliage_center_z = z + trunk_height + foliage_radius - 1

        for dx in range(-foliage_radius, foliage_radius + 1):
            for dy in range(-foliage_radius, foliage_radius + 1):
                for dz in range(-foliage_radius, foliage_radius + 1):
                    dist = (dx**2 + dy**2 + dz**2) ** 0.5
                    if dist <= foliage_radius + self._rng.random() * 0.5:
                        fz = foliage_center_z + dz
                        if fz >= z + trunk_height:
                            grid.set(x + dx, y + dy, fz, MaterialType.LEAVES)

    def _create_palm_tree(self, grid: VoxelGrid, x: int, y: int, z: int) -> None:
        """Create a palm tree with crown."""
        height = self._rng.integers(10, 19)

        # Trunk
        for h in range(height):
            grid.set(x, y, z + h, MaterialType.WOOD)

        # Crown (cross pattern at top)
        top_z = z + height
        for direction in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            for dist in range(1, 4):
                dx, dy = direction[0] * dist, direction[1] * dist
                dz = -dist // 2  # Drooping effect
                grid.set(x + dx, y + dy, top_z + dz, MaterialType.LEAVES)
        grid.set(x, y, top_z, MaterialType.LEAVES)

    def _place_bushes(self, grid: VoxelGrid) -> None:
        """Place bushes on suitable terrain."""
        for _ in range(grid.width * grid.depth // 100):
            x = self._rng.integers(0, grid.width)
            y = self._rng.integers(0, grid.depth)
            z = grid.get_surface_height(x, y)

            if self._can_place_bush(grid, x, y, z):
                size = "large" if self._rng.random() > 0.6 else "small"
                self._create_bush(grid, x, y, z + 1, size)

    def _can_place_bush(self, grid: VoxelGrid, x: int, y: int, z: int) -> bool:
        """Check if a bush can be placed here."""
        surface = grid.get(x, y, z)
        if surface not in (MaterialType.GRASS, MaterialType.DIRT):
            return False

        if z < 26 or z > 77:
            return False

        if (x, y) in self._occupied_positions:
            return False

        return self._rng.random() < 0.3

    def _create_bush(self, grid: VoxelGrid, x: int, y: int, z: int, size: str) -> None:
        """Create a bush."""
        self._occupied_positions.add((x, y))

        radius = 2 if size == "large" else 1
        height = 3 if size == "large" else 2

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for dz in range(height):
                    if abs(dx) + abs(dy) + dz <= radius + height - 1:
                        grid.set(x + dx, y + dy, z + dz, MaterialType.LEAVES)

    def _place_grass(self, grid: VoxelGrid) -> None:
        """Place grass patches on suitable terrain."""
        for x in range(grid.width):
            for y in range(grid.depth):
                z = grid.get_surface_height(x, y)

                if self._can_place_grass(grid, x, y, z):
                    height = 1 if self._rng.random() > 0.2 else self._rng.integers(2, 4)
                    for h in range(height):
                        if grid.get(x, y, z + 1 + h) == MaterialType.AIR:
                            grid.set(x, y, z + 1 + h, MaterialType.GRASS)

    def _can_place_grass(self, grid: VoxelGrid, x: int, y: int, z: int) -> bool:
        """Check if grass can be placed here."""
        surface = grid.get(x, y, z)
        if surface != MaterialType.GRASS:
            return False

        if z < 13 or z > 102:
            return False

        if (x, y) in self._occupied_positions:
            return False

        return self._rng.random() < 0.4
