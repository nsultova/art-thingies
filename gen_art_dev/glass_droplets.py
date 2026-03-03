"""
Water Droplets on Glass — generative art simulating a rain-covered window.

Visual model
------------
Two populations:
  static beads   — drops stuck to the glass, scattered across the whole surface.
                   Rings are concentric (speed = 0 → no elongation).
  sliding drops  — drops heavy enough to overcome surface tension and slide down.
                   Rings deform into teardrops; a clean trail follows above.

Ring system
-----------
Rings use smooth sine-wave harmonics for organic warp (2, 3, 5 cycles/ring)
instead of per-point Gaussian noise.  This avoids the spiky "rose" look and
gives smooth, blob-like shapes.  Distortion adds a small amount of high-frequency
texture on top.

Wind
----
A single global wind direction (wind_angle degrees from vertical) affects ALL
sliding drops the same way (with ±25 % per-drop magnitude variation).
Positive wind_angle = rightward drift.

Usage
-----
    python glass_droplets.py [seed]    # single render (default 42)
    python glass_droplets.py batch     # 8 random variations
"""

import math
import random
import sys

from scripts.generators import BaseGenerator
from scripts.batch_gen import BatchGenerator


class GlassDroplets(BaseGenerator):

    def __init__(
        self,
        width: float = 210,
        height: float = 297,
        seed: int = None,

        # ── Population ──────────────────────────────────────────────────
        num_drops: int = 50,
        slide_fraction: float = 0.25,   # 0 = all static beads, 1 = all sliding

        # ── Physics (sliding drops) ──────────────────────────────────────
        drop_length: float = 45.0,      # max trail length in mm
        wind_angle: float = 5.0,        # degrees from vertical (+ = right)
        wind_strength: float = 0.25,    # lateral drift intensity
        heaviness: float = 5.0,         # drop size multiplier
        viscosity: float = 0.30,        # 0 = water (fast/elongated), 1 = syrup (slow/round)
        randomness: float = 0.15,       # path jitter (low = smooth glassy path)

        # ── Rings ────────────────────────────────────────────────────────
        ring_count: int = 5,            # concentric rings per drop
        ring_warp: float = 0.40,        # sine-wave warp amplitude
        distortion: float = 0.20,       # fine noise on top of warp

        # ── Satellites ──────────────────────────────────────────────────
        fractal_depth: int = 1,         # generations of satellite drops (0 = none)

        **kwargs,
    ):
        super().__init__(width, height, seed, **kwargs)

        self.num_drops      = int(num_drops)
        self.slide_fraction = float(slide_fraction)

        self.drop_length    = drop_length
        self.wind_angle     = wind_angle
        self.wind_strength  = wind_strength
        self.heaviness      = heaviness
        self.viscosity      = viscosity
        self.randomness     = randomness

        self.ring_count     = int(ring_count)
        self.ring_warp      = ring_warp
        self.distortion     = distortion
        self.fractal_depth  = int(fractal_depth)

    # ── Physics ────────────────────────────────────────────────────────────────

    def _sim_path(self, x0: float, y0: float, wind_vx: float) -> list:
        """Euler-integrate a drop sliding down the glass."""
        path = [(x0, y0)]
        x, y = x0, y0
        vx        = wind_vx
        vy        = 0.05
        dt        = 0.5
        max_steps = int(self.drop_length * 2.5 / dt)
        gravity   = 0.08 * (self.heaviness / 5.0)
        drag      = 0.85 + self.viscosity * 0.12

        for _ in range(max_steps):
            vy += gravity * dt
            vx += wind_vx * 0.008 * dt + random.gauss(0, self.randomness * 0.10) * dt
            vy += random.gauss(0, self.randomness * 0.015) * dt
            vx *= drag
            vy *= drag

            spd     = math.sqrt(vx * vx + vy * vy)
            max_spd = 1.5 * (1.0 - self.viscosity * 0.6)
            if spd > max_spd:
                vx = vx / spd * max_spd
                vy = vy / spd * max_spd

            x += vx * dt
            y += vy * dt
            if y > self.height * 0.97 or x < -self.width * 0.1 or x > self.width * 1.1:
                break
            path.append((x, y))

        return path

    def _smooth_path(self, path: list, iterations: int = 3) -> list:
        """Laplacian smooth — removes high-frequency jitter for a glassy look."""
        p = list(path)
        for _ in range(iterations):
            s = [p[0]]
            for i in range(1, len(p) - 1):
                s.append((
                    0.25 * p[i-1][0] + 0.5 * p[i][0] + 0.25 * p[i+1][0],
                    0.25 * p[i-1][1] + 0.5 * p[i][1] + 0.25 * p[i+1][1],
                ))
            s.append(p[-1])
            p = s
        return p

    # ── Rings ──────────────────────────────────────────────────────────────────

    def _draw_rings(
        self,
        cx: float, cy: float,
        r: float,
        motion_angle: float,
        speed: float,
        rng_seed: int,
        n_rings: int = None,
    ) -> None:
        """
        Draw n_rings concentric rings centred at (cx, cy).

        Warp model
        ----------
        Each ring's radius is modulated by a sum of low-frequency sine harmonics
        (frequencies 2, 3, 5 cycles/ring) with random per-ring phases.
        This gives smooth, organic blob shapes instead of spiky jagged ones.
        A tiny amount of Gaussian noise (distortion param) adds fine texture.

        Teardrop shaping
        ----------------
        v < 0 (trailing edge): elongated proportional to speed × (1 − viscosity)
        v > 0 (leading edge):  slightly rounded/compressed
        At speed = 0 (static beads): rings are pure circles + smooth warp.

        Coordinate frame
        ----------------
        local u  = perpendicular to motion
        local v  = along motion (+ = leading/forward, − = trailing/behind)
        Rotate to world via:
          wx = cx + lx*(−sinA) + ly*cosA
          wy = cy + lx* cosA   + ly*sinA
        """
        if n_rings is None:
            n_rings = self.ring_count

        rng   = random.Random(rng_seed)
        cos_a = math.cos(motion_angle)
        sin_a = math.sin(motion_angle)

        max_elong = 1.0 + speed * max(0.0, 1.5 - self.viscosity * 1.2)

        WARP_FREQS = (2, 3, 5)

        for ri in range(n_rings):
            t      = (ri + 1) / n_rings
            ring_r = r * t
            n_pts  = max(24, int(72 * t))       # smooth polygon

            # Per-ring random phases (deterministic via rng_seed)
            phases   = [rng.uniform(0, 2.0 * math.pi) for _ in WARP_FREQS]
            warp_amp = self.ring_warp * ring_r * 0.10   # per-harmonic amplitude

            pts = []
            for j in range(n_pts):
                theta = 2.0 * math.pi * j / n_pts
                u = math.cos(theta)
                v = math.sin(theta)

                # Smooth sine-wave warp (low-freq harmonics → smooth bumps)
                warp_r = sum(
                    warp_amp * math.sin(f * theta + p)
                    for f, p in zip(WARP_FREQS, phases)
                )
                # Tiny Gaussian noise for fine texture
                warp_r += rng.gauss(0, self.distortion * ring_r * 0.04)

                r_eff = ring_r + warp_r

                # Teardrop elongation along the motion axis
                if v < 0:
                    v_shaped = v * (1.0 + abs(v) * (max_elong - 1.0))
                else:
                    v_shaped = v * (1.0 - v * 0.05)

                lx = r_eff * u
                ly = r_eff * v_shaped

                wx = cx + lx * (-sin_a) + ly * cos_a
                wy = cy + lx *  cos_a   + ly * sin_a
                pts.append((wx, wy))

            pts.append(pts[0])
            self.builder.add_polyline(pts)

    # ── Trail ──────────────────────────────────────────────────────────────────

    def _draw_trail(self, path: list) -> None:
        """Single clean spine — thin line above the drop head."""
        if len(path) < 2:
            return
        self.builder.add_polyline(path, width='0.3px')

    # ── Satellites ─────────────────────────────────────────────────────────────

    def _draw_satellites(self, path: list, parent_r: float, depth: int) -> None:
        """Scatter smaller static-bead drops along the trail (fractal recursion)."""
        if depth <= 0 or not path:
            return

        n_sats = random.randint(1, max(1, self.fractal_depth + 1))

        for _ in range(n_sats):
            idx    = random.randint(0, max(0, len(path) - 3))
            px, py = path[idx]

            if idx + 1 < len(path):
                dx, dy = path[idx+1][0] - px, path[idx+1][1] - py
                l      = math.sqrt(dx * dx + dy * dy) or 1.0
                perp_x, perp_y = -dy / l, dx / l
            else:
                perp_x, perp_y = 1.0, 0.0

            sat_r = parent_r * random.uniform(0.15, 0.45) / depth
            if sat_r < 0.2:
                continue

            side     = 1 if random.random() > 0.5 else -1
            offset_d = parent_r * random.uniform(0.8, 2.5)
            sx = px + perp_x * offset_d * side + random.gauss(0, sat_r * 0.3)
            sy = py + perp_y * offset_d * side + random.gauss(0, sat_r * 0.2)

            sat_rings = max(2, self.ring_count - (self.fractal_depth - depth + 1))
            self._draw_rings(sx, sy, sat_r, math.pi / 2, 0.0,
                             random.randint(0, 99_999), sat_rings)

            if depth > 1 and random.random() < 0.4:
                self._draw_satellites([(sx, sy)], sat_r, depth - 1)

    # ── Main ───────────────────────────────────────────────────────────────────

    def generate(self) -> None:
        W, H = self.width, self.height

        # Global wind vector — same direction for every sliding drop
        wind_rad     = math.radians(self.wind_angle)
        base_wind_vx = math.sin(wind_rad) * self.wind_strength * 2.0

        for drop_i in range(self.num_drops):
            is_sliding = random.random() < self.slide_fraction

            # Size distribution:
            #   static beads  → exponential (many tiny, few large)
            #   sliding drops → lognormal shifted slightly larger
            if is_sliding:
                r = max(1.0, math.exp(random.gauss(0.4, 0.45)) * self.heaviness / 5.0)
                r = min(r, self.heaviness)
                x0 = random.uniform(W * 0.05, W * 0.95)
                y0 = random.uniform(H * 0.03, H * 0.55)
            else:
                rate = 2.5 / max(0.1, self.heaviness)
                r    = max(0.3, -math.log(max(random.random(), 1e-9)) / rate)
                r    = min(r, self.heaviness * 0.6)
                x0   = random.uniform(W * 0.03, W * 0.97)
                y0   = random.uniform(H * 0.03, H * 0.97)

            rng_seed = drop_i * 997 + self.seed % 10_000

            if is_sliding:
                wind_vx = base_wind_vx * random.uniform(0.75, 1.25)
                path    = self._sim_path(x0, y0, wind_vx)
                if len(path) < 4:
                    continue
                path = self._smooth_path(path, iterations=4)

                # Trail stops 2 points before the head (avoids overlap with rings)
                trail_path = path[:-2] if len(path) > 4 else path
                self._draw_trail(trail_path)

                # Head orientation from velocity
                hx, hy     = path[-1]
                look_back  = min(5, len(path) - 1)
                px, py     = path[-1 - look_back]
                dx, dy     = hx - px, hy - py
                angle      = math.atan2(dy, dx)
                speed      = math.sqrt(dx * dx + dy * dy) / look_back

                self._draw_rings(hx, hy, r, angle, speed, rng_seed)

                if self.fractal_depth > 0:
                    self._draw_satellites(trail_path, r, self.fractal_depth)
            else:
                # Static bead: speed = 0 → circular rings with warp only
                self._draw_rings(x0, y0, r, math.pi / 2, 0.0, rng_seed)

    def describe(self) -> str:
        n_slide = round(self.num_drops * self.slide_fraction)
        return (
            f"Glass Droplets — {self.num_drops} drops "
            f"({n_slide} sliding, {self.num_drops - n_slide} static), "
            f"viscosity={self.viscosity:.2f}"
        )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "42"

    if arg == "batch":
        print("Batch mode: generating 8 variations …")
        batch = BatchGenerator(
            GlassDroplets,
            base_params={"width": 210, "height": 297},
        )
        batch.generate_series("glass_droplets", num_variations=8, output_dir="output/batch")

    else:
        seed = int(arg)
        art  = GlassDroplets(
            width=210, height=297, seed=seed,
            num_drops=50,
            slide_fraction=0.25,
            drop_length=45.0,
            wind_angle=5.0,
            wind_strength=0.25,
            heaviness=5.0,
            viscosity=0.30,
            randomness=0.15,
            ring_count=5,
            ring_warp=0.40,
            distortion=0.20,
            fractal_depth=1,
        )
        art.render()
        art.display()
        out = art.save("glass_droplets", output_dir="output")
        print(f"\nSeed:  {seed}")
        print(f"Saved: {out['standard']}")
        print(f"       {out['print_optimized']}")
