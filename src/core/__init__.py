"""Core components for voxel data management."""

from .materials import MaterialType, is_solid, get_material_color, MATERIAL_COLORS
from .voxel_grid import VoxelGrid, Voxel
from .noise_generator import NoiseGenerator
