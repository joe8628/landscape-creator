"""Terrain generation with hills, valleys, mountains, water, and caves."""

import numpy as np
from typing import Optional

from ..core.voxel_grid import VoxelGrid
from ..core.materials import MaterialType
from ..core.noise_generator import NoiseGenerator


class TerrainGenerator:
    """Generates terrain features including heightmap and caves.

    Creates realistic geological features:
    - Hills (gentle slopes < 30 degrees)
    - Valleys (depressions between hills)
    - Mountains (steep slopes 30-70 degrees)
    - Cliffs (near-vertical faces > 70 degrees)
    - Water bodies (lakes at low elevations)
    - Caves (3D volumetric carved spaces)
    """

    # Height distribution percentages (of 128 max height)
    BASE_TERRAIN_MAX = 51      # 0-40% for base terrain
    HILL_MIN = 26              # 20%
    HILL_MAX = 77              # 60%
    MOUNTAIN_MIN = 77          # 60%
    MOUNTAIN_MAX = 122         # 95%
    WATER_LEVEL_DEFAULT = 26   # ~20% of max height

    # Material layer thicknesses
    DIRT_LAYER_THICKNESS = 3
    SAND_BEACH_WIDTH = 10
    SNOW_LINE = 115            # 90% of max height

    def __init__(self, seed: int):
        """Initialize terrain generator with a seed.

        Args:
            seed: Integer seed for reproducible generation
        """
        self.seed = seed
        self.noise = NoiseGenerator(seed)
        self._rng = np.random.default_rng(seed)

        # Randomize parameters within realistic ranges
        self.water_level = self._rng.integers(19, 33)  # 15-25% of height

    def generate(self, grid: VoxelGrid) -> None:
        """Generate terrain into the provided voxel grid.

        Args:
            grid: VoxelGrid to fill with terrain
        """
        # Step 1: Generate base heightmap
        heightmap = self._generate_heightmap(grid.width, grid.depth)

        # Step 2: Fill terrain based on heightmap
        self._fill_terrain(grid, heightmap)

        # Step 3: Add water
        self._add_water(grid)

        # Step 4: Carve caves (volumetric 3D)
        self._carve_caves(grid)

    def _generate_heightmap(self, width: int, depth: int) -> np.ndarray:
        """Generate a 2D heightmap using multi-octave noise.

        Args:
            width, depth: Dimensions of the heightmap

        Returns:
            2D numpy array of height values
        """
        heightmap = np.zeros((width, depth), dtype=np.float32)

        for x in range(width):
            for y in range(depth):
                # Continental scale (large features)
                continental = self.noise.noise_2d(x, y, octaves=2, scale=200.0)

                # Mountain ranges
                mountain = self.noise.noise_2d(x, y, octaves=4, scale=80.0)
                mountain = max(0, mountain) ** 2  # Only positive, squared for peaks

                # Local detail
                detail = self.noise.noise_2d(x, y, octaves=6, scale=30.0)

                # Combine layers
                height = (
                    (continental * 0.4 + 0.5) * self.BASE_TERRAIN_MAX +
                    mountain * 60 +
                    detail * 10
                )

                # Clamp to valid range
                heightmap[x, y] = np.clip(height, 1, 127)

        return heightmap

    def _fill_terrain(self, grid: VoxelGrid, heightmap: np.ndarray) -> None:
        """Fill the voxel grid based on heightmap.

        Args:
            grid: VoxelGrid to fill
            heightmap: 2D height values
        """
        for x in range(grid.width):
            for y in range(grid.depth):
                surface_height = int(heightmap[x, y])

                for z in range(surface_height + 1):
                    material = self._get_material_for_position(x, y, z, surface_height)
                    grid.set(x, y, z, material)

    def _get_material_for_position(
        self,
        x: int,
        y: int,
        z: int,
        surface_height: int
    ) -> MaterialType:
        """Determine material type based on position and height.

        Args:
            x, y, z: Voxel coordinates
            surface_height: Height of the surface at this (x, y)

        Returns:
            Appropriate MaterialType
        """
        depth_from_surface = surface_height - z

        # Snow at high elevations
        if z >= self.SNOW_LINE and depth_from_surface < 2:
            return MaterialType.SNOW

        # Surface layers
        if depth_from_surface == 0:
            # Top surface
            if z <= self.water_level + 3:
                return MaterialType.SAND  # Beach
            else:
                return MaterialType.GRASS
        elif depth_from_surface < self.DIRT_LAYER_THICKNESS:
            # Dirt layer below surface
            if z <= self.water_level + 3:
                return MaterialType.SAND
            else:
                return MaterialType.DIRT
        else:
            # Deep underground
            return MaterialType.STONE

    def _add_water(self, grid: VoxelGrid) -> None:
        """Add water to all empty spaces below water level.

        Args:
            grid: VoxelGrid to add water to
        """
        for x in range(grid.width):
            for y in range(grid.depth):
                for z in range(self.water_level + 1):
                    if grid.get(x, y, z) == MaterialType.AIR:
                        grid.set(x, y, z, MaterialType.WATER)

    def _carve_caves(self, grid: VoxelGrid) -> None:
        """Carve caves using 3D noise.

        Args:
            grid: VoxelGrid to carve caves in
        """
        cave_threshold = 0.6  # Higher = fewer caves

        for x in range(grid.width):
            for y in range(grid.depth):
                surface_height = grid.get_surface_height(x, y)

                # Only carve below surface, not too deep
                max_cave_depth = min(surface_height - 5, 77)  # 60% of height
                min_cave_depth = 13  # 10% of height

                if max_cave_depth <= min_cave_depth:
                    continue

                for z in range(min_cave_depth, max_cave_depth):
                    noise_val = self.noise.noise_3d(
                        x, y, z,
                        octaves=3,
                        scale=20.0
                    )

                    if noise_val > cave_threshold:
                        # Carve out cave, but not if it's under water
                        if z > self.water_level:
                            grid.set(x, y, z, MaterialType.AIR)
