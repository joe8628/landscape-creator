"""Noise generation utilities for procedural terrain."""

import numpy as np
from typing import Optional

try:
    from noise import pnoise2, pnoise3, snoise2, snoise3
    HAS_NOISE = True
except ImportError:
    HAS_NOISE = False


class NoiseGenerator:
    """Generates coherent noise for procedural generation.

    Uses Perlin/Simplex noise with multiple octaves for natural-looking
    terrain features.
    """

    def __init__(self, seed: int):
        """Initialize the noise generator with a seed.

        Args:
            seed: Integer seed for reproducible noise generation
        """
        self.seed = seed
        self._rng = np.random.default_rng(seed)

        # Generate base offsets for each octave to ensure variety
        self._offsets = self._rng.random((8, 2)) * 10000

    def noise_2d(
        self,
        x: float,
        y: float,
        octaves: int = 6,
        persistence: float = 0.5,
        lacunarity: float = 2.0,
        scale: float = 1.0
    ) -> float:
        """Generate 2D Perlin noise at a point.

        Args:
            x, y: Coordinates
            octaves: Number of noise layers to combine
            persistence: Amplitude multiplier per octave
            lacunarity: Frequency multiplier per octave
            scale: Base scale of the noise

        Returns:
            Noise value typically in range [-1, 1]
        """
        if HAS_NOISE:
            return pnoise2(
                x / scale,
                y / scale,
                octaves=octaves,
                persistence=persistence,
                lacunarity=lacunarity,
                base=self.seed
            )
        else:
            # Fallback: simple multi-octave sine-based noise
            return self._fallback_noise_2d(x, y, octaves, persistence, lacunarity, scale)

    def noise_3d(
        self,
        x: float,
        y: float,
        z: float,
        octaves: int = 4,
        persistence: float = 0.5,
        lacunarity: float = 2.0,
        scale: float = 1.0
    ) -> float:
        """Generate 3D Perlin noise at a point.

        Used for cave generation and volumetric features.

        Args:
            x, y, z: Coordinates
            octaves: Number of noise layers to combine
            persistence: Amplitude multiplier per octave
            lacunarity: Frequency multiplier per octave
            scale: Base scale of the noise

        Returns:
            Noise value typically in range [-1, 1]
        """
        if HAS_NOISE:
            return pnoise3(
                x / scale,
                y / scale,
                z / scale,
                octaves=octaves,
                persistence=persistence,
                lacunarity=lacunarity,
                base=self.seed
            )
        else:
            return self._fallback_noise_3d(x, y, z, octaves, persistence, lacunarity, scale)

    def _fallback_noise_2d(
        self,
        x: float,
        y: float,
        octaves: int,
        persistence: float,
        lacunarity: float,
        scale: float
    ) -> float:
        """Fallback noise when noise library is not available."""
        value = 0.0
        amplitude = 1.0
        frequency = 1.0 / scale
        max_value = 0.0

        for i in range(octaves):
            ox, oy = self._offsets[i % 8]
            value += amplitude * np.sin((x * frequency + ox) * 0.1) * np.cos((y * frequency + oy) * 0.1)
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        return value / max_value

    def _fallback_noise_3d(
        self,
        x: float,
        y: float,
        z: float,
        octaves: int,
        persistence: float,
        lacunarity: float,
        scale: float
    ) -> float:
        """Fallback 3D noise when noise library is not available."""
        value = 0.0
        amplitude = 1.0
        frequency = 1.0 / scale
        max_value = 0.0

        for i in range(octaves):
            ox, oy = self._offsets[i % 8]
            value += amplitude * (
                np.sin((x * frequency + ox) * 0.1) *
                np.cos((y * frequency + oy) * 0.1) *
                np.sin((z * frequency + ox + oy) * 0.1)
            )
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        return value / max_value

    def tileable_noise_2d(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        octaves: int = 6,
        persistence: float = 0.5,
        scale: float = 1.0
    ) -> float:
        """Generate tileable 2D noise for seamless terrain edges.

        Args:
            x, y: Coordinates
            width, height: Dimensions for tiling
            octaves: Number of noise layers
            persistence: Amplitude decay per octave
            scale: Base scale

        Returns:
            Tileable noise value
        """
        # Map coordinates to a torus to create seamless tiling
        nx = x / width
        ny = y / height

        # Sample noise at 4D points on a torus
        angle_x = nx * 2 * np.pi
        angle_y = ny * 2 * np.pi

        px = np.cos(angle_x) * scale
        py = np.sin(angle_x) * scale
        qx = np.cos(angle_y) * scale
        qy = np.sin(angle_y) * scale

        # Use the 4D coordinates to sample 2D noise twice
        n1 = self.noise_2d(px, py, octaves, persistence, scale=1.0)
        n2 = self.noise_2d(qx, qy, octaves, persistence, scale=1.0)

        return (n1 + n2) / 2
