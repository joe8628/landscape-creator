"""OBJ format exporter for 3D meshes."""

from pathlib import Path
from typing import Optional

from ..core.voxel_grid import VoxelGrid
from ..rendering.mesh_builder import MeshBuilder


class OBJExporter:
    """Exports voxel grids to OBJ format."""

    def __init__(self):
        """Initialize the OBJ exporter."""
        self._mesh_builder = MeshBuilder()

    def export(self, grid: VoxelGrid, filepath: str) -> bool:
        """Export voxel grid to OBJ file.

        Args:
            grid: VoxelGrid to export
            filepath: Path for the output OBJ file

        Returns:
            True if successful, False otherwise
        """
        try:
            vertices, faces, colors = self._mesh_builder.build_mesh(grid)

            if len(vertices) == 0:
                print("No mesh data to export.")
                return False

            path = Path(filepath)
            mtl_path = path.with_suffix('.mtl')

            # Write MTL file (materials)
            self._write_mtl(mtl_path, colors, vertices)

            # Write OBJ file
            self._write_obj(path, vertices, faces, mtl_path.name)

            print(f"Exported to {filepath}")
            return True

        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def _write_obj(
        self,
        path: Path,
        vertices,
        faces,
        mtl_filename: str
    ) -> None:
        """Write the OBJ file."""
        with open(path, 'w') as f:
            f.write(f"# Procedural Landscape Generator\n")
            f.write(f"# Vertices: {len(vertices)}\n")
            f.write(f"# Faces: {len(faces)}\n\n")

            f.write(f"mtllib {mtl_filename}\n\n")

            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")

            f.write("\n")

            # Write faces (OBJ uses 1-based indexing)
            f.write("usemtl landscape\n")
            for face in faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    def _write_mtl(self, path: Path, colors, vertices) -> None:
        """Write the MTL (material) file."""
        with open(path, 'w') as f:
            f.write("# Procedural Landscape Materials\n\n")
            f.write("newmtl landscape\n")
            f.write("Ka 0.2 0.2 0.2\n")  # Ambient
            f.write("Kd 0.8 0.8 0.8\n")  # Diffuse
            f.write("Ks 0.1 0.1 0.1\n")  # Specular
            f.write("Ns 10.0\n")          # Shininess
            f.write("d 1.0\n")            # Opacity
