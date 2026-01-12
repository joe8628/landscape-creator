#!/usr/bin/env python3
"""Procedural 3D Voxel Landscape Generator.

A procedural generator that produces low-resolution 3D voxel landscapes
with realistic geological features, vegetation, and decorative elements.

Usage:
    python main.py [--seed SEED] [--no-gui]

Examples:
    python main.py                  # Launch GUI
    python main.py --seed 12345     # Generate with specific seed
    python main.py --no-gui         # CLI mode (generate and export)
"""

import argparse
import sys


def main():
    """Main entry point for the landscape generator."""
    parser = argparse.ArgumentParser(
        description="Procedural 3D Voxel Landscape Generator"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Seed for deterministic generation (default: 12345)"
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run in CLI mode without GUI"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for CLI mode (e.g., landscape.obj)"
    )

    args = parser.parse_args()

    if args.no_gui:
        run_cli(args.seed, args.output)
    else:
        run_gui()


def run_gui():
    """Launch the GUI application."""
    try:
        from src.gui.main_window import MainWindow

        app = MainWindow()
        app.run()
    except ImportError as e:
        print(f"Error: Could not import GUI components: {e}")
        print("Make sure tkinter is installed.")
        sys.exit(1)


def run_cli(seed: int, output_path: str = None):
    """Run in command-line mode.

    Args:
        seed: Generation seed
        output_path: Optional output file path
    """
    print(f"Procedural Landscape Generator - CLI Mode")
    print(f"Seed: {seed}")
    print("-" * 40)

    from src.core.voxel_grid import VoxelGrid
    from src.generators.terrain_generator import TerrainGenerator
    from src.generators.plant_generator import PlantGenerator
    from src.generators.decoration_generator import DecorationGenerator

    # Create grid
    print("Creating voxel grid (256x256x128)...")
    grid = VoxelGrid()

    # Generate terrain
    print("Generating terrain...")
    terrain_gen = TerrainGenerator(seed)
    terrain_gen.generate(grid)

    # Generate plants
    print("Generating plants...")
    plant_gen = PlantGenerator(seed + 1)
    plant_gen.generate(grid)

    # Generate decorations
    print("Generating decorations...")
    deco_gen = DecorationGenerator(seed + 2)
    deco_gen.generate(grid)

    print("Generation complete!")

    # Export if path provided
    if output_path:
        print(f"Exporting to {output_path}...")

        if output_path.endswith('.obj'):
            from src.export.obj_exporter import OBJExporter
            OBJExporter().export(grid, output_path)
        elif output_path.endswith('.ply'):
            from src.export.ply_exporter import PLYExporter
            PLYExporter().export(grid, output_path)
        elif output_path.endswith('.json'):
            from src.export.data_exporter import DataExporter
            DataExporter().export_json(grid, output_path, seed)
        elif output_path.endswith('.voxel'):
            from src.export.data_exporter import DataExporter
            DataExporter().export_binary(grid, output_path, seed)
        else:
            print(f"Unknown format. Supported: .obj, .ply, .json, .voxel")
    else:
        # Show viewport
        print("Opening viewport...")
        from src.rendering.viewport import Viewport
        viewport = Viewport()
        viewport.show(grid)


if __name__ == "__main__":
    main()
