"""Mesh building using marching cubes for smooth surfaces."""

import numpy as np
from typing import Tuple, Optional

from ..core.voxel_grid import VoxelGrid
from ..core.materials import MaterialType, get_material_color


class MeshBuilder:
    """Builds smooth 3D meshes from voxel data using marching cubes."""

    def __init__(self):
        """Initialize the mesh builder."""
        self._vertices = []
        self._faces = []
        self._colors = []

    def build_mesh(self, grid: VoxelGrid) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build a mesh from voxel grid data.

        Uses marching cubes for smooth surface extraction.

        Args:
            grid: VoxelGrid to convert to mesh

        Returns:
            Tuple of (vertices, faces, colors) as numpy arrays
        """
        try:
            from skimage import measure
            return self._build_with_marching_cubes(grid, measure)
        except ImportError:
            # Fallback to simple cube-based mesh
            return self._build_simple_mesh(grid)

    def _build_with_marching_cubes(
        self,
        grid: VoxelGrid,
        measure_module
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build mesh using scikit-image marching cubes."""
        data = grid.get_raw_data()

        # Create a scalar field (1 for solid, 0 for air/water)
        solid_field = np.zeros_like(data, dtype=np.float32)
        for material in MaterialType:
            if material not in (MaterialType.AIR, MaterialType.WATER):
                solid_field[data == material.value] = 1.0

        # Apply slight smoothing for better marching cubes results
        from scipy import ndimage
        solid_field = ndimage.gaussian_filter(solid_field, sigma=0.5)

        # Extract surface using marching cubes
        try:
            verts, faces, normals, values = measure_module.marching_cubes(
                solid_field,
                level=0.5,
                spacing=(1.0, 1.0, 1.0)
            )
        except ValueError:
            # No surface found
            return np.array([]), np.array([]), np.array([])

        # Assign colors based on nearest voxel material
        colors = self._assign_vertex_colors(verts, grid)

        return verts, faces, colors

    def _build_simple_mesh(self, grid: VoxelGrid) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build a simple cube-based mesh (fallback)."""
        vertices = []
        faces = []
        colors = []

        for x in range(grid.width):
            for y in range(grid.depth):
                for z in range(grid.height):
                    material = grid.get(x, y, z)
                    if material in (MaterialType.AIR, MaterialType.WATER):
                        continue

                    # Check if any face is exposed
                    for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                        neighbor = grid.get(x+dx, y+dy, z+dz)
                        if neighbor in (MaterialType.AIR, MaterialType.WATER):
                            # Add this face
                            self._add_face(vertices, faces, colors, x, y, z, dx, dy, dz, material)

        return (
            np.array(vertices) if vertices else np.array([]),
            np.array(faces) if faces else np.array([]),
            np.array(colors) if colors else np.array([])
        )

    def _add_face(
        self,
        vertices: list,
        faces: list,
        colors: list,
        x: int, y: int, z: int,
        dx: int, dy: int, dz: int,
        material: MaterialType
    ) -> None:
        """Add a cube face to the mesh."""
        base_idx = len(vertices)
        color = get_material_color(material)
        color_normalized = [c / 255.0 for c in color]

        # Define face vertices based on direction
        if dx == 1:  # +X face
            vertices.extend([
                [x+1, y, z], [x+1, y+1, z], [x+1, y+1, z+1], [x+1, y, z+1]
            ])
        elif dx == -1:  # -X face
            vertices.extend([
                [x, y+1, z], [x, y, z], [x, y, z+1], [x, y+1, z+1]
            ])
        elif dy == 1:  # +Y face
            vertices.extend([
                [x+1, y+1, z], [x, y+1, z], [x, y+1, z+1], [x+1, y+1, z+1]
            ])
        elif dy == -1:  # -Y face
            vertices.extend([
                [x, y, z], [x+1, y, z], [x+1, y, z+1], [x, y, z+1]
            ])
        elif dz == 1:  # +Z face (top)
            vertices.extend([
                [x, y, z+1], [x+1, y, z+1], [x+1, y+1, z+1], [x, y+1, z+1]
            ])
        elif dz == -1:  # -Z face (bottom)
            vertices.extend([
                [x, y+1, z], [x+1, y+1, z], [x+1, y, z], [x, y, z]
            ])

        # Add two triangles for the quad
        faces.extend([
            [base_idx, base_idx+1, base_idx+2],
            [base_idx, base_idx+2, base_idx+3]
        ])

        # Add colors for each vertex
        for _ in range(4):
            colors.append(color_normalized)

    def _assign_vertex_colors(self, vertices: np.ndarray, grid: VoxelGrid) -> np.ndarray:
        """Assign colors to vertices based on nearest voxel material."""
        colors = np.zeros((len(vertices), 3), dtype=np.float32)

        for i, vert in enumerate(vertices):
            x, y, z = int(vert[0]), int(vert[1]), int(vert[2])
            material = grid.get(x, y, z)

            # If air, look at neighbors
            if material == MaterialType.AIR:
                for dx, dy, dz in [(0,0,-1), (0,0,1), (1,0,0), (-1,0,0), (0,1,0), (0,-1,0)]:
                    neighbor = grid.get(x+dx, y+dy, z+dz)
                    if neighbor not in (MaterialType.AIR, MaterialType.WATER):
                        material = neighbor
                        break

            rgb = get_material_color(material)
            colors[i] = [c / 255.0 for c in rgb]

        return colors
