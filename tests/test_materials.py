"""Tests for materials module."""

import unittest
from src.core.materials import MaterialType, get_material_color, is_solid, MATERIAL_COLORS


class TestMaterials(unittest.TestCase):
    """Tests for material types and colors."""

    def test_all_materials_have_colors(self):
        """Test that all material types have defined colors."""
        for material in MaterialType:
            color = get_material_color(material)
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)

    def test_color_values_in_range(self):
        """Test that all color values are in valid RGB range."""
        for material, color in MATERIAL_COLORS.items():
            for component in color:
                self.assertGreaterEqual(component, 0)
                self.assertLessEqual(component, 255)

    def test_air_is_not_solid(self):
        """Test that AIR is not solid."""
        self.assertFalse(is_solid(MaterialType.AIR))

    def test_water_is_not_solid(self):
        """Test that WATER is not solid."""
        self.assertFalse(is_solid(MaterialType.WATER))

    def test_stone_is_solid(self):
        """Test that STONE is solid."""
        self.assertTrue(is_solid(MaterialType.STONE))

    def test_all_non_air_water_are_solid(self):
        """Test that all materials except AIR and WATER are solid."""
        non_solid = {MaterialType.AIR, MaterialType.WATER}
        for material in MaterialType:
            if material in non_solid:
                self.assertFalse(is_solid(material))
            else:
                self.assertTrue(is_solid(material))


if __name__ == '__main__':
    unittest.main()
