# Procedural 3D Voxel Landscape Generator - Requirements Specification

**Version:** 1.0  
**Date:** January 10, 2026  
**Project Type:** Learning Exercise & Art Project

---

## Executive Summary

**Confirmed Specifications:**
- **Grid Size:** 256×256×128 voxels (fixed)
- **Programming Language:** Python
- **Rendering Style:** Smooth/interpolated surfaces (marching cubes)
- **Color Palette:** Realistic natural colors
- **Generation:** Deterministic (seed-based), incremental phases
- **Output:** 3D models (OBJ/PLY/GLTF) and data export (JSON/binary)

**Development Phases:**
1. Terrain (hills, valleys, mountains, water, caves)
2. Plants (trees, grass, bushes with placement rules)
3. Decorations (rocks, mushrooms, flowers)

---

## 1. Project Overview

### 1.1 Purpose
Create a procedural generator that produces low-resolution 3D voxel landscapes with realistic geological features, vegetation, and decorative elements. The system will generate pre-computed landscapes that can be rendered, visualized, and exported.

### 1.2 Scope
- Voxel-based terrain generation with realistic geological constraints
- Seamlessly tiling landscapes for infinite terrain possibility
- Incremental feature implementation: Terrain → Plants → Decorations
- Both data export and 3D model rendering capabilities

---

## 2. Technical Architecture

### 2.1 Recommended Technology Stack

**Primary Language: Python** (Confirmed)
- Libraries: NumPy (voxel data), Perlin/Simplex noise, PyVista/VTK (3D visualization)
- Easy prototyping and extensive 3D libraries
- Excellent for learning and rapid iteration

**Performance Note:** Python is suitable for this project scale (256×256×128). If performance becomes critical in future expansions, critical sections can be optimized with Numba or Cython without rewriting the entire project.

### 2.2 Core Components
```
┌─────────────────────────────────────────┐
│         GUI Application Layer           │
│  (Controls, Seed Input, Visualization)  │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Generation Engine (Core Logic)     │
│  - Terrain Generator                    │
│  - Plant Placement System               │
│  - Decoration System                    │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       Voxel Data Structure              │
│  (256x256xH grid with material types)   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     Rendering & Export System           │
│  - 3D Mesh Generator                    │
│  - File Export (OBJ, PLY, Voxel Data)   │
└─────────────────────────────────────────┘
```

---

## 3. Functional Requirements

### 3.1 Core Grid Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Horizontal Resolution | 256×256 | Fixed grid size |
| Vertical Resolution | 128 | Height limit (confirmed) |
| Voxel Size | 1 unit³ | Standard unit cube |
| World Dimensions | 256×256×128 units | Fixed world size |
| Tiling | Seamless on X and Y axes | Edges must match for infinite tiling |

### 3.2 Voxel Data Structure

Each voxel contains:
```
Voxel {
    material_type: MaterialType,
    is_solid: boolean,
    // Future: color, metadata
}

MaterialType enum:
- AIR (empty space)
- STONE (base terrain)
- DIRT (surface layer)
- SAND (beaches, desert)
- WATER (lakes, rivers)
- GRASS (ground cover)
- WOOD (tree trunks)
- LEAVES (tree foliage)
- SNOW (mountain peaks)
- DECORATION (rocks, flowers, etc.)
```

### 3.3 Visual Style & Rendering

**Confirmed Visual Approach:**

**Color Palette - Realistic Natural Colors:**
| Material | RGB Color | Hex | Description |
|----------|-----------|-----|-------------|
| STONE | (128, 128, 128) | #808080 | Medium gray |
| DIRT | (139, 90, 43) | #8B5A2B | Rich brown |
| SAND | (194, 178, 128) | #C2B280 | Tan/beige |
| WATER | (65, 105, 225) | #4169E1 | Royal blue |
| GRASS | (34, 139, 34) | #228B22 | Forest green |
| WOOD | (101, 67, 33) | #654321 | Dark brown |
| LEAVES | (50, 205, 50) | #32CD32 | Lime green |
| SNOW | (255, 250, 250) | #FFFAFA | Snow white |
| DECORATION | (Varies) | - | Context-dependent |

**Rendering Style - Smooth/Interpolated Surfaces:**
- Use **marching cubes** or similar algorithm to create smooth meshes from voxel data
- Voxels are converted to continuous surfaces (not blocky Minecraft-style)
- Surface normals calculated for proper lighting
- Optional: Apply subtle texture or normal mapping for surface detail

