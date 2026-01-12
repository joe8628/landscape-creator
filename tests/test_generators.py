"""Tests for landscape generators."""

import unittest
from src.core.voxel_grid import VoxelGrid
from src.core.materials import MaterialType
from src.generators.terrain_generator import TerrainGenerator


class TestVoxelGrid(unittest.TestCase):
    """Tests for VoxelGrid class."""

    def test_create_default_grid(self):
        """Test creating a grid with default dimensions."""
        grid = VoxelGrid()
        self.assertEqual(grid.get_dimensions(), (256, 256, 128))

    def test_create_custom_grid(self):
        """Test creating a grid with custom dimensions."""
        grid = VoxelGrid(64, 64, 32)
        self.assertEqual(grid.get_dimensions(), (64, 64, 32))

    def test_set_and_get_voxel(self):
        """Test setting and getting voxel values."""
        grid = VoxelGrid(16, 16, 16)
        grid.set(5, 5, 5, MaterialType.STONE)
        self.assertEqual(grid.get(5, 5, 5), MaterialType.STONE)

    def test_out_of_bounds_returns_air(self):
        """Test that out-of-bounds access returns AIR."""
        grid = VoxelGrid(16, 16, 16)
        self.assertEqual(grid.get(100, 100, 100), MaterialType.AIR)

    def test_clear_grid(self):
        """Test clearing the grid."""
        grid = VoxelGrid(16, 16, 16)
        grid.set(5, 5, 5, MaterialType.STONE)
        grid.clear()
        self.assertEqual(grid.get(5, 5, 5), MaterialType.AIR)


class TestTerrainGenerator(unittest.TestCase):
    """Tests for TerrainGenerator class."""

    def test_deterministic_generation(self):
        """Test that same seed produces same result."""
        grid1 = VoxelGrid(32, 32, 32)
        grid2 = VoxelGrid(32, 32, 32)

        gen1 = TerrainGenerator(42)
        gen2 = TerrainGenerator(42)

        gen1.generate(grid1)
        gen2.generate(grid2)

        # Compare a sample of voxels
        for x in range(0, 32, 4):
            for y in range(0, 32, 4):
                for z in range(0, 32, 4):
                    self.assertEqual(grid1.get(x, y, z), grid2.get(x, y, z))

    def test_different_seeds_differ(self):
        """Test that different seeds produce different results."""
        grid1 = VoxelGrid(32, 32, 64)
        grid2 = VoxelGrid(32, 32, 64)

        TerrainGenerator(42).generate(grid1)
        TerrainGenerator(123).generate(grid2)

        # Compare surface heights - at least some should differ
        differences = 0
        for x in range(0, 32, 2):
            for y in range(0, 32, 2):
                h1 = grid1.get_surface_height(x, y)
                h2 = grid2.get_surface_height(x, y)
                if h1 != h2:
                    differences += 1

        self.assertGreater(differences, 0)


if __name__ == '__main__':
    unittest.main()
