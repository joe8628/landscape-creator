"""Control panel for landscape generation settings."""

import tkinter as tk
from tkinter import ttk
import random
from typing import Callable


class ControlsPanel:
    """Control panel with generation options."""

    def __init__(
        self,
        parent: ttk.Frame,
        on_generate: Callable[[int, dict], None],
        on_export: Callable[[str], None]
    ):
        """Initialize controls panel.

        Args:
            parent: Parent frame
            on_generate: Callback for generate button (seed, options)
            on_export: Callback for export button (format_type)
        """
        self.frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        self._on_generate = on_generate
        self._on_export = on_export

        self._setup_controls()

    def _setup_controls(self) -> None:
        """Create the control widgets."""
        # Seed input
        seed_frame = ttk.Frame(self.frame)
        seed_frame.pack(fill='x', pady=5)

        ttk.Label(seed_frame, text="Seed:").pack(side='left')

        self.seed_var = tk.StringVar(value="12345")
        self.seed_entry = ttk.Entry(seed_frame, textvariable=self.seed_var, width=15)
        self.seed_entry.pack(side='left', padx=5)

        ttk.Button(seed_frame, text="Random", command=self._random_seed).pack(side='left')

        # Layer toggles
        ttk.Separator(self.frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(self.frame, text="Layers:").pack(anchor='w')

        self.terrain_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.frame, text="Terrain", variable=self.terrain_var
        ).pack(anchor='w')

        self.plants_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.frame, text="Plants", variable=self.plants_var
        ).pack(anchor='w')

        self.decorations_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.frame, text="Decorations", variable=self.decorations_var
        ).pack(anchor='w')

        # Generate button
        ttk.Separator(self.frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Button(
            self.frame, text="Generate", command=self._generate
        ).pack(fill='x', pady=5)

        # Export section
        ttk.Separator(self.frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(self.frame, text="Export:").pack(anchor='w')

        export_frame = ttk.Frame(self.frame)
        export_frame.pack(fill='x', pady=5)

        ttk.Button(
            export_frame, text="OBJ", command=lambda: self._on_export('obj')
        ).pack(side='left', padx=2)

        ttk.Button(
            export_frame, text="PLY", command=lambda: self._on_export('ply')
        ).pack(side='left', padx=2)

        ttk.Button(
            export_frame, text="JSON", command=lambda: self._on_export('json')
        ).pack(side='left', padx=2)

        ttk.Button(
            export_frame, text="Binary", command=lambda: self._on_export('binary')
        ).pack(side='left', padx=2)

    def _random_seed(self) -> None:
        """Generate a random seed."""
        self.seed_var.set(str(random.randint(0, 999999999)))

    def _generate(self) -> None:
        """Trigger generation with current settings."""
        try:
            seed = int(self.seed_var.get())
        except ValueError:
            seed = hash(self.seed_var.get()) % 1000000000

        options = {
            'terrain': self.terrain_var.get(),
            'plants': self.plants_var.get(),
            'decorations': self.decorations_var.get()
        }

        self._on_generate(seed, options)