**Benefits of Smooth Rendering:**
- More natural, organic appearance
- Better for artistic/visualization purposes
- Hills and mountains look realistic
- Vegetation blends naturally with terrain

**Implementation:**
- PyVista's `contour()` or `threshold()` methods for smooth surface extraction
- Or use scikit-image's `marching_cubes` algorithm
- Apply Phong shading or similar lighting model

---

## 4. Phase 1: Terrain Generation

### 4.1 Terrain Features

**Required Features:**
1. **Hills** - Gentle elevation changes (slopes < 30°)
2. **Valleys** - Depressions between hills
3. **Mountains** - Steep elevation (slopes 30-60°, peaks 60-70°)
4. **Cliffs** - Near-vertical faces (slopes > 70°)
5. **Water Bodies** - Lakes, rivers at low elevations
6. **Caves** - Enclosed underground spaces (special handling)

### 4.2 Geological Constraints

**Realistic Parameters (Auto-randomized within ranges):**

| Feature | Height Range (voxels) | Height Range (%) | Slope Range | Frequency |
|---------|----------------------|------------------|-------------|-----------|
| Base Terrain | 0-51 | 0-40% | 0-15° | - |
| Hills | 26-77 | 20-60% | 5-30° | Common |
| Mountains | 77-122 | 60-95% | 30-70° | Rare |
| Valleys | 13-38 | 10-30% | 5-25° (inverse) | Common |
| Water Level | 19-32 | 15-25% | 0° (flat) | Variable |
| Cliffs | Any height | - | 70-90° | Uncommon |

**Material Distribution by Height:**
- 0-38 voxels (0-30%): Stone/Sand base, Water possible
- 38-90 voxels (30-70%): Stone base, Dirt surface (2-4 voxels deep)
- 90-115 voxels (70-90%): Stone base, Dirt surface (1-2 voxels)
- 115-128 voxels (90-100%): Stone/Snow

### 4.3 Cave Generation

**Special Handling Required:**
- Caves exist as 3D noise regions below surface
- Cannot use simple heightmap (need volumetric data)
- **Implementation approach:**
  1. Generate surface heightmap first
  2. Apply 3D noise field underground
  3. Carve out voxels where noise exceeds threshold
  4. Ensure caves don't create floating terrain (stability check)

**Cave Constraints:**
- Depth: 13-77 voxels (10-60% of max height)
- Size: 3-20 voxels in any dimension
- Frequency: Sparse (5-10% of underground volume)

### 4.4 Terrain Generation Algorithm

**Recommended Approach:**
1. **Base Heightmap:** Multi-octave Perlin/Simplex noise
   - Low frequency (continental scale)
   - Medium frequency (mountain ranges)
   - High frequency (local detail)
   
2. **Feature Addition:**
   - Apply domain warping for realistic variation
   - Add ridge noise for mountain ranges
   - Subtract valleys using inverse noise
   
3. **Erosion Simulation (Optional for realism):**
   - Simple thermal erosion (material slides down steep slopes)
   - Hydraulic erosion (water carves valleys)
   
4. **Seamless Tiling:**
   - Use tileable noise (wrap coordinates)
   - Or blend edges using transition zones

### 4.5 Water Placement

- Define global water level (approximately 26 voxels, or 20% of max height)
- All voxels below water level and below terrain = WATER
- Create "beaches" by checking slope near water (flat areas = SAND)

---

## 5. Phase 2: Plant Generation

### 5.1 Plant Types

**Limited Variations (Keep complexity low):**

1. **Trees (3 variations)**
   - Pine (conical, 8-15 voxels tall)
   - Oak (rounded, 6-12 voxels tall)
   - Palm (thin trunk, crown, 10-18 voxels tall)

2. **Grass/Vegetation (2 variations)**
   - Short grass (1 voxel tall, GRASS material)
   - Tall grass/flowers (2-3 voxels, mixed GRASS/DECORATION)

3. **Bushes (2 variations)**
   - Small bush (3x3x2 voxels, LEAVES)
   - Large bush (5x5x3 voxels, LEAVES)

### 5.2 Plant Structure

**Procedural Generation Rules:**

**Tree Generation:**
```
Pine Tree:
  - Trunk: 1 voxel wide, height H (WOOD)
  - Foliage: Layers of cross patterns, decreasing size
  - Top layer: 1x1, Middle: 3x3, Bottom: 5x5 (LEAVES)
  
Oak Tree:
  - Trunk: 1-2 voxels wide, height H (WOOD)
  - Foliage: Rounded blob, 5x5x5 to 7x7x7 (LEAVES)
  - Random variations in foliage shape
  
Palm Tree:
  - Trunk: 1 voxel wide, height H (WOOD)
  - Crown: Cross pattern at top, 5x5x2 (LEAVES)
```

