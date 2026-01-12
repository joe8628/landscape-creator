"""Voxel grid data structure for landscape storage."""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Iterator, List, Dict
import math

from .materials import MaterialType, is_solid


@dataclass
class Voxel:
    """Represents a single voxel with its properties.

    Attributes:
        material_type: The material type of this voxel
        x, y, z: Position coordinates in the grid
    """
    material_type: MaterialType
    x: int
    y: int
    z: int

    @property
    def is_solid(self) -> bool:
        """Check if this voxel is solid (not air or water)."""
        return is_solid(self.material_type)

    @property
    def is_empty(self) -> bool:
        """Check if this voxel is empty (air)."""
        return self.material_type == MaterialType.AIR

    @property
    def position(self) -> Tuple[int, int, int]:
        """Get position as tuple."""
        return (self.x, self.y, self.z)


class VoxelGrid:
    """A 3D grid of voxels representing the landscape.

    The grid uses a numpy array internally for efficient storage and
    manipulation. Each voxel stores a material type as a uint8 value.

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

        # Cache for surface heights (invalidated on modification)
        self._surface_cache: Optional[np.ndarray] = None

    # ==================== Basic Operations ====================

    def get(self, x: int, y: int, z: int) -> MaterialType:
        """Get the material type at a position.

        Args:
            x, y, z: Voxel coordinates

        Returns:
            MaterialType at the given position, AIR if out of bounds
        """
        if not self._in_bounds(x, y, z):
            return MaterialType.AIR
        val = self._data[x, y, z]
        return MaterialType(val) if val > 0 else MaterialType.AIR

    def get_voxel(self, x: int, y: int, z: int) -> Voxel:
        """Get a Voxel object at a position.

        Args:
            x, y, z: Voxel coordinates

        Returns:
            Voxel object with material and position data
        """
        return Voxel(
            material_type=self.get(x, y, z),
            x=x, y=y, z=z
        )

    def set(self, x: int, y: int, z: int, material: MaterialType) -> None:
        """Set the material type at a position.

        Args:
            x, y, z: Voxel coordinates
            material: MaterialType to set
        """
        if self._in_bounds(x, y, z):
            self._data[x, y, z] = material.value
            self._surface_cache = None  # Invalidate cache

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
        self._surface_cache = None

    def get_raw_data(self) -> np.ndarray:
        """Get the raw numpy array for direct manipulation.

        Warning: Direct modification bypasses cache invalidation.
        Call invalidate_cache() after direct modifications.
        """
        return self._data

    def invalidate_cache(self) -> None:
        """Invalidate internal caches. Call after direct data modification."""
        self._surface_cache = None

    # ==================== Surface & Height Operations ====================

    def get_surface_height(self, x: int, y: int) -> int:
        """Get the height of the topmost solid voxel at (x, y).

        Args:
            x, y: Horizontal coordinates

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

    def get_surface_material(self, x: int, y: int) -> MaterialType:
        """Get the material at the surface position.

        Args:
            x, y: Horizontal coordinates

        Returns:
            MaterialType at the surface, or AIR if column is empty
        """
        height = self.get_surface_height(x, y)
        return self.get(x, y, height)

    def compute_heightmap(self) -> np.ndarray:
        """Compute a 2D heightmap of the terrain.

        Returns:
            2D numpy array of surface heights
        """
        if self._surface_cache is not None:
            return self._surface_cache.copy()

        heightmap = np.zeros((self.width, self.depth), dtype=np.int32)
        for x in range(self.width):
            for y in range(self.depth):
                heightmap[x, y] = self.get_surface_height(x, y)

        self._surface_cache = heightmap
        return heightmap.copy()

    # ==================== Slope Calculation ====================

    def get_slope_at(self, x: int, y: int) -> float:
        """Calculate the slope angle at a position in degrees.

        Uses the gradient of neighboring surface heights to compute slope.

        Args:
            x, y: Horizontal coordinates

        Returns:
            Slope angle in degrees (0 = flat, 90 = vertical)
        """
        h_center = self.get_surface_height(x, y)

        # Get neighboring heights (use edge values if at boundary)
        h_left = self.get_surface_height(max(0, x - 1), y)
        h_right = self.get_surface_height(min(self.width - 1, x + 1), y)
        h_front = self.get_surface_height(x, max(0, y - 1))
        h_back = self.get_surface_height(x, min(self.depth - 1, y + 1))

        # Calculate gradients
        dx = (h_right - h_left) / 2.0
        dy = (h_back - h_front) / 2.0

        # Magnitude of gradient gives slope
        gradient_magnitude = math.sqrt(dx * dx + dy * dy)

        # Convert to angle (arctan of rise/run, run = 1 voxel)
        slope_radians = math.atan(gradient_magnitude)
        return math.degrees(slope_radians)

    def get_slope_direction(self, x: int, y: int) -> Tuple[float, float]:
        """Get the direction of steepest descent at a position.

        Args:
            x, y: Horizontal coordinates

        Returns:
            Tuple of (dx, dy) normalized direction vector
        """
        h_left = self.get_surface_height(max(0, x - 1), y)
        h_right = self.get_surface_height(min(self.width - 1, x + 1), y)
        h_front = self.get_surface_height(x, max(0, y - 1))
        h_back = self.get_surface_height(x, min(self.depth - 1, y + 1))

        dx = h_left - h_right  # Points downhill
        dy = h_front - h_back

        magnitude = math.sqrt(dx * dx + dy * dy)
        if magnitude > 0:
            return (dx / magnitude, dy / magnitude)
        return (0.0, 0.0)

    # ==================== Neighbor Operations ====================

    def get_neighbors_6(self, x: int, y: int, z: int) -> List[Voxel]:
        """Get the 6 face-adjacent neighbors of a voxel.

        Args:
            x, y, z: Voxel coordinates

        Returns:
            List of up to 6 neighboring Voxel objects
        """
        neighbors = []
        for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
            nx, ny, nz = x + dx, y + dy, z + dz
            if self._in_bounds(nx, ny, nz):
                neighbors.append(self.get_voxel(nx, ny, nz))
        return neighbors

    def get_neighbors_26(self, x: int, y: int, z: int) -> List[Voxel]:
        """Get all 26 neighbors of a voxel (including diagonals).

        Args:
            x, y, z: Voxel coordinates

        Returns:
            List of up to 26 neighboring Voxel objects
        """
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    if dx == 0 and dy == 0 and dz == 0:
                        continue
                    nx, ny, nz = x + dx, y + dy, z + dz
                    if self._in_bounds(nx, ny, nz):
                        neighbors.append(self.get_voxel(nx, ny, nz))
        return neighbors

    def count_solid_neighbors(self, x: int, y: int, z: int) -> int:
        """Count the number of solid neighbors (6-connected).

        Args:
            x, y, z: Voxel coordinates

        Returns:
            Number of solid neighbors (0-6)
        """
        return sum(1 for v in self.get_neighbors_6(x, y, z) if v.is_solid)

    def is_exposed(self, x: int, y: int, z: int) -> bool:
        """Check if a voxel has at least one air neighbor.

        Args:
            x, y, z: Voxel coordinates

        Returns:
            True if the voxel is exposed to air
        """
        if not self.get_voxel(x, y, z).is_solid:
            return False
        return any(v.is_empty for v in self.get_neighbors_6(x, y, z))

    # ==================== Region Operations ====================

    def fill_region(
        self,
        x1: int, y1: int, z1: int,
        x2: int, y2: int, z2: int,
        material: MaterialType
    ) -> None:
        """Fill a rectangular region with a material.

        Args:
            x1, y1, z1: Start corner (inclusive)
            x2, y2, z2: End corner (inclusive)
            material: MaterialType to fill with
        """
        x1, x2 = max(0, min(x1, x2)), min(self.width - 1, max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(self.depth - 1, max(y1, y2))
        z1, z2 = max(0, min(z1, z2)), min(self.height - 1, max(z1, z2))

        self._data[x1:x2+1, y1:y2+1, z1:z2+1] = material.value
        self._surface_cache = None

    def fill_column(self, x: int, y: int, z_start: int, z_end: int, material: MaterialType) -> None:
        """Fill a vertical column with a material.

        Args:
            x, y: Horizontal position
            z_start, z_end: Vertical range (inclusive)
            material: MaterialType to fill with
        """
        if not (0 <= x < self.width and 0 <= y < self.depth):
            return
        z_start = max(0, z_start)
        z_end = min(self.height - 1, z_end)
        self._data[x, y, z_start:z_end+1] = material.value
        self._surface_cache = None

    # ==================== Seamless Tiling ====================

    def get_wrapped(self, x: int, y: int, z: int) -> MaterialType:
        """Get material at position with X/Y wrapping for seamless tiling.

        Args:
            x, y, z: Voxel coordinates (x, y wrap around)

        Returns:
            MaterialType at wrapped position
        """
        x = x % self.width
        y = y % self.depth
        if not (0 <= z < self.height):
            return MaterialType.AIR
        val = self._data[x, y, z]
        return MaterialType(val) if val > 0 else MaterialType.AIR

    def set_wrapped(self, x: int, y: int, z: int, material: MaterialType) -> None:
        """Set material at position with X/Y wrapping for seamless tiling.

        Args:
            x, y, z: Voxel coordinates (x, y wrap around)
            material: MaterialType to set
        """
        x = x % self.width
        y = y % self.depth
        if 0 <= z < self.height:
            self._data[x, y, z] = material.value
            self._surface_cache = None

    # ==================== Statistics ====================

    def count_material(self, material: MaterialType) -> int:
        """Count voxels of a specific material type.

        Args:
            material: MaterialType to count

        Returns:
            Number of voxels with this material
        """
        if material == MaterialType.AIR:
            # AIR is stored as 0 in the array
            return int(np.sum(self._data == 0))
        return int(np.sum(self._data == material.value))

    def get_material_distribution(self) -> Dict[MaterialType, int]:
        """Get the distribution of all material types.

        Returns:
            Dictionary mapping MaterialType to count
        """
        distribution = {}
        # Count AIR (stored as 0)
        air_count = int(np.sum(self._data == 0))
        if air_count > 0:
            distribution[MaterialType.AIR] = air_count

        for material in MaterialType:
            if material == MaterialType.AIR:
                continue  # Already counted
            count = int(np.sum(self._data == material.value))
            if count > 0:
                distribution[material] = count
        return distribution

    def count_solid_voxels(self) -> int:
        """Count all solid (non-air, non-water) voxels.

        Returns:
            Number of solid voxels
        """
        # Count voxels that are not 0 (AIR) and not WATER
        non_air = self._data != 0
        non_water = self._data != MaterialType.WATER.value
        return int(np.sum(non_air & non_water))

    @property
    def total_voxels(self) -> int:
        """Total number of voxels in the grid."""
        return self.width * self.depth * self.height

    # ==================== Copy & Clone ====================

    def copy(self) -> 'VoxelGrid':
        """Create a deep copy of this grid.

        Returns:
            New VoxelGrid with copied data
        """
        new_grid = VoxelGrid(self.width, self.depth, self.height)
        new_grid._data = self._data.copy()
        return new_grid

    def copy_region(
        self,
        x1: int, y1: int, z1: int,
        x2: int, y2: int, z2: int
    ) -> 'VoxelGrid':
        """Copy a rectangular region to a new grid.

        Args:
            x1, y1, z1: Start corner (inclusive)
            x2, y2, z2: End corner (inclusive)

        Returns:
            New VoxelGrid containing the region
        """
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        z1, z2 = min(z1, z2), max(z1, z2)

        width = x2 - x1 + 1
        depth = y2 - y1 + 1
        height = z2 - z1 + 1

        new_grid = VoxelGrid(width, depth, height)
        new_grid._data = self._data[x1:x2+1, y1:y2+1, z1:z2+1].copy()
        return new_grid

    # ==================== Iteration ====================

    def iter_all(self) -> Iterator[Voxel]:
        """Iterate over all voxels in the grid.

        Yields:
            Voxel objects for each position
        """
        for x in range(self.width):
            for y in range(self.depth):
                for z in range(self.height):
                    yield self.get_voxel(x, y, z)

    def iter_solid(self) -> Iterator[Voxel]:
        """Iterate over all solid voxels.

        Yields:
            Voxel objects for solid positions only
        """
        for x in range(self.width):
            for y in range(self.depth):
                for z in range(self.height):
                    voxel = self.get_voxel(x, y, z)
                    if voxel.is_solid:
                        yield voxel

    def iter_surface(self) -> Iterator[Voxel]:
        """Iterate over surface voxels (exposed to air).

        Yields:
            Voxel objects for exposed surface positions
        """
        for x in range(self.width):
            for y in range(self.depth):
                z = self.get_surface_height(x, y)
                if z > 0 or self.get(x, y, 0) != MaterialType.AIR:
                    yield self.get_voxel(x, y, z)

    def iter_material(self, material: MaterialType) -> Iterator[Voxel]:
        """Iterate over voxels of a specific material.

        Args:
            material: MaterialType to filter by

        Yields:
            Voxel objects matching the material
        """
        positions = np.argwhere(self._data == material.value)
        for pos in positions:
            yield Voxel(material, int(pos[0]), int(pos[1]), int(pos[2]))

    # ==================== String Representation ====================

    def __repr__(self) -> str:
        """String representation of the grid."""
        solid = self.count_solid_voxels()
        total = self.total_voxels
        return f"VoxelGrid({self.width}x{self.depth}x{self.height}, {solid}/{total} solid)"
