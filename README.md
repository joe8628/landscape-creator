# Procedural 3D Voxel Landscape Generator

A Python-based procedural generator that creates low-resolution 3D voxel landscapes with realistic geological features, vegetation, and decorative elements.

## Features

- **Terrain Generation**: Hills, valleys, mountains, cliffs, water bodies, and caves
- **Vegetation**: Trees (pine, oak, palm), grass, and bushes with terrain-aware placement
- **Decorations**: Rocks, mushrooms, and flowers
- **Smooth Rendering**: Marching cubes algorithm for natural-looking surfaces
- **Multiple Export Formats**: OBJ, PLY, JSON, and binary formats
- **Deterministic Generation**: Seed-based for reproducible landscapes
- **GUI Application**: Simple tkinter interface for easy use

## Installation

### Requirements

- Python 3.10+
- NumPy, SciPy, PyVista, and other dependencies

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install with pip:

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

### GUI Mode

```bash
python main.py
```

### CLI Mode

```bash
# Generate and view
python main.py --no-gui --seed 12345

# Generate and export
python main.py --no-gui --seed 12345 --output landscape.obj
```

### As a Library

```python
from src.core.voxel_grid import VoxelGrid
from src.generators.terrain_generator import TerrainGenerator
from src.generators.plant_generator import PlantGenerator
from src.export.obj_exporter import OBJExporter

# Create grid
grid = VoxelGrid()  # 256x256x128

# Generate terrain
TerrainGenerator(seed=42).generate(grid)

# Add plants
PlantGenerator(seed=43).generate(grid)

# Export
OBJExporter().export(grid, "landscape.obj")
```

## Grid Specifications

| Parameter | Value |
|-----------|-------|
| Horizontal Resolution | 256 x 256 |
| Vertical Resolution | 128 |
| Voxel Size | 1 unit cube |
| Tiling | Seamless on X and Y axes |

## Material Types

| Material | Color | Description |
|----------|-------|-------------|
| STONE | #808080 | Base terrain |
| DIRT | #8B5A2B | Surface layer |
| SAND | #C2B280 | Beaches |
| WATER | #4169E1 | Lakes, rivers |
| GRASS | #228B22 | Ground cover |
| WOOD | #654321 | Tree trunks |
| LEAVES | #32CD32 | Tree foliage |
| SNOW | #FFFAFA | Mountain peaks |

## Project Structure

```
landscape-creator/
├── main.py                 # Entry point
├── src/
│   ├── core/               # Core data structures
│   ├── generators/         # Procedural generators
│   ├── rendering/          # 3D visualization
│   ├── export/             # File exporters
│   └── gui/                # GUI components
├── tests/                  # Unit tests
└── examples/               # Example seeds
```

## Running Tests

```bash
python -m pytest tests/ -v
```

Or with unittest:

```bash
python -m unittest discover -s tests -v
```

## Export Formats

- **OBJ**: Standard 3D format, widely compatible
- **PLY**: Supports vertex colors
- **JSON**: Human-readable voxel data
- **Binary (.voxel)**: Compact format for fast loading

## License

MIT License