**Small Vegetation:**
- 1-3 voxels tall
- Placed densely in suitable areas

### 5.3 Placement Rules

**Terrain-Based Constraints:**

| Plant Type | Slope Constraint | Height Range (voxels) | Height Range (%) | Soil Type | Density |
|------------|------------------|----------------------|------------------|-----------|---------|
| Pine | < 35° | 77-115 | 60-90% | Dirt/Stone | Sparse |
| Oak | < 30° | 38-90 | 30-70% | Dirt | Medium |
| Palm | < 15° | 13-51 | 10-40% | Sand/Dirt | Sparse |
| Grass | < 25° | 13-102 | 10-80% | Dirt | Dense |
| Bushes | < 30° | 26-77 | 20-60% | Dirt | Medium |

**Additional Rules:**
- No plants on water, stone, or snow surfaces
- No plants on cliffs (slope > 45°)
- Grass near water (within 10 voxels) has higher density
- Trees cannot overlap (minimum 3-voxel separation)
- Vegetation density decreases with altitude

### 5.4 Distribution Algorithm

1. **Grid-based placement:**
   - Divide terrain into cells (e.g., 8x8 voxel cells)
   - Each cell evaluated for plant eligibility
   
2. **Eligibility check:**
   - Surface slope within range?
   - Correct material type?
   - Height within range?
   - Not too close to other plants?
   
3. **Probabilistic placement:**
   - Use seeded random for determinism
   - Plant type selected based on biome-less probability
   - Variation within type (height, size) randomized

---

## 6. Phase 3: Decorations

### 6.1 Decoration Types

**Simple Elements:**
1. **Rocks** (scattered boulders)
   - 1-3 voxel clusters
   - STONE material
   - Placed on slopes and valleys
   
2. **Mushrooms** (fantasy element)
   - 2-4 voxels tall
   - DECORATION material
   - Near trees, in dark areas
   
3. **Flowers** (color variation)
   - 1-2 voxels tall
   - DECORATION material
   - In grass areas

### 6.2 Placement Rules

| Decoration | Slope | Height Range (voxels) | Height Range (%) | Proximity Rules | Density |
|------------|-------|-----------------------|------------------|-----------------|---------|
| Rocks | Any | Any | Any | Avoid water, 2+ voxels from plants | Sparse |
| Mushrooms | < 20° | 26-90 | 20-70% | Within 5 voxels of trees | Rare |
| Flowers | < 15° | 26-77 | 20-60% | In grass areas | Medium |

---

## 7. Deterministic Generation

### 7.1 Seed-Based System

**Implementation:**
```python
class LandscapeGenerator:
    def __init__(self, seed: int):
        self.rng = SeededRandom(seed)
        self.noise_gen = PerlinNoise(seed)
    
    def generate(self) -> VoxelGrid:
        # Same seed = same output
        terrain = self.generate_terrain()
        plants = self.generate_plants()
        decorations = self.generate_decorations()
        return self.combine(terrain, plants, decorations)
```

**Benefits:**
- Reproducible results for debugging
- Users can share seeds for interesting landscapes
- Can regenerate exact landscape from seed alone

**Future Extension:**
- Add "mutation" parameter to vary from base seed
- Allow manual editing with seed as starting point

---

## 8. GUI Application Requirements

### 8.1 User Interface Elements

**Main Window:**
```
┌──────────────────────────────────────────────────┐
│  Procedural Landscape Generator                  │
├──────────────────────────────────────────────────┤
│  Controls Panel                  │  3D Viewport  │
│  ┌─────────────────────┐        │               │
│  │ Seed: [_______] Gen │        │   [Rendered   │
│  │                      │        │    Landscape] │
│  │ ☐ Terrain            │        │               │
│  │ ☐ Plants             │        │               │
│  │ ☐ Decorations        │        │               │
│  │                      │        │               │
│  │ [Generate]           │        │               │
│  │ [Export 3D]          │        │               │
│  │ [Export Data]        │        │               │
│  └─────────────────────┘        │               │
└──────────────────────────────────────────────────┘
```

**Features:**
1. **Seed Input:** Text field for integer seed value
2. **Random Seed Button:** Generate new random seed
3. **Layer Toggles:** Enable/disable terrain, plants, decorations
4. **Generate Button:** Create landscape with current settings
5. **3D Viewport:** Rotate, zoom, pan the generated landscape
6. **Export Options:** Save as 3D model or raw data

