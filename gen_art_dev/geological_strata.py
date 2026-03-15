"""
Geological Strata — generative art simulating crumpled fabric / eroded terrain.

Visual model
------------
Densely packed horizontal lines displaced vertically by a complex noise
heightmap.  Lines bunch together on steep slopes (creating dark shadow
areas) and spread apart on plateaus (light areas).

The organic, folded quality comes from **domain warping**: the noise
coordinates are themselves distorted by another layer of noise, producing
the characteristic geological / crumpled-fabric look.

Technique
---------
  1. Lay down N horizontal scan-lines across the canvas.
  2. For each point on each line, evaluate a multi-octave noise field
     with domain warping to get a vertical displacement.
  3. Apply an irregular boundary mask (also noise-based) so the edges
     aren't a clean rectangle — they tear and fade organically.
  4. Draw each displaced line as a polyline.

Usage
-----
    python geological_strata.py [seed]     # single render (default 42)
    python geological_strata.py batch      # 8 random variations
"""

import math
import random
import sys

from scripts.generators import BaseGenerator
from scripts.batch_gen import BatchGenerator


# ── Simplex-like 2D noise ────────────────────────────────────────────────────
# Permutation-based gradient noise (compact, no dependencies).

def _build_perm(seed: int):
    """Build a 512-entry permutation table from seed."""
    rng = random.Random(seed)
    p = list(range(256))
    rng.shuffle(p)
    return p + p  # double for wrapping


# 12 gradient vectors for 2D (unit-length, evenly spaced)
_GRADS = [(math.cos(a), math.sin(a)) for a in
          (math.pi * 2 * i / 12 for i in range(12))]


def _noise2(x: float, y: float, perm: list) -> float:
    """
    2D gradient noise in [-1, 1].
    """
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255
    xf = x - math.floor(x)
    yf = y - math.floor(y)

    # Fade curves (6t^5 - 15t^4 + 10t^3)
    u = xf * xf * xf * (xf * (xf * 6.0 - 15.0) + 10.0)
    v = yf * yf * yf * (yf * (yf * 6.0 - 15.0) + 10.0)

    aa = perm[perm[xi] + yi] % 12
    ab = perm[perm[xi] + yi + 1] % 12
    ba = perm[perm[xi + 1] + yi] % 12
    bb = perm[perm[xi + 1] + yi + 1] % 12

    def dot(gi, fx, fy):
        g = _GRADS[gi]
        return g[0] * fx + g[1] * fy

    x1 = dot(aa, xf, yf) + u * (dot(ba, xf - 1, yf) - dot(aa, xf, yf))
    x2 = dot(ab, xf, yf - 1) + u * (dot(bb, xf - 1, yf - 1) - dot(ab, xf, yf - 1))
    return x1 + v * (x2 - x1)


def _fbm(x: float, y: float, perm: list, octaves: int = 6,
         lacunarity: float = 2.0, gain: float = 0.5) -> float:
    """Fractal Brownian Motion: layered noise octaves."""
    total = 0.0
    amplitude = 1.0
    frequency = 1.0
    max_amp = 0.0
    for _ in range(octaves):
        total += _noise2(x * frequency, y * frequency, perm) * amplitude
        max_amp += amplitude
        amplitude *= gain
        frequency *= lacunarity
    return total / max_amp


def _warped_fbm(x: float, y: float, perm: list, perm2: list,
                octaves: int, warp_strength: float, warp_scale: float,
                warp_octaves: int = 3) -> float:
    """
    Domain-warped fBm.
    Evaluates a warp noise field to distort the coordinates before
    sampling the main fBm — this creates the organic folded patterns.
    """
    # First warp layer
    wx = _fbm(x * warp_scale, y * warp_scale, perm2, warp_octaves) * warp_strength
    wy = _fbm(x * warp_scale + 5.2, y * warp_scale + 1.3, perm2, warp_octaves) * warp_strength
    return _fbm(x + wx, y + wy, perm, octaves)


