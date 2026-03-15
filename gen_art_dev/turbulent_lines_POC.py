"""
Turbulent Lines — master curve + child strand bundles.

For each horizontal line, a smooth MASTER CURVE is generated via
Catmull-Rom interpolation through random control points (amplitudes
modulated by chaos gradient). Then N CHILD STRANDS are spawned that
closely follow the master with slight independent deviations, creating
tight bundles of lines that trace each bump's shape — like smoke
clinging to each wave.
"""

import math
import random
from scripts.generators import BaseGenerator
from scripts.svg_utils import SvgBuilder


class TurbulentLines(BaseGenerator):
    def __init__(self, width=200, height=200, seed=42,
                 num_lines=45,
                 max_amplitude=12.0,
                 control_spacing=8,
                 smoothing=0.5,
                 max_passes=14,
                 child_spread=0.35,
                 child_freq_scale=0.10,
                 child_octaves=2,
                 resolution=350,
                 chaos_exponent=2.2,
                 h_weight=0.65,
                 v_weight=0.35,
                 stroke_width='0.30px'):
        super().__init__(width, height, seed,
                         num_lines=num_lines,
                         max_amplitude=max_amplitude,
                         control_spacing=control_spacing,
                         smoothing=smoothing,
                         max_passes=max_passes,
                         child_spread=child_spread,
                         child_freq_scale=child_freq_scale,
                         child_octaves=child_octaves,
                         resolution=resolution,
                         chaos_exponent=chaos_exponent,
                         h_weight=h_weight,
                         v_weight=v_weight,
                         stroke_width=stroke_width)
        self.num_lines = num_lines
        self.max_amplitude = max_amplitude
        self.control_spacing = control_spacing
        self.smoothing = smoothing
        self.max_passes = max_passes
        self.child_spread = child_spread
        self.child_freq_scale = child_freq_scale
        self.child_octaves = child_octaves
        self.resolution = resolution
        self.chaos_exponent = chaos_exponent
        self.h_weight = h_weight
        self.v_weight = v_weight
        self.stroke_width = stroke_width

    def _chaos_factor(self, xn, yn):
        hc = 1.0 - xn
        vc = 1.0 - yn
        wt = self.h_weight + self.v_weight
        combined = (self.h_weight * hc + self.v_weight * vc) / wt if wt > 0 else 0
        return max(0, min(1, combined)) ** self.chaos_exponent

    @staticmethod
    def _catmull_rom(y0, y1, y2, y3, t):
        t2 = t * t
        t3 = t2 * t
        return 0.5 * (
            (2 * y1) +
            (-y0 + y2) * t +
            (2 * y0 - 5 * y1 + 4 * y2 - y3) * t2 +
            (-y0 + 3 * y1 - 3 * y2 + y3) * t3
        )

    def _generate_smooth_curve(self, ctrl_pts, num_samples):
        n = len(ctrl_pts)
        out = []
        for i in range(num_samples + 1):
            t = i / num_samples
            pos = t * (n - 1)
            idx = min(int(pos), n - 2)
            frac = pos - idx
            y0 = ctrl_pts[max(0, idx - 1)]
            y1 = ctrl_pts[idx]
            y2 = ctrl_pts[min(n - 1, idx + 1)]
            y3 = ctrl_pts[min(n - 1, idx + 2)]
            out.append(self._catmull_rom(y0, y1, y2, y3, frac))
        return out

    def _smooth_points(self, pts):
        n = len(pts)
        temp = [0.0] * n
        for i in range(n):
            prev = pts[i - 1] if i > 0 else pts[i]
            nxt = pts[i + 1] if i < n - 1 else pts[i]
            temp[i] = pts[i] * (1 - self.smoothing) + (prev + nxt) / 2 * self.smoothing
        return temp

    def _child_wiggle(self, x, freq, phase, octaves):
        val = 0.0
        amp = 1.0
        f = freq
        ph = phase
        for _ in range(octaves):
            val += amp * math.sin(f * x + ph)
            f *= 1.9
            amp *= 0.45
            ph += 2.7
        return val

    def generate(self):
        builder = self.builder
        w = self.width
        h = self.height

        margin_y = h * 0.04
        usable_h = h - 2 * margin_y
        spacing = usable_h / (self.num_lines - 1) if self.num_lines > 1 else usable_h

        for li in range(self.num_lines):
            y_base = margin_y + li * spacing
            y_norm = li / max(self.num_lines - 1, 1)

            # Build master control points
            num_ctrl = max(3, int(math.ceil(w / self.control_spacing)) + 1)
            ctrl_pts = []
            for ci in range(num_ctrl):
                xn = ci / (num_ctrl - 1)
                chaos = self._chaos_factor(xn, y_norm)
                amp = self.max_amplitude * chaos
                ctrl_pts.append((random.random() * 2 - 1) * amp)

            # Smooth control points
            if self.smoothing > 0:
                for _ in range(2):
                    ctrl_pts = self._smooth_points(ctrl_pts)

            master_curve = self._generate_smooth_curve(ctrl_pts, self.resolution)

            # Number of children based on chaos
            avg_chaos = self._chaos_factor(0.25, y_norm)
            n_children = max(1, round(self.max_passes * avg_chaos))

            for ci in range(n_children):
                child_phase = random.random() * 1000

                # Child control points: master + small random offset
                child_ctrl = []
                for k in range(num_ctrl):
                    xn = k / (num_ctrl - 1)
                    chaos = self._chaos_factor(xn, y_norm)
                    offset = (random.random() * 2 - 1) * self.max_amplitude * self.child_spread * chaos
                    child_ctrl.append(ctrl_pts[k] + offset)

                if self.smoothing > 0:
                    child_ctrl = self._smooth_points(child_ctrl)

                child_curve = self._generate_smooth_curve(child_ctrl, self.resolution)

                points = []
                for i in range(self.resolution + 1):
                    xn = i / self.resolution
                    x = xn * w
                    chaos = self._chaos_factor(xn, y_norm)

                    dy = child_curve[i]
                    wiggle = self._child_wiggle(
                        x, self.child_freq_scale * (1 + chaos * 2),
                        child_phase, self.child_octaves
                    )
                    dy += wiggle * self.max_amplitude * 0.08 * chaos

                    points.append((x, y_base + dy))

                builder.add_polyline(points, stroke='black', width=self.stroke_width)

    def describe(self):
        return "Turbulent Lines — master curve + child strand bundles"


if __name__ == '__main__':
    art = TurbulentLines(width=200, height=200, seed=42)
    art.render()
    art.display()
    art.save('turbulent_lines', output_dir='output')