### 8.2 Viewport Controls

- **Mouse Orbit:** Left-click drag to rotate camera
- **Zoom:** Scroll wheel or right-click drag
- **Pan:** Middle-click drag or Shift+left-click
- **Reset View:** Button to return to default camera position

### 8.3 Progress Indication

- Show progress bar during generation (terrain → plants → decorations)
- Estimated time remaining (if possible)
- Real-time preview updates (optional)

---

## 9. Data Persistence

### 9.1 Export Formats

**3D Model Export:**
- **OBJ format** (widely compatible, simple)
- **PLY format** (supports vertex colors for materials)
- **GLTF/GLB** (modern, includes materials)

**Data Export:**
- **JSON format:**
  ```json
  {
    "seed": 12345,
    "dimensions": [256, 256, 128],
    "voxels": [
      {"x": 0, "y": 0, "z": 0, "material": "STONE"},
      ...
    ],
    "metadata": {
      "generation_date": "2026-01-10",
      "parameters": {...}
    }
  }
  ```
  
- **Binary format** (more efficient):
  - Custom format or use existing (MagicaVoxel .vox, Qubicle .qb)
  - Smaller file size, faster loading

### 9.2 Save/Load Functionality

**Save:**
- Store complete voxel grid state
- Include generation parameters (seed, enabled layers)
- Timestamp and version info

**Load:**
- Reconstruct voxel grid from file
- Display in viewport
- Allow re-export in different formats

---

## 10. Non-Functional Requirements

### 10.1 Performance

| Metric | Target | Acceptable |
|--------|--------|------------|
| Generation Time | < 30 seconds | < 2 minutes |
| Memory Usage | < 500 MB | < 1 GB |
| Viewport FPS | 30+ fps | 15+ fps |
| Export Time | < 10 seconds | < 30 seconds |

### 10.2 Usability

- **Neurodivergent-friendly design:**
  - Clear, labeled controls
  - Minimal required user input
  - Automated parameter selection (no overwhelming options)
  - Deterministic behavior (same actions = same results)
  
- **Visual clarity:**
  - Distinct material colors in viewport
  - Grid/axis indicators for orientation
  - Simple, uncluttered interface

### 10.3 Reliability

- Graceful error handling (invalid seeds, memory limits)
- Undo capability for generation (save previous state)
- Autosave option for work in progress

### 10.4 Extensibility

- Modular design allows adding new:
  - Material types
  - Plant variations
  - Decoration types
  - Export formats
  
- Plugin system (future consideration)

---

## 11. Development Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up project structure and dependencies
- [ ] Implement voxel data structure
- [ ] Create basic GUI with viewport
- [ ] Implement seeded random number generation
- [ ] Add basic export (OBJ format)

### Phase 2: Terrain (Weeks 3-5)
- [ ] Implement multi-octave noise generation
- [ ] Create heightmap-based terrain
- [ ] Add material layering (stone, dirt, sand)
- [ ] Implement water placement
- [ ] Add seamless tiling
- [ ] Implement cave generation (3D volumetric)
- [ ] Test geological realism

### Phase 3: Plants (Weeks 6-7)
- [ ] Create procedural tree generators (3 types)
- [ ] Implement grass/vegetation placement
- [ ] Add bush generators
- [ ] Implement terrain-based placement rules
- [ ] Add slope and elevation constraints
- [ ] Test plant distribution and density

### Phase 4: Decorations (Week 8)
- [ ] Implement rock placement
- [ ] Add mushroom generation
- [ ] Add flower placement
- [ ] Test overall composition

### Phase 5: Polish (Weeks 9-10)
- [ ] Optimize performance
- [ ] Add progress indicators
- [ ] Implement save/load functionality
- [ ] Add additional export formats
- [ ] User testing and bug fixes
- [ ] Documentation

---

## 12. Success Criteria

### 12.1 Minimum Viable Product (MVP)

The project is successful when it can:
1. Generate a 256×256×H voxel landscape deterministically from a seed
2. Include realistic terrain with hills, valleys, and water
3. Place trees and vegetation following terrain rules
4. Display the result in a 3D viewport
5. Export to at least one 3D format (OBJ)

### 12.2 Full Feature Set

Complete when all phases are implemented:
- All terrain features (including caves)
- All plant types with placement rules
- All decoration types
- Multiple export formats
- Save/load functionality
- Polished GUI

### 12.3 Quality Metrics

- Landscapes look geologically plausible
- No floating terrain or impossible features
- Plants distributed realistically
- Seamless tiling works correctly
- Generation completes within performance targets
- Interface is intuitive and neurodivergent-friendly

