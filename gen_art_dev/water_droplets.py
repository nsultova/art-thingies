"""
Water Droplets – Generative art simulating ripples on a puddle.

Models the visual pattern of multiple drops hitting a still water surface:
  • Concentric ripple rings with exponential spacing (inner rings tighter)
  • Fluid distortion via superimposed sine waves on each ring
  • Wave interference between drops (sinusoidal cross-drop perturbation)
  • Secondary micro-droplets scattered around impacts (circles or distorted rings)
  • Fully parametric – adjust everything below or via constructor kwargs

Usage:
    python water_droplets.py [seed]          # renders with given seed (default 42)
    python water_droplets.py batch           # generates 8 random variations
"""

import math
import random
import sys
from pathlib import Path

from scripts.generators import BaseGenerator
from scripts.batch_gen import BatchGenerator


# ─── Main generator ───────────────────────────────────────────────────────────

class WaterDroplets(BaseGenerator):
    """
    Simulates water droplets hitting a puddle surface.

    Parameters
    ----------
    width, height       : canvas size in mm
    seed                : reproducibility seed (None = random)

    # Drop layout
    num_drops           : number of impact sites
    max_rings           : max ripple rings per drop (scaled by drop 'age')

    # Ring geometry
    ring_spacing        : initial gap between innermost rings (mm)
    ring_spacing_growth : exponential growth factor per ring (1.0 = even, 1.1 = spreading)

    # Distortion
    distortion          : amplitude of ring wobble (mm)
    distortion_freqs    : tuple of angular frequencies for wobble (cycles per full circle)
    distortion_growth   : how quickly distortion increases per ring index (0 = flat)

    # Wave interference
    interference_strength : amplitude of cross-drop wave perturbation (mm)
    interference_wavelength_factor : wavelength as a multiple of ring_spacing

    # Secondary droplets
    secondary_drops        : micro-splashes per drop
    secondary_rings        : rings per micro-splash
    secondary_ring_spacing : spacing between secondary rings (mm)
    secondary_dist_min     : min scatter distance (fraction of ring_spacing)
    secondary_dist_max     : scatter radius scale (added to ring_spacing*2, multiplied by 8)
    secondary_distortion   : ring wobble amplitude; 0 = perfect concentric circles
    secondary_dist_freq    : angular frequency of secondary ring distortion
    secondary_dist_growth  : how distortion amplitude grows per ring index

    # Impact center
    impact_rings        : tight rings drawn right at the impact point
    impact_ring_spacing : spacing between impact rings (fraction of ring_spacing)

    # Rendering
    ring_points         : polygon resolution (higher = smoother curves)
    """

    def __init__(
        self,
        width: float = 160,
        height: float = 160,
        seed: int = None,

        # Drop layout
        num_drops: int = 4,
        max_rings: int = 11,

        # Ring geometry
        ring_spacing: float = 4.0,
        ring_spacing_growth: float = 1.11,

        # Distortion
        distortion: float = 1.4,
        distortion_freqs: tuple = (3, 7, 13),
        distortion_growth: float = 0.05,

        # Wave interference
        interference_strength: float = 0.65,
        interference_wavelength_factor: float = 2.4,

        # Secondary droplets
        secondary_drops: int = 5,
        secondary_rings: int = 3,
        secondary_ring_spacing: float = 0.9,
        secondary_dist_min: float = 0.7,
        secondary_dist_max: float = 1.4,
        secondary_distortion: float = 0.0,
        secondary_dist_freq: int = 5,
        secondary_dist_growth: float = 0.1,

        # Impact center
        impact_rings: int = 3,
        impact_ring_spacing: float = 0.22,

        # Rendering
        ring_points: int = 200,

        **kwargs,
    ):
        super().__init__(width, height, seed, **kwargs)

        self.num_drops = num_drops
        self.max_rings = max_rings

        self.ring_spacing = ring_spacing
        self.ring_spacing_growth = ring_spacing_growth

        self.distortion = distortion
        self.distortion_freqs = list(distortion_freqs)
        self.distortion_growth = distortion_growth

        self.interference_strength = interference_strength
        self.interference_wavelength_factor = interference_wavelength_factor

        self.secondary_drops = secondary_drops
        self.secondary_rings = secondary_rings
        self.secondary_ring_spacing = secondary_ring_spacing
        self.secondary_dist_min = secondary_dist_min
        self.secondary_dist_max = secondary_dist_max
        self.secondary_distortion = secondary_distortion
        self.secondary_dist_freq = secondary_dist_freq
        self.secondary_dist_growth = secondary_dist_growth

        self.impact_rings = impact_rings
        self.impact_ring_spacing = impact_ring_spacing

        self.ring_points = ring_points

    # ── Main algorithm ───────────────────────────────────────────────────────

    def generate(self) -> None:
        # Build list of drops with positions, age, and per-drop phase offsets
        drops = []
        for _ in range(self.num_drops):
            x = random.uniform(self.width * 0.15, self.width * 0.85)
            y = random.uniform(self.height * 0.15, self.height * 0.85)
            age = random.uniform(0.4, 1.0)          # fraction of rings visible
            # Random phase per distortion frequency — gives each drop unique wobble
            phases = [random.uniform(0, 2 * math.pi) for _ in self.distortion_freqs]
            drops.append({"x": x, "y": y, "age": age, "phases": phases})

        # Render each drop
        for drop in drops:
            cx, cy = drop["x"], drop["y"]
            n_rings = max(2, int(self.max_rings * drop["age"]))

            # Ripple rings, innermost to outermost
            for ring_idx in range(n_rings):
                base_r = self.ring_spacing * (self.ring_spacing_growth ** ring_idx)
                self._draw_ring(cx, cy, base_r, ring_idx, drop, drops)

            # Tight impact cluster at center
            self._draw_impact_center(cx, cy)

            # Micro-splashes scattered around impact
            self._draw_secondary_drops(cx, cy)

    # ── Ring drawing ─────────────────────────────────────────────────────────

    def _draw_ring(
        self, cx: float, cy: float, base_r: float,
        ring_idx: int, drop: dict, all_drops: list,
    ) -> None:
        """Draw one distorted ripple ring as a closed polygon."""
        n = self.ring_points
        phases = drop["phases"]
        n_freqs = len(self.distortion_freqs)

        # Distortion amplitude grows slightly with ring index
        dist_amp = self.distortion * (1.0 + self.distortion_growth * ring_idx)

        # Interference wavelength
        wavelength = self.ring_spacing * self.interference_wavelength_factor

        points = []
        for i in range(n):
            theta = 2 * math.pi * i / n
            r = base_r

            # ── Fluid distortion: superimposed sine waves ──────────────────
            # Dividing by n_freqs keeps total amplitude = distortion param
            for freq, phase in zip(self.distortion_freqs, phases):
                r += (dist_amp / n_freqs) * math.sin(freq * theta + phase)

            # ── Wave interference from other drops ────────────────────────
            # Use the undistorted ring position as the sampling point
            px = cx + base_r * math.cos(theta)
            py = cy + base_r * math.sin(theta)
            for other in all_drops:
                if other is drop:
                    continue
                dx = px - other["x"]
                dy = py - other["y"]
                dist = math.sqrt(dx * dx + dy * dy)
                # Cosine wave: constructive where drops' wave fronts align
                r += self.interference_strength * math.cos(
                    2 * math.pi * dist / wavelength
                )

            # Final Cartesian point
            points.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))

        self.builder.add_polygon(points)

    def _draw_impact_center(self, cx: float, cy: float) -> None:
        """Tight concentric rings right at the impact point (crown splash)."""
        gap = self.ring_spacing * self.impact_ring_spacing
        for i in range(1, self.impact_rings + 1):
            self.builder.add_circle(cx, cy, i * gap)

    def _draw_secondary_drops(self, cx: float, cy: float) -> None:
        """Micro-splashlets scattered around the main impact zone."""
        for _ in range(self.secondary_drops):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(
                self.ring_spacing * self.secondary_dist_min,
                self.ring_spacing * 2 + self.secondary_dist_max * 8,
            )
            sx = cx + dist * math.cos(angle)
            sy = cy + dist * math.sin(angle)

            if not (0 <= sx <= self.width and 0 <= sy <= self.height):
                continue

            # Per-drop random phase offsets give each micro-drop unique wobble
            ph0 = random.uniform(0, 2 * math.pi)
            ph1 = random.uniform(0, 2 * math.pi)

            for j in range(1, self.secondary_rings + 1):
                base_r   = j * self.secondary_ring_spacing
                dist_amp = self.secondary_distortion * (1 + self.secondary_dist_growth * (j - 1))

                if dist_amp <= 0:
                    # Default: perfect concentric circles
                    self.builder.add_circle(sx, sy, base_r)
                else:
                    # Distorted ring — polygon with superimposed sine waves
                    n_pts  = max(32, int(self.ring_points * 0.35))
                    points = []
                    for k in range(n_pts):
                        theta = 2 * math.pi * k / n_pts
                        r = base_r
                        r += dist_amp       * math.sin(self.secondary_dist_freq       * theta + ph0)
                        r += dist_amp * 0.4 * math.sin(self.secondary_dist_freq * 2.1 * theta + ph1)
                        points.append((sx + r * math.cos(theta), sy + r * math.sin(theta)))
                    self.builder.add_polygon(points)

    # ─────────────────────────────────────────────────────────────────────────

    def describe(self) -> str:
        return (
            f"Water Droplets — {self.num_drops} drops, "
            f"max {self.max_rings} rings, "
            f"distortion={self.distortion:.1f}, "
            f"interference={self.interference_strength:.2f}"
        )


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "42"

    if arg == "batch":
        # Generate 8 random-seed variations with default parameters
        print("Batch mode: generating 8 variations...")
        batch = BatchGenerator(WaterDroplets, base_params={"width": 160, "height": 160})
        batch.generate_series("puddle", num_variations=8, output_dir="output/batch")

    else:
        seed = int(arg)

        art = WaterDroplets(
            width=160,
            height=160,
            seed=seed,

            # ── Adjust these to taste ──────────────────────────────────────
            num_drops=4,                     # how many drops land on the puddle
            max_rings=11,                    # max concentric ripple rings per drop
            ring_spacing=4.0,               # mm – inner ring gap
            ring_spacing_growth=1.11,       # >1 = rings spread outward exponentially
            distortion=1.4,                 # mm – amplitude of ring wobble
            distortion_freqs=(3, 7, 13),    # angular frequencies of wobble
            distortion_growth=0.05,         # how wobble grows ring-to-ring
            interference_strength=0.65,     # mm – strength of cross-drop wave bending
            interference_wavelength_factor=2.4,
            secondary_drops=5,              # micro-splashes per impact
            secondary_rings=3,              # rings on each micro-splash
            secondary_ring_spacing=0.9,     # mm – secondary ring spacing
            secondary_distortion=0.0,       # 0 = perfect circles; >0 = wobbly rings
            secondary_dist_freq=5,          # lobe count for distorted secondary rings
            secondary_dist_growth=0.1,      # distortion grows per ring index
            impact_rings=3,                 # tiny rings right at impact center
            ring_points=200,                # polygon smoothness (higher = smoother)
        )

        art.render()
        art.display()

        out = art.save("water_droplets", output_dir="output")
        print(f"\nSeed: {seed}")
        print(f"Saved: {out['standard']}")
        print(f"       {out['print_optimized']}")
