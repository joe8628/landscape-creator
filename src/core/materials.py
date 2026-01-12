"""Material types and color definitions for voxels."""

from enum import Enum, auto
from typing import Tuple


class MaterialType(Enum):
    """Enumeration of all voxel material types."""
    AIR = auto()
    STONE = auto()
    DIRT = auto()
    SAND = auto()
    WATER = auto()
    GRASS = auto()
    WOOD = auto()
    LEAVES = auto()
    SNOW = auto()
    DECORATION = auto()


# Realistic natural color palette (RGB)
MATERIAL_COLORS: dict[MaterialType, Tuple[int, int, int]] = {
    MaterialType.AIR: (0, 0, 0),           # Transparent/not rendered
    MaterialType.STONE: (128, 128, 128),   # Medium gray #808080
    MaterialType.DIRT: (139, 90, 43),      # Rich brown #8B5A2B
    MaterialType.SAND: (194, 178, 128),    # Tan/beige #C2B280
    MaterialType.WATER: (65, 105, 225),    # Royal blue #4169E1
    MaterialType.GRASS: (34, 139, 34),     # Forest green #228B22
    MaterialType.WOOD: (101, 67, 33),      # Dark brown #654321
    MaterialType.LEAVES: (50, 205, 50),    # Lime green #32CD32
    MaterialType.SNOW: (255, 250, 250),    # Snow white #FFFAFA
    MaterialType.DECORATION: (255, 105, 180),  # Pink (placeholder)
}


def get_material_color(material: MaterialType) -> Tuple[int, int, int]:
    """Get the RGB color for a material type."""
    return MATERIAL_COLORS.get(material, (255, 0, 255))  # Magenta for unknown


def is_solid(material: MaterialType) -> bool:
    """Check if a material type is solid (not air or water)."""
    return material not in (MaterialType.AIR, MaterialType.WATER)