---

## 13. Final Decisions (Confirmed)

### 13.1 Core Specifications

**All key decisions have been finalized:**

1. **Maximum Height:** 128 voxels
   - Balanced for performance and visual appeal
   - Allows for dramatic elevation changes
   - Total world size: 256×256×128 voxels

2. **Color Scheme:** Realistic natural colors
   - Stone: Medium gray (#808080)
   - Dirt: Rich brown (#8B5A2B)
   - Grass: Forest green (#228B22)
   - Water: Royal blue (#4169E1)
   - See complete palette in Section 3.3

3. **Rendering Style:** Smooth/interpolated surfaces
   - Marching cubes or similar algorithm
   - Natural, organic appearance
   - Phong shading for realistic lighting
   - NOT blocky/Minecraft-style

4. **Programming Language:** Python
   - Libraries: NumPy, noise, PyVista
   - Excellent for prototyping and 3D visualization
   - Can optimize critical sections later if needed

### 13.2 Future Enhancements (Post-MVP)

- **Biomes:** Different regions with distinct characteristics
- **Weather effects:** Snow accumulation, erosion patterns
- **Time of day:** Lighting variations
- **Animation:** Growing plants, flowing water
- **Multiplayer seeds:** Share and compare landscapes
- **Editing mode:** Manually modify generated landscapes
- **Higher resolution:** 512×512 or larger grids
- **LOD (Level of Detail):** Better performance for large landscapes

---

## 14. Technical Recommendations

### 14.1 Required Libraries (Python)

**Installation command:**
```bash
pip install numpy noise pyvista scipy trimesh
```

**Core Dependencies:**

```
Core Generation:
- numpy (1.24+): Voxel array manipulation and mathematical operations
- noise (1.2+): Perlin/Simplex noise generation
- scipy (1.10+): Advanced mathematical operations and marching cubes

3D Rendering & Visualization:
- pyvista (0.42+): 3D visualization with VTK backend
  * Provides smooth surface extraction (marching cubes)
  * Built-in lighting and camera controls
  * Easy mesh manipulation

GUI:
- tkinter: Built-in with Python, no installation needed
  * Simple and reliable for this use case
  * Cross-platform compatibility
  * Lightweight

Export:
- trimesh (3.23+): Mesh operations and multi-format export
  * Supports OBJ, PLY, GLTF, STL
  * Mesh validation and repair
  * Efficient binary formats

Optional (for optimization):
- numba: JIT compilation for performance-critical loops
- scikit-image: Alternative marching cubes implementation
```

**Why These Libraries:**
- NumPy: Industry standard, essential for voxel grid operations
- PyVista: Best Python library for 3D visualization and smooth surface rendering
- Trimesh: Handles all export formats with minimal code
- Tkinter: Simple GUI without external dependencies

### 14.2 Project Structure

```
procedural_landscape/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── voxel_grid.py
│   │   ├── noise_generator.py
│   │   └── materials.py
│   ├── generators/
│   │   ├── terrain_generator.py
│   │   ├── plant_generator.py
│   │   └── decoration_generator.py
│   ├── rendering/
│   │   ├── viewport.py
│   │   └── mesh_builder.py
│   ├── export/
│   │   ├── obj_exporter.py
│   │   ├── ply_exporter.py
│   │   └── data_exporter.py
│   └── gui/
│       ├── main_window.py
│       └── controls.py
├── tests/
│   └── test_generators.py
├── examples/
│   └── example_seeds.txt
├── requirements.txt
├── README.md
└── main.py
```

---

## 15. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Memory overflow (256³ voxels) | Medium | High | Use sparse arrays, optimize data structure |
| Slow generation time | Medium | Medium | Profile and optimize hot paths, use numba |
| Complex cave generation | High | Medium | Implement as separate phase, can be simple initially |
| Seamless tiling artifacts | Medium | Low | Test edge blending carefully, use proven noise tiling |
| Poor plant distribution | Low | Low | Iterative tuning of placement parameters |

---

## Conclusion

This specification provides a complete roadmap for building a procedural voxel landscape generator. The phased approach allows incremental development and testing, while the deterministic design ensures reproducibility for debugging and artistic control.

The system balances realism (geological constraints, terrain rules) with artistic freedom (procedural variation, stylized rendering), making it suitable for both learning and creative expression.

**Next Steps:**
1. Review and approve this specification
2. Set up development environment
3. Begin Phase 1 implementation
4. Iterate based on testing and feedback
