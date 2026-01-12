"""PLY format exporter with vertex colors."""

from pathlib import Path

from ..core.voxel_grid import VoxelGrid
from ..rendering.mesh_builder import MeshBuilder


class PLYExporter:
    """Exports voxel grids to PLY format with vertex colors."""

    def __init__(self):
        """Initialize the PLY exporter."""
        self._mesh_builder = MeshBuilder()

    def export(self, grid: VoxelGrid, filepath: str, binary: bool = True) -> bool:
        """Export voxel grid to PLY file.

        Args:
            grid: VoxelGrid to export
            filepath: Path for the output PLY file
            binary: If True, write binary PLY; otherwise ASCII

        Returns:
            True if successful, False otherwise
        """
        try:
            vertices, faces, colors = self._mesh_builder.build_mesh(grid)

            if len(vertices) == 0:
                print("No mesh data to export.")
                return False

            if binary:
                self._write_binary_ply(filepath, vertices, faces, colors)
            else:
                self._write_ascii_ply(filepath, vertices, faces, colors)

            print(f"Exported to {filepath}")
            return True

        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def _write_ascii_ply(self, filepath: str, vertices, faces, colors) -> None:
        """Write ASCII PLY file."""
        with open(filepath, 'w') as f:
            # Header
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(vertices)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("property uchar red\n")
            f.write("property uchar green\n")
            f.write("property uchar blue\n")
            f.write(f"element face {len(faces)}\n")
            f.write("property list uchar int vertex_indices\n")
            f.write("end_header\n")

            # Vertices with colors
            for i, v in enumerate(vertices):
                r, g, b = int(colors[i][0] * 255), int(colors[i][1] * 255), int(colors[i][2] * 255)
                f.write(f"{v[0]:.4f} {v[1]:.4f} {v[2]:.4f} {r} {g} {b}\n")

            # Faces
            for face in faces:
                f.write(f"3 {face[0]} {face[1]} {face[2]}\n")

    def _write_binary_ply(self, filepath: str, vertices, faces, colors) -> None:
        """Write binary PLY file."""
        import struct

        with open(filepath, 'wb') as f:
            # Header (ASCII)
            header = (
                "ply\n"
                "format binary_little_endian 1.0\n"
                f"element vertex {len(vertices)}\n"
                "property float x\n"
                "property float y\n"
                "property float z\n"
                "property uchar red\n"
                "property uchar green\n"
                "property uchar blue\n"
                f"element face {len(faces)}\n"
                "property list uchar int vertex_indices\n"
                "end_header\n"
            )
            f.write(header.encode('ascii'))

            # Vertices with colors (binary)
            for i, v in enumerate(vertices):
                r = int(colors[i][0] * 255)
                g = int(colors[i][1] * 255)
                b = int(colors[i][2] * 255)
                f.write(struct.pack('<fffBBB', v[0], v[1], v[2], r, g, b))

            # Faces (binary)
            for face in faces:
                f.write(struct.pack('<Biii', 3, face[0], face[1], face[2]))
