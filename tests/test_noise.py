"""Tests for noise generator module."""

import unittest
from src.core.noise_generator import NoiseGenerator


class TestNoiseGenerator(unittest.TestCase):
    """Tests for NoiseGenerator class."""

    def test_deterministic_2d(self):
        """Test that 2D noise is deterministic with same seed."""
        gen1 = NoiseGenerator(42)
        gen2 = NoiseGenerator(42)

        for x in range(10):
            for y in range(10):
                self.assertEqual(
                    gen1.noise_2d(x, y),
                    gen2.noise_2d(x, y)
                )

    def test_deterministic_3d(self):
        """Test that 3D noise is deterministic with same seed."""
        gen1 = NoiseGenerator(42)
        gen2 = NoiseGenerator(42)

        for x in range(5):
            for y in range(5):
                for z in range(5):
                    self.assertEqual(
                        gen1.noise_3d(x, y, z),
                        gen2.noise_3d(x, y, z)
                    )

    def test_different_seeds_produce_different_noise(self):
        """Test that different seeds produce different results."""
        gen1 = NoiseGenerator(42)
        gen2 = NoiseGenerator(123)

        differences = 0
        # Use larger coordinate values with scale for better seed differentiation
        for x in range(10):
            for y in range(10):
                val1 = gen1.noise_2d(x * 10 + 50, y * 10 + 50, scale=50.0)
                val2 = gen2.noise_2d(x * 10 + 50, y * 10 + 50, scale=50.0)
                if val1 != val2:
                    differences += 1

        self.assertGreater(differences, 0)

    def test_noise_range(self):
        """Test that noise values are in expected range."""
        gen = NoiseGenerator(42)

        for x in range(20):
            for y in range(20):
                val = gen.noise_2d(x * 10, y * 10, scale=50.0)
                # Perlin noise typically returns values in [-1, 1]
                self.assertGreaterEqual(val, -2.0)
                self.assertLessEqual(val, 2.0)

    def test_octaves_affect_detail(self):
        """Test that more octaves add detail (different values)."""
        gen = NoiseGenerator(42)

        val1 = gen.noise_2d(50, 50, octaves=1, scale=100.0)
        val6 = gen.noise_2d(50, 50, octaves=6, scale=100.0)

        # Different octave counts should produce different values
        self.assertNotEqual(val1, val6)


if __name__ == '__main__':
    unittest.main()
