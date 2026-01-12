"""Comprehensive tests for VoxelGrid and Voxel classes."""

import unittest
import numpy as np
from src.core.voxel_grid import VoxelGrid, Voxel
from src.core.materials import MaterialType


class TestVoxel(unittest.TestCase):
    """Tests for Voxel dataclass."""

    def test_voxel_creation(self):
        """Test creating a voxel."""
        voxel = Voxel(MaterialType.STONE, 1, 2, 3)
        self.assertEqual(voxel.material_type, MaterialType.STONE)
        self.assertEqual(voxel.x, 1)
        self.assertEqual(voxel.y, 2)
        self.assertEqual(voxel.z, 3)

    def test_voxel_is_solid(self):
        """Test is_solid property."""
        stone = Voxel(MaterialType.STONE, 0, 0, 0)
        air = Voxel(MaterialType.AIR, 0, 0, 0)
        water = Voxel(MaterialType.WATER, 0, 0, 0)

        self.assertTrue(stone.is_solid)
        self.assertFalse(air.is_solid)
        self.assertFalse(water.is_solid)

    def test_voxel_is_empty(self):
        """Test is_empty property."""
        air = Voxel(MaterialType.AIR, 0, 0, 0)
        stone = Voxel(MaterialType.STONE, 0, 0, 0)

        self.assertTrue(air.is_empty)
        self.assertFalse(stone.is_empty)

    def test_voxel_position(self):
        """Test position property."""
        voxel = Voxel(MaterialType.DIRT, 5, 10, 15)
        self.assertEqual(voxel.position, (5, 10, 15))


class TestVoxelGridBasic(unittest.TestCase):
    """Basic tests for VoxelGrid class."""

    def test_create_default_grid(self):
        """Test creating grid with default dimensions."""
        grid = VoxelGrid()
        self.assertEqual(grid.get_dimensions(), (256, 256, 128))

    def test_create_custom_grid(self):
        """Test creating grid with custom dimensions."""
        grid = VoxelGrid(32, 64, 16)
        self.assertEqual(grid.get_dimensions(), (32, 64, 16))

    def test_set_and_get(self):
        """Test basic set and get operations."""
        grid = VoxelGrid(16, 16, 16)
        grid.set(5, 5, 5, MaterialType.STONE)
        self.assertEqual(grid.get(5, 5, 5), MaterialType.STONE)

    def test_get_voxel(self):
        """Test get_voxel returns proper Voxel object."""
        grid = VoxelGrid(16, 16, 16)
        grid.set(3, 4, 5, MaterialType.DIRT)
        voxel = grid.get_voxel(3, 4, 5)

        self.assertIsInstance(voxel, Voxel)
        self.assertEqual(voxel.material_type, MaterialType.DIRT)
        self.assertEqual(voxel.position, (3, 4, 5))

    def test_out_of_bounds_returns_air(self):
        """Test out of bounds access returns AIR."""
        grid = VoxelGrid(16, 16, 16)
        self.assertEqual(grid.get(100, 0, 0), MaterialType.AIR)
        self.assertEqual(grid.get(-1, 0, 0), MaterialType.AIR)

    def test_clear(self):
        """Test clearing the grid."""
        grid = VoxelGrid(16, 16, 16)
        grid.set(5, 5, 5, MaterialType.STONE)
        grid.clear()
        self.assertEqual(grid.get(5, 5, 5), MaterialType.AIR)

    def test_repr(self):
        """Test string representation."""
        grid = VoxelGrid(16, 16, 16)
        repr_str = repr(grid)
        self.assertIn("16x16x16", repr_str)


class TestVoxelGridSurface(unittest.TestCase):
    """Tests for surface-related operations."""

    def setUp(self):
        """Set up test grid with terrain."""
        self.grid = VoxelGrid(16, 16, 32)
        # Create a simple terrain: stone base with dirt on top
        for x in range(16):
            for y in range(16):
                for z in range(10):
                    self.grid.set(x, y, z, MaterialType.STONE)
                self.grid.set(x, y, 10, MaterialType.DIRT)

    def test_get_surface_height(self):
        """Test getting surface height."""
        self.assertEqual(self.grid.get_surface_height(5, 5), 10)

    def test_get_surface_material(self):
        """Test getting surface material."""
        self.assertEqual(self.grid.get_surface_material(5, 5), MaterialType.DIRT)

    def test_compute_heightmap(self):
        """Test computing heightmap."""
        heightmap = self.grid.compute_heightmap()
        self.assertEqual(heightmap.shape, (16, 16))
        self.assertEqual(heightmap[5, 5], 10)


