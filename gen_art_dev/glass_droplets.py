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
instead of per-point Gaussian noise.  This gives smooth blob shapes.
Distortion adds a small amount of high-frequency texture on top.

Fluid dynamics
--------------
  Stick-slip  — real drops on glass don't slide smoothly: surface contact-angle
                hysteresis pins the drop until enough energy builds up, then it
                lurches forward.  The stick_slip param (0–1) controls how often
                this happens and how severe the velocity resets are.
  Capillary   — surface irregularities cause subtle lateral drift even without
                wind.  Controlled by the randomness param.

Secondary droplets
------------------
  Sliding drops leave a trail of small bead-drops behind them (Rayleigh-Plateau
  capillary breakup of the thin film).  sec_count controls how many; sec_rings
  controls their ring structure (1 = single circle dot, N = concentric rings);
  sec_scatter controls perpendicular spread; sec_randomness blends from evenly
  spaced (0) to fully random positions (1) along the trail.

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
        drop_length: float = 60.0,      # max trail length in mm
        heaviness: float = 8.0,         # drop size multiplier (bigger = larger drops)
        viscosity: float = 0.30,        # 0 = water (fast/elongated), 1 = syrup (slow/round)
        randomness: float = 0.15,       # surface-irregularity jitter on path
        stick_slip: float = 0.25,       # 0 = smooth glide, 1 = jerky stick-slip motion

        # ── Rings ────────────────────────────────────────────────────────
        ring_count: int = 6,            # concentric rings per drop
        ring_warp: float = 0.00,        # sine-wave warp amplitude (0 = perfect circles)
        distortion: float = 0.00,       # fine sine-harmonic texture on top of warp (0 = off)

        # ── Secondary droplets ───────────────────────────────────────────
        sec_count: int = 12,            # beads left along the trail
        sec_rings: int = 1,             # rings per secondary drop (1 = single circle)
        sec_scatter: float = 1.2,       # perpendicular scatter (0 = on trail)
        sec_randomness: float = 0.30,   # 0 = evenly spaced, 1 = fully random
        sec_size: float = 0.65,         # size scale relative to parent drop

        # ── Fractal satellites ───────────────────────────────────────────
        fractal_depth: int = 1,

        **kwargs,
    ):
        super().__init__(width, height, seed, **kwargs)

        self.num_drops      = int(num_drops)
        self.slide_fraction = float(slide_fraction)

        self.drop_length    = drop_length
        self.heaviness      = heaviness
        self.viscosity      = viscosity
        self.randomness     = randomness
        self.stick_slip     = stick_slip

        self.ring_count     = int(ring_count)
        self.ring_warp      = ring_warp
        self.distortion     = distortion

        self.sec_count      = int(sec_count)
        self.sec_rings      = int(max(1, sec_rings))
        self.sec_scatter    = sec_scatter
        self.sec_randomness = sec_randomness
        self.sec_size       = sec_size

        self.fractal_depth  = int(fractal_depth)

    # ── Physics ────────────────────────────────────────────────────────────────

    def _sim_path(self, x0: float, y0: float) -> list:
        """
        Euler-integrate a drop sliding down the glass.

        No external wind — lateral drift comes from surface irregularities
        (randomness param).  Stick-slip events (stick_slip param) momentarily
        pin the drop and reset velocity, producing the characteristic
        stuttering / lurch pattern seen on real glass.
        """
        path = [(x0, y0)]
        x, y  = x0, y0
        vx    = 0.0
        vy    = 0.05
        dt    = 0.5
        max_steps = int(self.drop_length * 2.5 / dt)
        gravity   = 0.08 * (self.heaviness / 5.0)
        drag      = 0.85 + self.viscosity * 0.12

        for _ in range(max_steps):
            # Stick-slip: contact-angle hysteresis pins drop, then releases
            if self.stick_slip > 0 and random.random() < self.stick_slip * 0.04:
                vx *= 0.05
                vy *= 0.05

            vy += gravity * dt
            # Surface irregularities → subtle lateral jitter
            vx += random.gauss(0, self.randomness * 0.10) * dt
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
        """Laplacian smooth — removes high-frequency jitter."""
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
        Concentric rings with smooth sine-wave warp + teardrop elongation.
        speed = 0  →  pure circles + warp (static beads / secondary drops)
        speed > 0  →  teardrop: trailing edge elongated
        """
        if n_rings is None:
            n_rings = self.ring_count

        rng   = random.Random(rng_seed)
        cos_a = math.cos(motion_angle)
        sin_a = math.sin(motion_angle)
        max_elong = 1.0 + speed * max(0.0, 1.5 - self.viscosity * 1.2)

        FREQS_COARSE = (2, 3, 5)       # ring_warp: large organic bumps
        FREQS_FINE   = (6, 9, 13)      # distortion: finer ripple, still smooth

        for ri in range(n_rings):
            t      = (ri + 1) / n_rings
            ring_r = r * t
            n_pts  = max(24, int(72 * t))

            amp_c    = self.ring_warp  * ring_r * 0.25
            amp_f    = self.distortion * ring_r * 0.10
            phases_c = [rng.uniform(0, 2.0 * math.pi) for _ in FREQS_COARSE]
            phases_f = [rng.uniform(0, 2.0 * math.pi) for _ in FREQS_FINE]

            pts = []
            for j in range(n_pts):
                theta = 2.0 * math.pi * j / n_pts
                u = math.cos(theta)
                v = math.sin(theta)

                warp_r = (
                    sum(amp_c * math.sin(f * theta + p) for f, p in zip(FREQS_COARSE, phases_c))
                  + sum(amp_f * math.sin(f * theta + p) for f, p in zip(FREQS_FINE,   phases_f))
                )
                r_eff = ring_r + warp_r

                v_shaped = (v * (1.0 + abs(v) * (max_elong - 1.0))
                            if v < 0 else v * (1.0 - v * 0.05))

                lx = r_eff * u
                ly = r_eff * v_shaped
                wx = cx + lx * (-sin_a) + ly * cos_a
                wy = cy + lx *  cos_a   + ly * sin_a
                pts.append((wx, wy))

            pts.append(pts[0])
            self.builder.add_polyline(pts)

    # ── Trail ──────────────────────────────────────────────────────────────────

    def _draw_trail(self, path: list) -> None:
        if len(path) >= 2:
            self.builder.add_polyline(path, width='0.3px')

    # ── Secondary droplets ─────────────────────────────────────────────────────

    def _draw_secondary_droplets(self, path: list, base_r: float) -> None:
        """
        Scatter small bead drops along/near the trail.

        sec_rings = 1  →  each bead is a single circle (the baseline)
        sec_rings > 1  →  each bead becomes concentric rings
        sec_scatter    →  perpendicular spread from the trail line
        sec_randomness →  0 = evenly spaced along trail, 1 = fully random
        """
        if self.sec_count <= 0 or not path:
            return

        for i in range(self.sec_count):
            # Blend between evenly-spaced (t_even) and fully random (rand)
            t_even = (i + 0.5) / self.sec_count
            t      = t_even * (1.0 - self.sec_randomness) + random.random() * self.sec_randomness
            t      = max(0.0, min(0.999, t))

            idx    = int(t * (len(path) - 1))
            px, py = path[min(idx, len(path) - 1)]

            # Perpendicular direction at this point on the path
            if idx + 1 < len(path):
                dx, dy = path[idx+1][0] - px, path[idx+1][1] - py
                l      = math.sqrt(dx * dx + dy * dy) or 1.0
                perp_x, perp_y = -dy / l, dx / l
            else:
                perp_x, perp_y = 1.0, 0.0

            scatter = random.gauss(0, self.sec_scatter * base_r * 0.8)
            sx = px + perp_x * scatter
            sy = py + perp_y * scatter

            sec_r = max(0.15, base_r * self.sec_size * random.uniform(0.10, 0.30))
            self._draw_rings(sx, sy, sec_r, math.pi / 2, 0.0,
                             random.randint(0, 99_999), self.sec_rings)

    # ── Fractal satellites ─────────────────────────────────────────────────────

    def _draw_satellites(self, path: list, parent_r: float, depth: int) -> None:
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

        for drop_i in range(self.num_drops):
            is_sliding = random.random() < self.slide_fraction
            rng_seed   = drop_i * 997 + self.seed % 10_000

            if is_sliding:
                r  = max(1.0, math.exp(random.gauss(0.4, 0.45)) * self.heaviness / 5.0)
                r  = min(r, self.heaviness)
                x0 = random.uniform(W * 0.05, W * 0.95)
                y0 = random.uniform(H * 0.03, H * 0.55)
            else:
                rate = 2.5 / max(0.1, self.heaviness)
                r    = max(0.3, -math.log(max(random.random(), 1e-9)) / rate)
                r    = min(r, self.heaviness * 0.6)
                x0   = random.uniform(W * 0.03, W * 0.97)
                y0   = random.uniform(H * 0.03, H * 0.97)

            if is_sliding:
                path = self._sim_path(x0, y0)
                if len(path) < 4:
                    continue
                path = self._smooth_path(path, iterations=4)

                trail_path = path[:-2] if len(path) > 4 else path
                self._draw_trail(trail_path)
                self._draw_secondary_droplets(trail_path, r)

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
                self._draw_rings(x0, y0, r, math.pi / 2, 0.0, rng_seed)

    def describe(self) -> str:
        n_slide = round(self.num_drops * self.slide_fraction)
        return (
            f"Glass Droplets — {self.num_drops} drops "
            f"({n_slide} sliding, {self.num_drops - n_slide} static), "
            f"viscosity={self.viscosity:.2f}, stick_slip={self.stick_slip:.2f}"
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
            num_drops=50,        slide_fraction=0.25,
            drop_length=60.0,    heaviness=8.0,
            viscosity=0.30,      randomness=0.15,  stick_slip=0.25,
            ring_count=6,        ring_warp=0.00,   distortion=0.00,
            sec_count=12,        sec_rings=1,      sec_scatter=1.2,
            sec_randomness=0.30, sec_size=0.65,
            fractal_depth=1,
        )
        art.render()
        art.display()
        out = art.save("glass_droplets", output_dir="output")
        print(f"\nSeed:  {seed}")
        print(f"Saved: {out['standard']}")
        print(f"       {out['print_optimized']}")
