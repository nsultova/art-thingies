"""
Turbulent Lines — horizontal lines transitioning from chaotic smoke to calm order.

Upper-left corner is the chaos epicenter: lines are displaced with smooth,
high-amplitude noise and drawn with multiple overlapping passes to create
dense, smokey tangles. Moving right and downward, turbulence fades until
lines become perfectly straight.
"""

import math
import random
from scripts.generators import BaseGenerator
from scripts.svg_utils import SvgBuilder


class TurbulentLines(BaseGenerator):
    def __init__(self, width=200, height=200, seed=42,
                 num_lines=45,
                 max_amplitude=18.0,
                 max_frequency=0.15,
                 max_passes=12,
                 resolution=300,
                 chaos_exponent=2.2,
                 octaves=4,
                 vertical_chaos_weight=0.35,
                 horizontal_chaos_weight=0.65,
                 stroke_width='0.35px'):
        super().__init__(width, height, seed,
                         num_lines=num_lines,
                         max_amplitude=max_amplitude,
                         max_frequency=max_frequency,
                         max_passes=max_passes,
                         resolution=resolution,
                         chaos_exponent=chaos_exponent,
                         octaves=octaves,
                         vertical_chaos_weight=vertical_chaos_weight,
                         horizontal_chaos_weight=horizontal_chaos_weight,
                         stroke_width=stroke_width)
        self.num_lines = num_lines
        self.max_amplitude = max_amplitude
        self.max_frequency = max_frequency
        self.max_passes = max_passes
        self.resolution = resolution
        self.chaos_exponent = chaos_exponent
        self.octaves = octaves
        self.vertical_chaos_weight = vertical_chaos_weight
        self.horizontal_chaos_weight = horizontal_chaos_weight
        self.stroke_width = stroke_width

    def _noise_1d(self, x, freq, phase):
        """Simple layered sine-based noise with multiple octaves."""
        val = 0.0
        amp = 1.0
        f = freq
        for _ in range(self.octaves):
            val += amp * math.sin(f * x + phase)
            # Add some non-linearity
            val += amp * 0.5 * math.sin(f * 1.7 * x + phase * 2.3 + 1.1)
            f *= 2.1
            amp *= 0.5
            phase += 3.7
        return val

    def _chaos_factor(self, x_norm, y_norm):
        """
        Compute chaos intensity at a given normalized position (0-1).
        Upper-left = max chaos, lower-right = calm.
        """
        # Horizontal: left=1, right=0
        h_chaos = 1.0 - x_norm
        # Vertical: top=1, bottom=0
        v_chaos = 1.0 - y_norm

        # Weighted combination
        wh = self.horizontal_chaos_weight
        wv = self.vertical_chaos_weight
        combined = (wh * h_chaos + wv * v_chaos) / (wh + wv)

        # Apply exponent for sharper falloff
        return combined ** self.chaos_exponent

    def generate(self):
        builder = self.builder
        w = self.width
        h = self.height

        # Vertical spacing
        margin_top = h * 0.05
        margin_bottom = h * 0.05
        usable_h = h - margin_top - margin_bottom
        spacing = usable_h / (self.num_lines - 1) if self.num_lines > 1 else usable_h

        for line_idx in range(self.num_lines):
            y_base = margin_top + line_idx * spacing
            y_norm = line_idx / max(self.num_lines - 1, 1)

            # Determine number of passes for this line based on vertical chaos
            v_chaos = (1.0 - y_norm) ** self.chaos_exponent
            # More passes at top, fewer at bottom
            num_passes = max(1, int(self.max_passes * v_chaos * 0.8 + 1))

            for pass_idx in range(num_passes):
                # Unique phase offset per pass
                phase_seed = random.random() * 1000.0
                phase2 = random.random() * 1000.0
                amp_variation = 0.6 + random.random() * 0.8  # vary amplitude per pass

                points = []
                for i in range(self.resolution + 1):
                    x_norm = i / self.resolution
                    x = x_norm * w

                    # Chaos factor at this point
                    chaos = self._chaos_factor(x_norm, y_norm)

                    # Amplitude scales with chaos
                    amp = self.max_amplitude * chaos * amp_variation

                    # Frequency scales with chaos (more wiggly in chaotic regions)
                    freq = self.max_frequency * (1.0 + chaos * 3.0)

                    # Compute displacement
                    displacement = amp * self._noise_1d(x, freq, phase_seed)

                    # Add secondary high-frequency detail in very chaotic areas
                    if chaos > 0.3:
                        detail_amp = amp * 0.4 * ((chaos - 0.3) / 0.7)
                        detail_freq = freq * 3.5
                        displacement += detail_amp * math.sin(detail_freq * x + phase2)

                    # Add slight random jitter for organic feel in chaotic areas
                    if chaos > 0.5:
                        jitter = (random.random() - 0.5) * amp * 0.15
                        displacement += jitter

                    y = y_base + displacement
                    points.append((x, y))

                builder.add_polyline(points, stroke='black', width=self.stroke_width)

    def describe(self):
        return "Turbulent Lines — chaos-to-order horizontal line field"


if __name__ == '__main__':
    art = TurbulentLines(width=200, height=200, seed=42)
    art.render()
    art.display()
    art.save('turbulent_lines', output_dir='output')