class TestVoxelGridSlope(unittest.TestCase):
    """Tests for slope calculations."""

    def test_flat_terrain_zero_slope(self):
        """Test that flat terrain has zero slope."""
        grid = VoxelGrid(16, 16, 32)
        for x in range(16):
            for y in range(16):
                grid.set(x, y, 10, MaterialType.STONE)

        slope = grid.get_slope_at(8, 8)
        self.assertAlmostEqual(slope, 0.0, places=1)

    def test_sloped_terrain(self):
        """Test slope calculation on inclined terrain."""
        grid = VoxelGrid(16, 16, 32)
        for x in range(16):
            for y in range(16):
                # Create a slope in x direction
                height = 5 + x
                for z in range(height + 1):
                    grid.set(x, y, z, MaterialType.STONE)

        slope = grid.get_slope_at(8, 8)
        self.assertGreater(slope, 0)

    def test_slope_direction(self):
        """Test slope direction calculation."""
        grid = VoxelGrid(16, 16, 32)
        for x in range(16):
            for y in range(16):
                height = 10 + x  # Higher on positive x
                for z in range(height + 1):
                    grid.set(x, y, z, MaterialType.STONE)

        dx, dy = grid.get_slope_direction(8, 8)
        # Should point in negative x direction (downhill)
        self.assertLess(dx, 0)


class TestVoxelGridNeighbors(unittest.TestCase):
    """Tests for neighbor operations."""

    def setUp(self):
        """Set up test grid."""
        self.grid = VoxelGrid(16, 16, 16)
        self.grid.set(5, 5, 5, MaterialType.STONE)

    def test_get_neighbors_6(self):
        """Test getting 6 face-adjacent neighbors."""
        neighbors = self.grid.get_neighbors_6(5, 5, 5)
        self.assertEqual(len(neighbors), 6)

    def test_get_neighbors_26(self):
        """Test getting all 26 neighbors."""
        neighbors = self.grid.get_neighbors_26(5, 5, 5)
        self.assertEqual(len(neighbors), 26)

    def test_neighbors_at_edge(self):
        """Test neighbors at grid edge."""
        neighbors = self.grid.get_neighbors_6(0, 0, 0)
        self.assertEqual(len(neighbors), 3)  # Only 3 valid neighbors at corner

    def test_count_solid_neighbors(self):
        """Test counting solid neighbors."""
        # Surround center voxel with stone
        for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0)]:
            self.grid.set(5+dx, 5+dy, 5+dz, MaterialType.STONE)

        count = self.grid.count_solid_neighbors(5, 5, 5)
        self.assertEqual(count, 3)

    def test_is_exposed(self):
        """Test checking if voxel is exposed."""
        # Single stone voxel is exposed
        self.assertTrue(self.grid.is_exposed(5, 5, 5))

        # Surround with stone
        for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
            self.grid.set(5+dx, 5+dy, 5+dz, MaterialType.STONE)

        # Now not exposed
        self.assertFalse(self.grid.is_exposed(5, 5, 5))


class TestVoxelGridRegion(unittest.TestCase):
    """Tests for region operations."""

    def test_fill_region(self):
        """Test filling a rectangular region."""
        grid = VoxelGrid(16, 16, 16)
        grid.fill_region(2, 2, 2, 5, 5, 5, MaterialType.STONE)

        # Check inside region
        self.assertEqual(grid.get(3, 3, 3), MaterialType.STONE)
        # Check outside region
        self.assertEqual(grid.get(1, 1, 1), MaterialType.AIR)

    def test_fill_column(self):
        """Test filling a vertical column."""
        grid = VoxelGrid(16, 16, 16)
        grid.fill_column(5, 5, 0, 10, MaterialType.STONE)

        for z in range(11):
            self.assertEqual(grid.get(5, 5, z), MaterialType.STONE)
        self.assertEqual(grid.get(5, 5, 11), MaterialType.AIR)


