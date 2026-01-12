"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def small_grid():
    """Create a small voxel grid for testing."""
    from src.core.voxel_grid import VoxelGrid
    return VoxelGrid(32, 32, 32)


@pytest.fixture
def medium_grid():
    """Create a medium voxel grid for testing."""
    from src.core.voxel_grid import VoxelGrid
    return VoxelGrid(64, 64, 64)


@pytest.fixture
def default_seed():
    """Default seed for reproducible tests."""
    return 42


@pytest.fixture
def terrain_generator(default_seed):
    """Create a terrain generator with default seed."""
    from src.generators.terrain_generator import TerrainGenerator
    return TerrainGenerator(default_seed)


@pytest.fixture
def plant_generator(default_seed):
    """Create a plant generator with default seed."""
    from src.generators.plant_generator import PlantGenerator
    return PlantGenerator(default_seed)


@pytest.fixture
def decoration_generator(default_seed):
    """Create a decoration generator with default seed."""
    from src.generators.decoration_generator import DecorationGenerator
    return DecorationGenerator(default_seed)
