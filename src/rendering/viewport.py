"""3D viewport for landscape visualization."""

from typing import Optional, Tuple
import numpy as np

from ..core.voxel_grid import VoxelGrid
from ..core.materials import MaterialType, get_material_color


class Viewport:
    """3D viewport for rendering and interacting with landscapes.

    Uses matplotlib by default for reliable cross-platform rendering.
    PyVista can be enabled by setting use_pyvista=True if OpenGL is working.
    """

    def __init__(self, render_mode: str = "auto", use_pyvista: bool = False):
        """Initialize the viewport.

        Args:
            render_mode: "smooth" for marching cubes, "voxel" for blocky,
                        "auto" to choose based on grid size
            use_pyvista: If True, try to use PyVista/VTK (requires OpenGL).
                        Default is False to use matplotlib which is more reliable.
        """
        self._render_mode = render_mode
        self._use_pyvista = use_pyvista
        self._plotter = None

    def show(self, grid: VoxelGrid, title: str = "Landscape Viewer") -> None:
        """Display the voxel grid in a 3D viewport.

        Args:
            grid: VoxelGrid to visualize
            title: Window title
        """
        import os

        # Check environment variable to force matplotlib
        force_matplotlib = os.environ.get('LANDSCAPE_USE_MATPLOTLIB', '1') == '1'

        # Use matplotlib by default for reliability
        if force_matplotlib or not self._use_pyvista:
            self._show_matplotlib(grid, title)
            return

        # Check if OpenGL/PyVista rendering is available
        if not self._check_opengl_available():
            print("OpenGL not available. Using matplotlib fallback.")
            self._show_matplotlib(grid, title)
            return

        try:
            import pyvista as pv
            self._show_pyvista(grid, pv, title)
        except ImportError:
            print("PyVista not available. Using matplotlib fallback.")
            self._show_matplotlib(grid, title)
        except Exception as e:
            error_msg = str(e).lower()
            if "opengl" in error_msg or "config" in error_msg or "visual" in error_msg:
                print(f"OpenGL initialization failed: {e}")
                print("Using matplotlib fallback visualization.")
                self._show_matplotlib(grid, title)
            else:
                raise

    def _check_opengl_available(self) -> bool:
        """Check if OpenGL rendering is available on this system."""
        import os
        import subprocess

        # Check for common indicators of headless/no-GPU environment
        display = os.environ.get('DISPLAY', '')
        wayland = os.environ.get('WAYLAND_DISPLAY', '')

        if not display and not wayland:
            return False

        # Try to check for working OpenGL using glxinfo
        try:
            result = subprocess.run(
                ['glxinfo'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode != 0:
                return False

            output = result.stdout + result.stderr

            # Check for common error indicators
            error_indicators = [
                'error',
                'could not',
                'cannot',
                'failed',
                'no matching',
            ]
            output_lower = output.lower()
            for indicator in error_indicators:
                if indicator in output_lower:
                    # Check it's not just a warning but actual error
                    if 'OpenGL renderer string' not in output:
                        return False

            # Check if we have a working OpenGL with version 3.2+
            if 'OpenGL renderer string' in output:
                # Check for OpenGL version
                import re
                version_match = re.search(r'OpenGL version string:.*?(\d+)\.(\d+)', output)
                if version_match:
                    major = int(version_match.group(1))
                    minor = int(version_match.group(2))
                    if major > 3 or (major == 3 and minor >= 2):
                        return True
                    else:
                        print(f"OpenGL version {major}.{minor} found, but 3.2+ required.")
                        return False
                return True

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # glxinfo not available - try to run without checking
            # but be cautious in certain environments
            pass

        # Check if we have VTK environment variables set for software rendering
        if os.environ.get('VTK_OPENGL_FORCE_OSMESA') == '1':
            return True

        # If DISPLAY is set but we couldn't verify OpenGL, default to False
        # to avoid potential crashes
        return False

    def _show_pyvista(self, grid: VoxelGrid, pv, title: str) -> None:
        """Show grid using PyVista."""
        # Choose render mode based on grid size
        total_voxels = grid.total_voxels
        render_mode = self._render_mode

        if render_mode == "auto":
            # Use voxel mode for larger grids (faster)
            render_mode = "voxel" if total_voxels > 500000 else "smooth"

        print(f"Rendering mode: {render_mode}")
        print(f"Grid size: {grid.get_dimensions()}")

        # Build the mesh
        if render_mode == "smooth":
            mesh = self._build_smooth_mesh(grid, pv)
        else:
            mesh = self._build_voxel_mesh(grid, pv)

        if mesh is None:
            print("No mesh data to display.")
            return

        # Create plotter with better settings
        plotter = pv.Plotter(title=title)

        # Add the mesh
        plotter.add_mesh(
            mesh,
            scalars="colors",
            rgb=True,
            smooth_shading=(render_mode == "smooth"),
            show_edges=False
        )

        # Set up scene
        plotter.add_axes()
        plotter.camera_position = 'iso'

        # Add ground plane for reference
        dims = grid.get_dimensions()
        ground = pv.Plane(
            center=(dims[0]/2, dims[1]/2, 0),
            direction=(0, 0, 1),
            i_size=dims[0],
            j_size=dims[1]
        )
        plotter.add_mesh(ground, color='lightgray', opacity=0.3)

        # Set background
        plotter.set_background('lightblue', top='white')

        # Show with interaction - catch OpenGL errors
        try:
            plotter.show()
        except Exception as e:
            plotter.close()
            error_msg = str(e).lower()
            if "opengl" in error_msg or "gl" in error_msg:
                print(f"OpenGL error during rendering: {e}")
                print("Using matplotlib fallback.")
                self._show_matplotlib(grid, title)
            else:
                raise

    def _build_smooth_mesh(self, grid: VoxelGrid, pv):
        """Build smooth mesh using marching cubes."""
        try:
            from skimage import measure
            from scipy import ndimage
        except ImportError:
            print("scikit-image not available, falling back to voxel mesh")
            return self._build_voxel_mesh(grid, pv)

        data = grid.get_raw_data()

        # Create scalar field for marching cubes
        solid_field = np.zeros_like(data, dtype=np.float32)
        for material in MaterialType:
            if material not in (MaterialType.AIR, MaterialType.WATER):
                solid_field[data == material.value] = 1.0

        # Skip if no solid voxels
        if np.sum(solid_field) == 0:
            return None

        # Apply slight smoothing
        solid_field = ndimage.gaussian_filter(solid_field, sigma=0.5)

        # Extract surface
        try:
            verts, faces, normals, values = measure.marching_cubes(
                solid_field,
                level=0.5,
                spacing=(1.0, 1.0, 1.0)
            )
        except ValueError:
            return None

        # Create PyVista mesh
        pv_faces = np.hstack([
            np.full((len(faces), 1), 3),
            faces
        ]).flatten()

        mesh = pv.PolyData(verts, pv_faces)

        # Assign colors
        colors = self._assign_vertex_colors(verts, grid)
        mesh.point_data["colors"] = (colors * 255).astype(np.uint8)

        return mesh

    def _build_voxel_mesh(self, grid: VoxelGrid, pv):
        """Build voxel-style mesh (faster for large grids)."""
        # Collect visible voxels
        cubes = []
        colors_list = []

        data = grid.get_raw_data()
        width, depth, height = grid.get_dimensions()

        # Only render surface voxels for efficiency
        for x in range(width):
            for y in range(depth):
                for z in range(height):
                    val = data[x, y, z]
                    if val == 0:  # AIR
                        continue

                    material = MaterialType(val) if val > 0 else MaterialType.AIR
                    if material in (MaterialType.AIR, MaterialType.WATER):
                        continue

                    # Check if this voxel is exposed
                    exposed = False
                    for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                        nx, ny, nz = x + dx, y + dy, z + dz
                        if not (0 <= nx < width and 0 <= ny < depth and 0 <= nz < height):
                            exposed = True
                            break
                        neighbor_val = data[nx, ny, nz]
                        if neighbor_val == 0 or neighbor_val == MaterialType.WATER.value:
                            exposed = True
                            break

                    if exposed:
                        # Create cube at this position
                        cube = pv.Cube(center=(x + 0.5, y + 0.5, z + 0.5), x_length=1, y_length=1, z_length=1)
                        cubes.append(cube)
                        colors_list.append(get_material_color(material))

        if not cubes:
            return None

        # Merge all cubes
        mesh = cubes[0]
        for cube in cubes[1:]:
            mesh = mesh.merge(cube)

        # Assign colors (one color per cube, expanded to vertices)
        n_points_per_cube = 8  # A cube has 8 vertices
        colors = np.zeros((len(mesh.points), 3), dtype=np.uint8)

        for i, color in enumerate(colors_list):
            start_idx = i * n_points_per_cube
            end_idx = start_idx + n_points_per_cube
            if end_idx <= len(colors):
                colors[start_idx:end_idx] = color

        mesh.point_data["colors"] = colors

        return mesh

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

    def _show_matplotlib(self, grid: VoxelGrid, title: str = "Landscape Viewer") -> None:
        """Show grid using matplotlib 3D visualization (OpenGL-free fallback)."""
        try:
            import matplotlib.pyplot as plt
            from matplotlib import cm
            from matplotlib.colors import LightSource
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            print("Matplotlib not available. Showing basic info instead.")
            self._show_basic_info(grid)
            return

        print("Building matplotlib visualization...")

        width, depth, height = grid.get_dimensions()

        # Compute heightmap for surface visualization
        heightmap = grid.compute_heightmap()

        # Create meshgrid for surface plot
        X, Y = np.meshgrid(np.arange(width), np.arange(depth), indexing='ij')
        Z = heightmap.copy()

        # Replace -1 (no surface) with 0
        Z[Z < 0] = 0

        # Build color array based on surface materials
        rgb_colors = np.zeros((width, depth, 3))
        for x in range(width):
            for y in range(depth):
                h = heightmap[x, y]
                if h >= 0:
                    material = grid.get(x, y, int(h))
                    color = get_material_color(material)
                    rgb_colors[x, y] = [c / 255.0 for c in color]
                else:
                    # Water or empty - use blue
                    rgb_colors[x, y] = [0.2, 0.4, 0.8]

        print(f"Rendering terrain surface ({width}x{depth})...")

        # Create figure with interactive 3D view
        fig = plt.figure(figsize=(14, 6))
        fig.suptitle(f"{title} - Use mouse to rotate, scroll to zoom", fontsize=12)

        # 3D surface plot
        ax1 = fig.add_subplot(121, projection='3d')

        # Apply lighting for better depth perception
        ls = LightSource(azdeg=315, altdeg=45)

        # Normalize heights for shading
        z_norm = (Z - Z.min()) / (Z.max() - Z.min() + 0.001)

        # Apply shading to colors
        shaded_colors = np.zeros((width, depth, 3))
        for i in range(3):
            shaded_colors[:, :, i] = ls.shade(Z, cmap=cm.gray, blend_mode='soft')[:, :, 0] * 0.3 + rgb_colors[:, :, i] * 0.7

        # Clip colors to valid range
        shaded_colors = np.clip(shaded_colors, 0, 1)

        # Plot the surface
        surf = ax1.plot_surface(
            X, Y, Z,
            facecolors=shaded_colors,
            rstride=1, cstride=1,
            antialiased=True,
            shade=False
        )

        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('Height')
        ax1.set_title('3D Terrain View')

        # Set aspect ratio
        max_range = max(width, depth, height) / 2
        mid_x, mid_y = width / 2, depth / 2
        mid_z = (Z.max() + Z.min()) / 2
        ax1.set_xlim(mid_x - max_range, mid_x + max_range)
        ax1.set_ylim(mid_y - max_range, mid_y + max_range)
        ax1.set_zlim(0, height)

        # Set initial view angle
        ax1.view_init(elev=30, azim=45)

        # Store initial zoom level for zoom controls
        self._zoom_level = 1.0
        self._ax1 = ax1
        self._max_range = max_range
        self._mid_x = mid_x
        self._mid_y = mid_y

        # Add zoom with scroll wheel
        def on_scroll(event):
            if event.inaxes == ax1:
                if event.button == 'up':
                    self._zoom_level *= 0.9  # Zoom in
                elif event.button == 'down':
                    self._zoom_level *= 1.1  # Zoom out
                self._zoom_level = max(0.1, min(5.0, self._zoom_level))
                new_range = self._max_range * self._zoom_level
                ax1.set_xlim(self._mid_x - new_range, self._mid_x + new_range)
                ax1.set_ylim(self._mid_y - new_range, self._mid_y + new_range)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect('scroll_event', on_scroll)

        # Add keyboard zoom controls
        def on_key(event):
            if event.key == '+' or event.key == '=':
                self._zoom_level *= 0.8
            elif event.key == '-':
                self._zoom_level *= 1.25
            elif event.key == 'r':  # Reset
                self._zoom_level = 1.0
                ax1.view_init(elev=30, azim=45)
            self._zoom_level = max(0.1, min(5.0, self._zoom_level))
            new_range = self._max_range * self._zoom_level
            ax1.set_xlim(self._mid_x - new_range, self._mid_x + new_range)
            ax1.set_ylim(self._mid_y - new_range, self._mid_y + new_range)
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect('key_press_event', on_key)

        # Heightmap view (2D top-down)
        ax2 = fig.add_subplot(122)

        # Display colored heightmap
        ax2.imshow(rgb_colors.transpose(1, 0, 2), origin='lower', aspect='equal')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.set_title('Top-Down View (colored by material)')

        # Add contour lines for elevation
        contour = ax2.contour(X.T, Y.T, Z.T, levels=10, colors='black', alpha=0.3, linewidths=0.5)

        plt.tight_layout()
        print("Controls: Mouse drag to rotate, scroll to zoom, +/- keys to zoom, 'r' to reset view")
        plt.show()

    def _show_basic_info(self, grid: VoxelGrid) -> None:
        """Display basic grid information when visualization is unavailable."""
        width, depth, height = grid.get_dimensions()
        print(f"\nGrid dimensions: {width} x {depth} x {height}")
        print(f"Total voxels: {grid.total_voxels:,}")
        print(f"Solid voxels: {grid.count_solid_voxels():,}")

        print("\nMaterial distribution:")
        dist = grid.get_material_distribution()
        for material, count in sorted(dist.items(), key=lambda x: -x[1]):
            if material != MaterialType.AIR:
                percentage = count / grid.total_voxels * 100
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

            mesh = self._build_smooth_mesh(grid, pv)
            if mesh is None:
                mesh = self._build_voxel_mesh(grid, pv)

            if mesh is None:
                return False

            plotter = pv.Plotter(off_screen=True)
            plotter.add_mesh(mesh, scalars="colors", rgb=True, smooth_shading=True)
            plotter.camera_position = 'iso'
            plotter.set_background('lightblue', top='white')
            plotter.screenshot(filename)

            return True
        except Exception as e:
            print(f"Failed to save screenshot: {e}")
            return False