class TestVoxelGridTiling(unittest.TestCase):
    """Tests for seamless tiling operations."""

    def test_get_wrapped(self):
        """Test wrapped get operation."""
        grid = VoxelGrid(16, 16, 16)
        grid.set(0, 0, 5, MaterialType.STONE)

        # Access with wrapping
        self.assertEqual(grid.get_wrapped(16, 0, 5), MaterialType.STONE)
        self.assertEqual(grid.get_wrapped(-16, 0, 5), MaterialType.STONE)

    def test_set_wrapped(self):
        """Test wrapped set operation."""
        grid = VoxelGrid(16, 16, 16)
        grid.set_wrapped(16, 0, 5, MaterialType.STONE)

        # Should have set at (0, 0, 5)
        self.assertEqual(grid.get(0, 0, 5), MaterialType.STONE)


class TestVoxelGridStatistics(unittest.TestCase):
    """Tests for statistics methods."""

    def setUp(self):
        """Set up test grid with known contents."""
        self.grid = VoxelGrid(8, 8, 8)
        # Fill bottom half with stone
        for x in range(8):
            for y in range(8):
                for z in range(4):
                    self.grid.set(x, y, z, MaterialType.STONE)

    def test_count_material(self):
        """Test counting specific material."""
        count = self.grid.count_material(MaterialType.STONE)
        self.assertEqual(count, 8 * 8 * 4)

    def test_get_material_distribution(self):
        """Test getting material distribution."""
        dist = self.grid.get_material_distribution()
        self.assertIn(MaterialType.STONE, dist)
        self.assertEqual(dist[MaterialType.STONE], 8 * 8 * 4)

    def test_count_solid_voxels(self):
        """Test counting solid voxels."""
        count = self.grid.count_solid_voxels()
        self.assertEqual(count, 8 * 8 * 4)

    def test_total_voxels(self):
        """Test total voxels property."""
        self.assertEqual(self.grid.total_voxels, 8 * 8 * 8)


class TestVoxelGridCopy(unittest.TestCase):
    """Tests for copy operations."""

    def test_copy(self):
        """Test deep copying grid."""
        grid = VoxelGrid(8, 8, 8)
        grid.set(4, 4, 4, MaterialType.STONE)

        copy = grid.copy()
        self.assertEqual(copy.get(4, 4, 4), MaterialType.STONE)

        # Modify original
        grid.set(4, 4, 4, MaterialType.DIRT)
        # Copy should be unchanged
        self.assertEqual(copy.get(4, 4, 4), MaterialType.STONE)

    def test_copy_region(self):
        """Test copying a region."""
        grid = VoxelGrid(16, 16, 16)
        grid.fill_region(4, 4, 4, 7, 7, 7, MaterialType.STONE)

        region = grid.copy_region(4, 4, 4, 7, 7, 7)
        self.assertEqual(region.get_dimensions(), (4, 4, 4))
        self.assertEqual(region.get(0, 0, 0), MaterialType.STONE)


class TestVoxelGridIteration(unittest.TestCase):
    """Tests for iteration methods."""

    def setUp(self):
        """Set up small test grid."""
        self.grid = VoxelGrid(4, 4, 4)
        self.grid.set(1, 1, 1, MaterialType.STONE)
        self.grid.set(2, 2, 2, MaterialType.DIRT)

    def test_iter_solid(self):
        """Test iterating over solid voxels."""
        solid_voxels = list(self.grid.iter_solid())
        self.assertEqual(len(solid_voxels), 2)

    def test_iter_material(self):
        """Test iterating over specific material."""
        stone_voxels = list(self.grid.iter_material(MaterialType.STONE))
        self.assertEqual(len(stone_voxels), 1)
        self.assertEqual(stone_voxels[0].position, (1, 1, 1))

    def test_iter_surface(self):
        """Test iterating over surface voxels."""
        # Create a simple terrain
        grid = VoxelGrid(4, 4, 8)
        for x in range(4):
            for y in range(4):
                grid.set(x, y, 0, MaterialType.STONE)

        surface_voxels = list(grid.iter_surface())
        self.assertEqual(len(surface_voxels), 16)  # 4x4 surface


if __name__ == '__main__':
    unittest.main()