class GeologicalStrata(BaseGenerator):

    def __init__(
        self,
        width: float = 200,
        height: float = 200,
        seed: int = None,

        # ── Line field ───────────────────────────────────────────────────
        num_lines: int = 200,          # number of horizontal scan lines
        x_resolution: int = 300,       # points per line (higher = smoother)

        # ── Displacement ─────────────────────────────────────────────────
        displacement: float = 40.0,    # max vertical displacement (mm)
        noise_scale: float = 0.012,    # base noise frequency
        octaves: int = 6,              # fractal detail layers
        lacunarity: float = 2.0,       # frequency multiplier per octave
        gain: float = 0.50,            # amplitude multiplier per octave

        # ── Domain warping ───────────────────────────────────────────────
        warp_strength: float = 2.5,    # how much the coordinates warp
        warp_scale: float = 0.008,     # warp noise frequency
        warp_octaves: int = 3,         # warp noise detail

        # ── Boundary ─────────────────────────────────────────────────────
        edge_roughness: float = 0.7,   # 0 = clean rect, 1 = very torn
        edge_scale: float = 0.02,      # noise frequency for edge mask
        edge_inset: float = 0.05,      # fraction of canvas to inset edges

        # ── Style ────────────────────────────────────────────────────────
        stroke_width: float = 0.35,    # line weight in px

        **kwargs,
    ):
        super().__init__(width, height, seed, **kwargs)

        self.num_lines = int(num_lines)
        self.x_resolution = int(x_resolution)

        self.displacement = displacement
        self.noise_scale = noise_scale
        self.octaves = int(octaves)
        self.lacunarity = lacunarity
        self.gain = gain

        self.warp_strength = warp_strength
        self.warp_scale = warp_scale
        self.warp_octaves = int(warp_octaves)

        self.edge_roughness = edge_roughness
        self.edge_scale = edge_scale
        self.edge_inset = edge_inset

        self.stroke_width = stroke_width

    def _edge_mask(self, x: float, y: float, perm: list) -> float:
        """
        Returns 0..1 — how much a point should be included.
        Uses smooth distance-to-edge with noise-based irregularity.
        """
        W, H = self.width, self.height
        inset = self.edge_inset

        # Normalized distance from each edge (0 at edge, 1 deep inside)
        dl = x / (W * inset + 1e-6)
        dr = (W - x) / (W * inset + 1e-6)
        dt = y / (H * inset + 1e-6)
        db = (H - y) / (H * inset + 1e-6)
        d = min(dl, dr, dt, db)

        if self.edge_roughness > 0:
            noise_val = _fbm(x * self.edge_scale, y * self.edge_scale, perm, 3)
            d += noise_val * self.edge_roughness * 0.8

        return max(0.0, min(1.0, d))

    def generate(self) -> None:
        W, H = self.width, self.height

        # Build permutation tables (one for main noise, one for warp)
        perm = _build_perm(self.seed)
        perm2 = _build_perm(self.seed + 12345)
        perm_edge = _build_perm(self.seed + 67890)

        sw = f'{self.stroke_width}px'

        for li in range(self.num_lines):
            base_y = (li / (self.num_lines - 1)) * H

            # Build displaced line points
            points = []
            for xi in range(self.x_resolution + 1):
                x = (xi / self.x_resolution) * W
                y = base_y

                # Get displacement from warped noise
                disp = _warped_fbm(
                    x * self.noise_scale,
                    y * self.noise_scale,
                    perm, perm2,
                    self.octaves,
                    self.warp_strength,
                    self.warp_scale / max(self.noise_scale, 1e-6),
                    self.warp_octaves,
                )
                y_displaced = y + disp * self.displacement

                # Edge mask
                mask = self._edge_mask(x, base_y, perm_edge)
                if mask < 0.01:
                    # Outside boundary — break the line
                    if len(points) >= 2:
                        self.builder.add_polyline(points, width=sw)
                    points = []
                    continue

                points.append((x, y_displaced))

            # Draw remaining segment
            if len(points) >= 2:
                self.builder.add_polyline(points, width=sw)

    def describe(self) -> str:
        return (
            f"Geological Strata — {self.num_lines} lines, "
            f"displacement={self.displacement:.0f}mm, "
            f"warp={self.warp_strength:.1f}"
        )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "42"

    if arg == "batch":
        print("Batch mode: generating 8 variations …")
        batch = BatchGenerator(
            GeologicalStrata,
            base_params={"width": 200, "height": 200},
        )
        batch.generate_series("geological_strata", num_variations=8, output_dir="output/batch")

    else:
        seed = int(arg)
        art = GeologicalStrata(
            width=200, height=200, seed=seed,
            num_lines=200, x_resolution=300,
            displacement=40.0, noise_scale=0.012,
            octaves=6, warp_strength=2.5, warp_scale=0.008,
            edge_roughness=0.7, edge_scale=0.02, edge_inset=0.05,
            stroke_width=0.35,
        )
        art.render()
        art.display()
        out = art.save("geological_strata", output_dir="output")
        print(f"\nSeed:  {seed}")
        print(f"Saved: {out['standard']}")
        print(f"       {out['print_optimized']}")
