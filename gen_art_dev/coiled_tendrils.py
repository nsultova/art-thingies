"""
Coiled Tendrils — a central spiral with organic ribbed tendrils.

Each tendril is rendered as a tube with dense perpendicular cross-hatching,
creating a segmented/coiled appearance inspired by coiled wire sculptures.
"""

import math
import random
from scripts.generators import BaseGenerator
from scripts.svg_utils import SvgBuilder


class CoiledTendrils(BaseGenerator):
    def __init__(self, width=210, height=297, seed=42,
                 spiral_cx_pct=0.45, spiral_cy_pct=0.62,
                 spiral_turns=7, spiral_spacing=2.8,
                 num_tendrils=14, tendril_length=180,
                 tube_width=5.0, hatch_spacing=0.6,
                 curvature_strength=0.04, curvature_smooth=12,
                 width_variation=0.4, taper=0.15):
        super().__init__(width, height, seed)
        self.spiral_cx = width * spiral_cx_pct
        self.spiral_cy = height * spiral_cy_pct
        self.spiral_turns = spiral_turns
        self.spiral_spacing = spiral_spacing
        self.num_tendrils = num_tendrils
        self.tendril_length = tendril_length
        self.tube_width = tube_width
        self.hatch_spacing = hatch_spacing
        self.curvature_strength = curvature_strength
        self.curvature_smooth = curvature_smooth
        self.width_variation = width_variation
        self.taper = taper

    def describe(self):
        return "Coiled Tendrils — ribbed spiral tubes"

    def _generate_spiral_path(self):
        """Generate an Archimedean spiral as a list of (x, y) points."""
        points = []
        max_theta = self.spiral_turns * 2 * math.pi
        steps = int(max_theta / 0.02)
        for i in range(steps + 1):
            theta = (i / steps) * max_theta
            r = self.spiral_spacing * theta / (2 * math.pi)
            x = self.spiral_cx + r * math.cos(theta)
            y = self.spiral_cy + r * math.sin(theta)
            points.append((x, y))
        return points

    def _generate_tendril_path(self, start_x, start_y, start_angle, length, rng):
        """Generate an organic tendril path using smooth random-walk curvature."""
        step_size = 0.5
        num_steps = int(length / step_size)

        # Pre-generate curvature noise and smooth it
        raw_noise = [rng.random() * 2 - 1 for _ in range(num_steps)]
        smoothed = self._smooth(raw_noise, self.curvature_smooth)

        points = [(start_x, start_y)]
        angle = start_angle
        x, y = start_x, start_y

        for i in range(num_steps):
            angle += smoothed[i] * self.curvature_strength
            x += step_size * math.cos(angle)
            y += step_size * math.sin(angle)
            points.append((x, y))

        return points

    def _smooth(self, data, window):
        """Simple moving-average smoothing."""
        if window < 2:
            return data
        result = []
        for i in range(len(data)):
            lo = max(0, i - window)
            hi = min(len(data), i + window + 1)
            result.append(sum(data[lo:hi]) / (hi - lo))
        return result

    def _draw_ribbed_tube(self, path, tube_width, builder):
        """Draw perpendicular cross-hatch lines along a path to create ribbed tube effect."""
        if len(path) < 3:
            return

        # Walk along the path, placing hatch lines at regular arc-length intervals
        accum = 0.0
        for i in range(1, len(path) - 1):
            px, py = path[i]
            prev_x, prev_y = path[i - 1]

            # Accumulate arc length
            dx = px - prev_x
            dy = py - prev_y
            seg_len = math.sqrt(dx * dx + dy * dy)
            accum += seg_len

            if accum < self.hatch_spacing:
                continue
            accum = 0.0

            # Compute tangent from neighbors for smoother normals
            next_x, next_y = path[min(i + 1, len(path) - 1)]
            tx = next_x - prev_x
            ty = next_y - prev_y
            t_len = math.sqrt(tx * tx + ty * ty)
            if t_len < 1e-8:
                continue
            tx /= t_len
            ty /= t_len

            # Normal (perpendicular)
            nx, ny = -ty, tx

            # Taper: reduce width at start and end of path
            t = i / len(path)
            taper_factor = 1.0
            if t < self.taper:
                taper_factor = t / self.taper
            elif t > 1.0 - self.taper:
                taper_factor = (1.0 - t) / self.taper
            taper_factor = max(0.05, taper_factor)

            half_w = tube_width * 0.5 * taper_factor

            x1 = px + nx * half_w
            y1 = py + ny * half_w
            x2 = px - nx * half_w
            y2 = py - ny * half_w

            builder.add_line(x1, y1, x2, y2)

    def generate(self):
        builder = self.builder
        rng = random.Random(self.seed)

        # 1. Generate and draw the central spiral
        spiral = self._generate_spiral_path()
        spiral_width = self.tube_width * 0.7
        self._draw_ribbed_tube(spiral, spiral_width, builder)

        # 2. Generate tendrils from the outer portion of the spiral
        spiral_len = len(spiral)
        # Pick spawn points from the outer 60% of the spiral
        spawn_start = int(spiral_len * 0.4)

        for t_idx in range(self.num_tendrils):
            # Pick a spawn point
            spawn_frac = rng.uniform(0.0, 1.0)
            spawn_i = spawn_start + int(spawn_frac * (spiral_len - spawn_start - 2))
            spawn_i = min(spawn_i, spiral_len - 2)

            sx, sy = spiral[spawn_i]
            # Compute tangent at spawn point
            nx_pt, ny_pt = spiral[spawn_i + 1]
            px_pt, py_pt = spiral[max(0, spawn_i - 1)]
            tang_angle = math.atan2(ny_pt - py_pt, nx_pt - px_pt)

            # Add some angular spread: tendrils fan out
            angle_offset = rng.uniform(-0.6, 0.6)
            start_angle = tang_angle + angle_offset

            # Vary tendril length
            length = self.tendril_length * rng.uniform(0.5, 1.5)

            # Vary tube width per tendril
            tw = self.tube_width * rng.uniform(1.0 - self.width_variation,
                                                1.0 + self.width_variation)

            path = self._generate_tendril_path(sx, sy, start_angle, length, rng)
            self._draw_ribbed_tube(path, tw, builder)


if __name__ == '__main__':
    art = CoiledTendrils(width=210, height=297, seed=42)
    art.render()
    art.save('coiled_tendrils', output_dir='output')
    art.display()
