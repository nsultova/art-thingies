"""
Turbulent Lines v2 — eddy-based strand bundles.

Each horizontal "line" is a bundle of strands. Along each line, discrete
eddy events (localized turbulence hotspots) are scattered. When a strand
passes through an eddy, it gets high-frequency, high-amplitude displacement
unique to that strand+eddy combination, creating tangled knots.

Outside eddies, strands follow a gentle base wave and converge to a single
line in calm regions. The number of eddies and active strands scales with
a chaos gradient (upper-left = max chaos, lower-right = calm).
"""

import math
import random
from scripts.generators import BaseGenerator
from scripts.svg_utils import SvgBuilder


class TurbulentLines(BaseGenerator):
    def __init__(self, width=200, height=200, seed=42,
                 num_lines=48,
                 max_strands=14,
                 resolution=400,
                 eddy_density=3.0,
                 eddy_radius=10.0,
                 eddy_amp=16.0,
                 eddy_freq=1.5,
                 eddy_octaves=3,
                 base_amp=1.5,
                 base_freq=0.04,
                 chaos_exponent=2.0,
                 h_weight=0.60,
                 v_weight=0.40,
                 stroke_width='0.3px'):
        super().__init__(width, height, seed,
                         num_lines=num_lines,
                         max_strands=max_strands,
                         resolution=resolution,
                         eddy_density=eddy_density,
                         eddy_radius=eddy_radius,
                         eddy_amp=eddy_amp,
                         eddy_freq=eddy_freq,
                         eddy_octaves=eddy_octaves,
                         base_amp=base_amp,
                         base_freq=base_freq,
                         chaos_exponent=chaos_exponent,
                         h_weight=h_weight,
                         v_weight=v_weight,
                         stroke_width=stroke_width)
        self.num_lines = num_lines
        self.max_strands = max_strands
        self.resolution = resolution
        self.eddy_density = eddy_density
        self.eddy_radius = eddy_radius
        self.eddy_amp = eddy_amp
        self.eddy_freq = eddy_freq
        self.eddy_octaves = eddy_octaves
        self.base_amp = base_amp
        self.base_freq = base_freq
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

    def _sine_noise(self, x, freq, phase, octaves):
        val = 0.0
        amp = 1.0
        f = freq
        ph = phase
        for _ in range(octaves):
            val += amp * math.sin(f * x + ph)
            val += amp * 0.3 * math.sin(f * 1.73 * x + ph * 2.1 + 0.7)
            f *= 2.15
            amp *= 0.55
            ph += 4.1
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

            # Scatter eddies along this line
            eddies = []
            eddy_step = 1.5
            x = 0
            while x < w:
                xn = x / w
                chaos = self._chaos_factor(xn, y_norm)
                prob = chaos * self.eddy_density * (eddy_step / w) * 2.5
                if random.random() < prob:
                    e_radius = self.eddy_radius * (0.5 + random.random()) * (0.5 + chaos * 0.5)
                    e_amp = self.eddy_amp * (0.4 + random.random() * 0.6) * chaos
                    e_freq = self.eddy_freq * (0.6 + random.random() * 0.8)
                    e_phase = random.random() * 100
                    eddies.append({
                        'cx': x, 'radius': e_radius,
                        'amp': e_amp, 'freq': e_freq, 'phase': e_phase
                    })
                x += eddy_step

            # Number of strands
            avg_chaos = self._chaos_factor(0.3, y_norm)
            n_strands = max(1, round(self.max_strands * avg_chaos))

            for si in range(n_strands):
                strand_phase = random.random() * 1000
                strand_y_off = (random.random() - 0.5) * spacing * 0.08
                strand_amp_scale = 0.6 + random.random() * 0.8

                points = []
                for i in range(self.resolution + 1):
                    xn = i / self.resolution
                    x = xn * w
                    chaos = self._chaos_factor(xn, y_norm)

                    # Base wave
                    dy = self.base_amp * chaos * self._sine_noise(x, self.base_freq, strand_phase, 2)
                    dy += strand_y_off * chaos

                    # Eddy contributions
                    for e in eddies:
                        dist = abs(x - e['cx'])
                        influence = e['radius'] * 2.5
                        if dist < influence:
                            t = dist / influence
                            envelope = 0.5 * (1 + math.cos(math.pi * t))
                            local_phase = e['phase'] + si * 7.31 + strand_phase * 0.01
                            displacement = self._sine_noise(x, e['freq'], local_phase, self.eddy_octaves)
                            dy += e['amp'] * strand_amp_scale * envelope * displacement

                            # Micro-turbulence in eddy core
                            if t < 0.4:
                                micro_env = 1 - (t / 0.4)
                                micro_phase = local_phase + si * 3.77 + 100
                                micro = (math.sin(e['freq'] * 4.5 * x + micro_phase)
                                         + 0.5 * math.sin(e['freq'] * 7.2 * x + micro_phase * 1.3))
                                dy += e['amp'] * 0.3 * strand_amp_scale * micro_env * micro

                    points.append((x, y_base + dy))

                builder.add_polyline(points, stroke='black', width=self.stroke_width)

    def describe(self):
        return "Turbulent Lines v2 — eddy-based strand bundles"


if __name__ == '__main__':
    art = TurbulentLines(width=200, height=200, seed=42)
    art.render()
    art.display()
    art.save('turbulent_lines_v2', output_dir='output')
