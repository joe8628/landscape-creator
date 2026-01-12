"""Data export for voxel grids (JSON and binary formats)."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..core.voxel_grid import VoxelGrid
from ..core.materials import MaterialType


class DataExporter:
    """Exports voxel grids to JSON and binary data formats."""

    def export_json(
        self,
        grid: VoxelGrid,
        filepath: str,
        seed: int,
        include_empty: bool = False
    ) -> bool:
        """Export voxel grid to JSON format.

        Args:
            grid: VoxelGrid to export
            filepath: Path for the output JSON file
            seed: Generation seed for metadata
            include_empty: If True, include AIR voxels

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "seed": seed,
                "dimensions": list(grid.get_dimensions()),
                "metadata": {
                    "generation_date": datetime.now().isoformat(),
                    "version": "1.0.0"
                },
                "voxels": []
            }

            raw = grid.get_raw_data()
            width, depth, height = grid.get_dimensions()

            for x in range(width):
                for y in range(depth):
                    for z in range(height):
                        material_val = raw[x, y, z]
                        if material_val == 0 and not include_empty:
                            continue

                        material = MaterialType(material_val) if material_val > 0 else MaterialType.AIR
                        data["voxels"].append({
                            "x": x,
                            "y": y,
                            "z": z,
                            "material": material.name
                        })

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"Exported {len(data['voxels'])} voxels to {filepath}")
            return True

        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def export_binary(self, grid: VoxelGrid, filepath: str, seed: int) -> bool:
        """Export voxel grid to compact binary format.

        Format:
        - Header: 16 bytes (magic, version, seed, dimensions)
        - Data: raw voxel bytes

        Args:
            grid: VoxelGrid to export
            filepath: Path for the output file
            seed: Generation seed

        Returns:
            True if successful, False otherwise
        """
        import struct

        try:
            width, depth, height = grid.get_dimensions()

            with open(filepath, 'wb') as f:
                # Magic number (4 bytes)
                f.write(b'VOXL')

                # Version (2 bytes)
                f.write(struct.pack('<H', 1))

                # Seed (4 bytes)
                f.write(struct.pack('<I', seed))

                # Dimensions (6 bytes: 3 x uint16)
                f.write(struct.pack('<HHH', width, depth, height))

                # Raw voxel data
                f.write(grid.get_raw_data().tobytes())

            print(f"Exported binary data to {filepath}")
            return True

        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def load_binary(self, filepath: str) -> Optional[tuple]:
        """Load voxel grid from binary format.

        Args:
            filepath: Path to the binary file

        Returns:
            Tuple of (VoxelGrid, seed) or None if failed
        """
        import struct
        import numpy as np

        try:
            with open(filepath, 'rb') as f:
                # Check magic
                magic = f.read(4)
                if magic != b'VOXL':
                    print("Invalid file format")
                    return None

                # Read header
                version = struct.unpack('<H', f.read(2))[0]
                seed = struct.unpack('<I', f.read(4))[0]
                width, depth, height = struct.unpack('<HHH', f.read(6))

                # Read data
                data = np.frombuffer(f.read(), dtype=np.uint8)
                data = data.reshape((width, depth, height))

                # Create grid
                grid = VoxelGrid(width, depth, height)
                grid._data = data

                return grid, seed

        except Exception as e:
            print(f"Load failed: {e}")
            return None
