"""3D viewport for landscape visualization."""

from typing import Optional, Tuple
import numpy as np

from ..core.voxel_grid import VoxelGrid
from .mesh_builder import MeshBuilder


class Viewport:
    """3D viewport for rendering and interacting with landscapes.

    Uses PyVista for visualization when available.
    """

    def __init__(self):
        """Initialize the viewport."""
        self._plotter = None
        self._mesh_builder = MeshBuilder()
        self._current_mesh = None

    def show(self, grid: VoxelGrid) -> None:
        """Display the voxel grid in a 3D viewport.

        Args:
            grid: VoxelGrid to visualize
        """
        try:
            import pyvista as pv
            self._show_pyvista(grid, pv)
        except ImportError:
            print("PyVista not available. Install with: pip install pyvista")
            print("Falling back to basic info display.")
            self._show_basic_info(grid)

    def _show_pyvista(self, grid: VoxelGrid, pv) -> None:
        """Show grid using PyVista."""
        # Build mesh
        vertices, faces, colors = self._mesh_builder.build_mesh(grid)

        if len(vertices) == 0:
            print("No mesh data to display.")
            return

        # Convert to PyVista mesh format
        # Faces need to be in format [n_points, p1, p2, p3, ...]
        pv_faces = np.hstack([
            np.full((len(faces), 1), 3),
            faces
        ]).flatten()

        mesh = pv.PolyData(vertices, pv_faces)

        # Add vertex colors
        if len(colors) > 0:
            mesh.point_data["colors"] = (colors * 255).astype(np.uint8)

        # Create plotter
        plotter = pv.Plotter()
        plotter.add_mesh(
            mesh,
            scalars="colors",
            rgb=True,
            smooth_shading=True
        )

        # Set up camera
        plotter.camera_position = 'iso'
        plotter.add_axes()

        # Show
        plotter.show()

    def _show_basic_info(self, grid: VoxelGrid) -> None:
        """Display basic grid information when visualization is unavailable."""
        width, depth, height = grid.get_dimensions()
        print(f"Grid dimensions: {width} x {depth} x {height}")

        # Count materials
        data = grid.get_raw_data()
        from ..core.materials import MaterialType

        print("\nMaterial distribution:")
        for material in MaterialType:
            count = np.sum(data == material.value)
            if count > 0:
                percentage = count / data.size * 100
                print(f"  {material.name}: {count:,} voxels ({percentage:.1f}%)")

    def get_screenshot(self, grid: VoxelGrid, filename: str) -> bool:
        """Save a screenshot of the viewport.

        Args:
            grid: VoxelGrid to render
            filename: Path to save the screenshot

        Returns:
            True if successful, False otherwise
        """
        try:
            import pyvista as pv

            vertices, faces, colors = self._mesh_builder.build_mesh(grid)

            if len(vertices) == 0:
                return False

            pv_faces = np.hstack([
                np.full((len(faces), 1), 3),
                faces
            ]).flatten()

            mesh = pv.PolyData(vertices, pv_faces)

            if len(colors) > 0:
                mesh.point_data["colors"] = (colors * 255).astype(np.uint8)

            plotter = pv.Plotter(off_screen=True)
            plotter.add_mesh(mesh, scalars="colors", rgb=True, smooth_shading=True)
            plotter.camera_position = 'iso'
            plotter.screenshot(filename)

            return True
        except Exception as e:
            print(f"Failed to save screenshot: {e}")
            return False
