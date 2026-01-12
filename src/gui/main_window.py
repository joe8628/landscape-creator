"""Main application window."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from ..core.voxel_grid import VoxelGrid
from ..generators.terrain_generator import TerrainGenerator
from ..generators.plant_generator import PlantGenerator
from ..generators.decoration_generator import DecorationGenerator
from ..rendering.viewport import Viewport
from ..export.obj_exporter import OBJExporter
from ..export.ply_exporter import PLYExporter
from ..export.data_exporter import DataExporter
from .controls import ControlsPanel


class MainWindow:
    """Main application window with controls and viewport."""

    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Procedural Landscape Generator")
        self.root.geometry("800x600")

        self._grid: Optional[VoxelGrid] = None
        self._seed: int = 12345

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Controls panel (left side)
        self.controls = ControlsPanel(main_frame, self._on_generate, self._on_export)
        self.controls.frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        # Status area (right side / bottom)
        self._setup_status_area(main_frame)

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

    def _setup_status_area(self, parent: ttk.Frame) -> None:
        """Set up the status display area."""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(row=0, column=1, sticky="nsew")

        self.status_text = tk.Text(status_frame, height=20, width=50, state='disabled')
        self.status_text.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(status_frame, orient='vertical', command=self.status_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.status_text.configure(yscrollcommand=scrollbar.set)

    def _log(self, message: str) -> None:
        """Add a message to the status log."""
        self.status_text.configure(state='normal')
        self.status_text.insert('end', message + '\n')
        self.status_text.see('end')
        self.status_text.configure(state='disabled')
        self.root.update()

    def _on_generate(self, seed: int, options: dict) -> None:
        """Handle generate button click.

        Args:
            seed: Generation seed
            options: Generation options (terrain, plants, decorations enabled)
        """
        self._seed = seed
        self._log(f"Generating landscape with seed {seed}...")

        try:
            # Create grid
            self._grid = VoxelGrid()

            # Generate terrain
            if options.get('terrain', True):
                self._log("Generating terrain...")
                terrain_gen = TerrainGenerator(seed)
                terrain_gen.generate(self._grid)
                self._log("Terrain complete.")

            # Generate plants
            if options.get('plants', True):
                self._log("Generating plants...")
                plant_gen = PlantGenerator(seed + 1)
                plant_gen.generate(self._grid)
                self._log("Plants complete.")

            # Generate decorations
            if options.get('decorations', True):
                self._log("Generating decorations...")
                deco_gen = DecorationGenerator(seed + 2)
                deco_gen.generate(self._grid)
                self._log("Decorations complete.")

            self._log("Generation complete!")
            self._log(f"Grid size: {self._grid.get_dimensions()}")

            # Show viewport
            if messagebox.askyesno("View", "Open 3D viewport?"):
                viewport = Viewport()
                viewport.show(self._grid)

        except Exception as e:
            self._log(f"Error: {e}")
            messagebox.showerror("Error", str(e))

    def _on_export(self, format_type: str) -> None:
        """Handle export button click.

        Args:
            format_type: Export format ('obj', 'ply', 'json', 'binary')
        """
        if self._grid is None:
            messagebox.showwarning("Warning", "Generate a landscape first!")
            return

        extensions = {
            'obj': '.obj',
            'ply': '.ply',
            'json': '.json',
            'binary': '.voxel'
        }

        filepath = filedialog.asksaveasfilename(
            defaultextension=extensions.get(format_type, '.obj'),
            filetypes=[
                ("OBJ files", "*.obj"),
                ("PLY files", "*.ply"),
                ("JSON files", "*.json"),
                ("Binary files", "*.voxel"),
                ("All files", "*.*")
            ]
        )

        if not filepath:
            return

        self._log(f"Exporting to {filepath}...")

        try:
            if format_type == 'obj':
                OBJExporter().export(self._grid, filepath)
            elif format_type == 'ply':
                PLYExporter().export(self._grid, filepath)
            elif format_type == 'json':
                DataExporter().export_json(self._grid, filepath, self._seed)
            elif format_type == 'binary':
                DataExporter().export_binary(self._grid, filepath, self._seed)

            self._log("Export complete!")

        except Exception as e:
            self._log(f"Export error: {e}")
            messagebox.showerror("Export Error", str(e))

    def run(self) -> None:
        """Run the application main loop."""
        self.root.mainloop()
