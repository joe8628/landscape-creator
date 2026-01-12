"""Main application window."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
import threading
import time
import queue

from ..core.voxel_grid import VoxelGrid
from ..core.materials import MaterialType
from ..generators.terrain_generator import TerrainGenerator
from ..generators.plant_generator import PlantGenerator
from ..generators.decoration_generator import DecorationGenerator
from ..rendering.viewport import Viewport
from ..export.obj_exporter import OBJExporter
from ..export.ply_exporter import PLYExporter
from ..export.data_exporter import DataExporter


# Grid size presets for testing
GRID_SIZES = {
    "Tiny (32x32x32)": (32, 32, 32),
    "Small (64x64x64)": (64, 64, 64),
    "Medium (128x128x64)": (128, 128, 64),
    "Large (256x256x128)": (256, 256, 128),
}


class MainWindow:
    """Main application window with controls and viewport."""

    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Procedural Landscape Generator")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        self._grid: Optional[VoxelGrid] = None
        self._seed: int = 12345
        self._generating = False

        # Message queue for thread-safe UI updates
        self._message_queue = queue.Queue()

        self._setup_ui()

        # Start processing message queue
        self._process_queue()

    def _process_queue(self) -> None:
        """Process messages from background threads."""
        try:
            while True:
                msg_type, data = self._message_queue.get_nowait()

                if msg_type == "log":
                    self._do_log(data)
                elif msg_type == "progress":
                    self._do_update_progress(data[0], data[1])
                elif msg_type == "complete":
                    self._generation_complete()
                elif msg_type == "error":
                    self._generation_error(data)

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(50, self._process_queue)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Left panel - Controls
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        self._setup_controls(left_panel)

        # Right panel - Status and Stats
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        self._setup_stats(right_panel)
        self._setup_status(right_panel)

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

    def _setup_controls(self, parent: ttk.Frame) -> None:
        """Set up the controls panel."""
        # Title
        ttk.Label(parent, text="Controls", font=('TkDefaultFont', 12, 'bold')).pack(anchor='w', pady=(0, 10))

        # Seed input
        seed_frame = ttk.LabelFrame(parent, text="Seed", padding="5")
        seed_frame.pack(fill='x', pady=5)

        self.seed_var = tk.StringVar(value="12345")
        seed_entry = ttk.Entry(seed_frame, textvariable=self.seed_var, width=15)
        seed_entry.pack(side='left', padx=(0, 5))

        ttk.Button(seed_frame, text="Random", command=self._random_seed, width=8).pack(side='left')

        # Grid size selector
        size_frame = ttk.LabelFrame(parent, text="Grid Size", padding="5")
        size_frame.pack(fill='x', pady=5)

        self.size_var = tk.StringVar(value="Small (64x64x64)")
        size_combo = ttk.Combobox(size_frame, textvariable=self.size_var, values=list(GRID_SIZES.keys()), state='readonly')
        size_combo.pack(fill='x')

        # Layer toggles
        layers_frame = ttk.LabelFrame(parent, text="Layers", padding="5")
        layers_frame.pack(fill='x', pady=5)

        self.terrain_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(layers_frame, text="Terrain", variable=self.terrain_var).pack(anchor='w')

        self.plants_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(layers_frame, text="Plants", variable=self.plants_var).pack(anchor='w')

        self.decorations_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(layers_frame, text="Decorations", variable=self.decorations_var).pack(anchor='w')

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', pady=10)

        self.progress_label = ttk.Label(parent, text="Ready")
        self.progress_label.pack(anchor='w')

        # Action buttons
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)

        self.generate_btn = ttk.Button(parent, text="Generate Landscape", command=self._on_generate)
        self.generate_btn.pack(fill='x', pady=2)

        self.view_btn = ttk.Button(parent, text="View 3D", command=self._on_view, state='disabled')
        self.view_btn.pack(fill='x', pady=2)

        # Export section
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(parent, text="Export:").pack(anchor='w')

        export_frame = ttk.Frame(parent)
        export_frame.pack(fill='x', pady=5)

        self.export_btns = []
        for text, fmt in [("OBJ", 'obj'), ("PLY", 'ply'), ("JSON", 'json')]:
            btn = ttk.Button(export_frame, text=text, command=lambda f=fmt: self._on_export(f), state='disabled', width=6)
            btn.pack(side='left', padx=2)
            self.export_btns.append(btn)

    def _setup_stats(self, parent: ttk.Frame) -> None:
        """Set up the statistics display."""
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding="10")
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Stats display using grid
        self.stats_labels = {}
        stats = [
            ("Grid Size:", "grid_size", "-"),
            ("Total Voxels:", "total_voxels", "-"),
            ("Solid Voxels:", "solid_voxels", "-"),
            ("Fill Rate:", "fill_rate", "-"),
        ]

        for i, (label, key, default) in enumerate(stats):
            ttk.Label(stats_frame, text=label).grid(row=i, column=0, sticky='w', padx=(0, 10))
            self.stats_labels[key] = ttk.Label(stats_frame, text=default)
            self.stats_labels[key].grid(row=i, column=1, sticky='w')

        # Material distribution
        self.material_frame = ttk.LabelFrame(parent, text="Material Distribution", padding="10")
        self.material_frame.grid(row=1, column=0, sticky="new", pady=(0, 10))

        self.material_text = tk.Text(self.material_frame, height=8, width=40, state='disabled')
        self.material_text.pack(fill='both', expand=True)

    def _setup_status(self, parent: ttk.Frame) -> None:
        """Set up the status log."""
        status_frame = ttk.LabelFrame(parent, text="Log", padding="10")
        status_frame.grid(row=2, column=0, sticky="nsew")
        parent.rowconfigure(2, weight=1)

        # Status text with scrollbar
        text_frame = ttk.Frame(status_frame)
        text_frame.pack(fill='both', expand=True)

        self.status_text = tk.Text(text_frame, height=10, width=50, state='disabled')
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)

        self.status_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _log(self, message: str) -> None:
        """Thread-safe logging - queues message for main thread."""
        self._message_queue.put(("log", message))

    def _do_log(self, message: str) -> None:
        """Actually add message to log (must be called from main thread)."""
        self.status_text.configure(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')
        self.status_text.configure(state='disabled')

    def _update_progress(self, value: float, label: str) -> None:
        """Thread-safe progress update - queues for main thread."""
        self._message_queue.put(("progress", (value, label)))

    def _do_update_progress(self, value: float, label: str) -> None:
        """Actually update progress (must be called from main thread)."""
        self.progress_var.set(value)
        self.progress_label.config(text=label)

    def _update_stats(self) -> None:
        """Update statistics display (call from main thread only)."""
        if self._grid is None:
            return

        dims = self._grid.get_dimensions()
        total = self._grid.total_voxels
        solid = self._grid.count_solid_voxels()
        fill_rate = (solid / total) * 100 if total > 0 else 0

        self.stats_labels["grid_size"].config(text=f"{dims[0]}x{dims[1]}x{dims[2]}")
        self.stats_labels["total_voxels"].config(text=f"{total:,}")
        self.stats_labels["solid_voxels"].config(text=f"{solid:,}")
        self.stats_labels["fill_rate"].config(text=f"{fill_rate:.1f}%")

        # Update material distribution
        self.material_text.configure(state='normal')
        self.material_text.delete('1.0', 'end')

        dist = self._grid.get_material_distribution()
        for material, count in sorted(dist.items(), key=lambda x: -x[1]):
            if material != MaterialType.AIR:
                pct = (count / total) * 100
                self.material_text.insert('end', f"{material.name}: {count:,} ({pct:.1f}%)\n")

        self.material_text.configure(state='disabled')

    def _random_seed(self) -> None:
        """Generate a random seed."""
        import random
        self.seed_var.set(str(random.randint(0, 999999999)))

    def _on_generate(self) -> None:
        """Handle generate button click."""
        if self._generating:
            return

        self._generating = True
        self.generate_btn.config(state='disabled')
        self.view_btn.config(state='disabled')
        for btn in self.export_btns:
            btn.config(state='disabled')

        # Get parameters
        try:
            seed = int(self.seed_var.get())
        except ValueError:
            seed = hash(self.seed_var.get()) % 1000000000

        self._seed = seed
        size = GRID_SIZES[self.size_var.get()]

        # Get layer options before starting thread
        do_terrain = self.terrain_var.get()
        do_plants = self.plants_var.get()
        do_decorations = self.decorations_var.get()

        self._log(f"Starting generation with seed {seed}...")
        self._log(f"Grid size: {size[0]}x{size[1]}x{size[2]}")

        # Run generation in thread
        def generate():
            try:
                self._update_progress(0, "Creating grid...")

                # Create grid
                self._grid = VoxelGrid(size[0], size[1], size[2])

                steps_done = 0
                total_steps = sum([do_terrain, do_plants, do_decorations])
                if total_steps == 0:
                    total_steps = 1

                # Generate terrain
                if do_terrain:
                    self._update_progress(10, "Generating terrain...")
                    self._log("Generating terrain...")
                    terrain_gen = TerrainGenerator(seed)
                    terrain_gen.generate(self._grid)
                    steps_done += 1
                    self._log("Terrain complete.")

                # Generate plants
                if do_plants:
                    progress = 10 + (steps_done / total_steps) * 70
                    self._update_progress(progress, "Generating plants...")
                    self._log("Generating plants...")
                    plant_gen = PlantGenerator(seed + 1)
                    plant_gen.generate(self._grid)
                    steps_done += 1
                    self._log("Plants complete.")

                # Generate decorations
                if do_decorations:
                    progress = 10 + (steps_done / total_steps) * 70
                    self._update_progress(progress, "Generating decorations...")
                    self._log("Generating decorations...")
                    deco_gen = DecorationGenerator(seed + 2)
                    deco_gen.generate(self._grid)
                    steps_done += 1
                    self._log("Decorations complete.")

                self._update_progress(100, "Complete!")
                self._log("Generation complete!")

                # Signal completion via queue
                self._message_queue.put(("complete", None))

            except Exception as e:
                self._log(f"Error: {e}")
                self._message_queue.put(("error", str(e)))

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def _generation_complete(self) -> None:
        """Called when generation is complete (main thread)."""
        self._generating = False
        self.generate_btn.config(state='normal')
        self.view_btn.config(state='normal')
        for btn in self.export_btns:
            btn.config(state='normal')

        self._update_stats()

    def _generation_error(self, error: str) -> None:
        """Called when generation fails (main thread)."""
        self._generating = False
        self.generate_btn.config(state='normal')
        self._do_update_progress(0, "Error")
        messagebox.showerror("Generation Error", error)

    def _on_view(self) -> None:
        """Handle view button click."""
        if self._grid is None:
            messagebox.showwarning("Warning", "Generate a landscape first!")
            return

        self._do_log("Opening 3D viewport...")
        self._do_update_progress(50, "Building mesh...")

        try:
            viewport = Viewport()
            self._do_update_progress(100, "Ready")
            viewport.show(self._grid)
            self._do_log("Viewport closed.")
        except Exception as e:
            self._do_log(f"Viewport error: {e}")
            messagebox.showerror("Viewport Error", str(e))

        self._do_update_progress(0, "Ready")

    def _on_export(self, format_type: str) -> None:
        """Handle export button click."""
        if self._grid is None:
            messagebox.showwarning("Warning", "Generate a landscape first!")
            return

        extensions = {
            'obj': ('.obj', 'OBJ files'),
            'ply': ('.ply', 'PLY files'),
            'json': ('.json', 'JSON files'),
            'binary': ('.voxel', 'Voxel files'),
        }

        ext, desc = extensions.get(format_type, ('.obj', 'OBJ files'))

        filepath = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(desc, f"*{ext}"), ("All files", "*.*")]
        )

        if not filepath:
            return

        self._do_log(f"Exporting to {filepath}...")
        self._do_update_progress(50, "Exporting...")

        try:
            if format_type == 'obj':
                OBJExporter().export(self._grid, filepath)
            elif format_type == 'ply':
                PLYExporter().export(self._grid, filepath)
            elif format_type == 'json':
                DataExporter().export_json(self._grid, filepath, self._seed)
            elif format_type == 'binary':
                DataExporter().export_binary(self._grid, filepath, self._seed)

            self._do_log(f"Exported successfully to {filepath}")
            self._do_update_progress(100, "Export complete")

        except Exception as e:
            self._do_log(f"Export error: {e}")
            messagebox.showerror("Export Error", str(e))

        self._do_update_progress(0, "Ready")

    def run(self) -> None:
        """Run the application main loop."""
        self._do_log("Application started. Ready to generate landscapes.")
        self.root.mainloop()
