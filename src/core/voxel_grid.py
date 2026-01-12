"""Voxel grid data structure for landscape storage."""

import numpy as np
from typing import Optional, Tuple

from .materials import MaterialType


class VoxelGrid:
    """A 3D grid of voxels representing the landscape.

    Attributes:
        width: Grid width (X dimension), default 256
        depth: Grid depth (Y dimension), default 256
        height: Grid height (Z dimension), default 128
    """

    # Grid dimensions (fixed as per requirements)
    DEFAULT_WIDTH = 256
    DEFAULT_DEPTH = 256
    DEFAULT_HEIGHT = 128

    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        depth: int = DEFAULT_DEPTH,
        height: int = DEFAULT_HEIGHT
    ):
        """Initialize an empty voxel grid.

        Args:
            width: Grid width (X dimension)
            depth: Grid depth (Y dimension)
            height: Grid height (Z dimension)
        """
        self.width = width
        self.depth = depth
        self.height = height

        # Store material types as uint8 (0-255, enough for MaterialType enum)
        self._data = np.zeros((width, depth, height), dtype=np.uint8)

    def get(self, x: int, y: int, z: int) -> MaterialType:
        """Get the material type at a position.

        Args:
            x, y, z: Voxel coordinates

        Returns:
            MaterialType at the given position
        """
        if not self._in_bounds(x, y, z):
            return MaterialType.AIR
        return MaterialType(self._data[x, y, z]) if self._data[x, y, z] > 0 else MaterialType.AIR

    def set(self, x: int, y: int, z: int, material: MaterialType) -> None:
        """Set the material type at a position.

        Args:
            x, y, z: Voxel coordinates
            material: MaterialType to set
        """
        if self._in_bounds(x, y, z):
            self._data[x, y, z] = material.value

    def _in_bounds(self, x: int, y: int, z: int) -> bool:
        """Check if coordinates are within grid bounds."""
        return (0 <= x < self.width and
                0 <= y < self.depth and
                0 <= z < self.height)

    def get_dimensions(self) -> Tuple[int, int, int]:
        """Get grid dimensions as (width, depth, height)."""
        return (self.width, self.depth, self.height)

    def clear(self) -> None:
        """Clear the grid, setting all voxels to AIR."""
        self._data.fill(0)

    def get_raw_data(self) -> np.ndarray:
        """Get the raw numpy array for direct manipulation."""
        return self._data

    def get_surface_height(self, x: int, y: int) -> int:
        """Get the height of the topmost solid voxel at (x, y).

        Returns:
            Height of topmost solid voxel, or 0 if column is empty
        """
        if not (0 <= x < self.width and 0 <= y < self.depth):
            return 0

        for z in range(self.height - 1, -1, -1):
            material = self.get(x, y, z)
            if material not in (MaterialType.AIR, MaterialType.WATER):
                return z
        return 0
