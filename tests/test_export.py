"""Tests for export modules."""

import os
import json
import tempfile
import unittest

from src.core.voxel_grid import VoxelGrid
from src.core.materials import MaterialType
from src.export.data_exporter import DataExporter


class TestDataExporter(unittest.TestCase):
    """Tests for DataExporter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.grid = VoxelGrid(8, 8, 8)
        # Add some test data
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    self.grid.set(x, y, z, MaterialType.STONE)
        self.exporter = DataExporter()

    def test_export_json(self):
        """Test JSON export creates valid file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            result = self.exporter.export_json(self.grid, filepath, seed=42)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(filepath))

            # Verify JSON structure
            with open(filepath) as f:
                data = json.load(f)

            self.assertEqual(data['seed'], 42)
            self.assertEqual(data['dimensions'], [8, 8, 8])
            self.assertIn('voxels', data)
            self.assertIn('metadata', data)
        finally:
            os.unlink(filepath)

    def test_export_binary(self):
        """Test binary export creates valid file."""
        with tempfile.NamedTemporaryFile(suffix='.voxel', delete=False) as f:
            filepath = f.name

        try:
            result = self.exporter.export_binary(self.grid, filepath, seed=42)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(filepath))

            # File should have content
            self.assertGreater(os.path.getsize(filepath), 0)
        finally:
            os.unlink(filepath)

    def test_binary_roundtrip(self):
        """Test that binary export/import preserves data."""
        with tempfile.NamedTemporaryFile(suffix='.voxel', delete=False) as f:
            filepath = f.name

        try:
            self.exporter.export_binary(self.grid, filepath, seed=42)
            result = self.exporter.load_binary(filepath)

            self.assertIsNotNone(result)
            loaded_grid, seed = result

            self.assertEqual(seed, 42)
            self.assertEqual(loaded_grid.get_dimensions(), self.grid.get_dimensions())

            # Verify voxel data matches
            for x in range(8):
                for y in range(8):
                    for z in range(8):
                        self.assertEqual(
                            loaded_grid.get(x, y, z),
                            self.grid.get(x, y, z)
                        )
        finally:
            os.unlink(filepath)


if __name__ == '__main__':
    unittest.main()
