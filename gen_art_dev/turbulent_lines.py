"""
Turbulent Lines — master + child/grandchild bundles + domain warping.

Horizontal lines transition from chaotic smoke to calm order. Chaos is
focused radially from a configurable origin point (default upper-left).
Line spacing can be biased denser toward the top. An optional domain
warping layer (inspired by geological_strata) adds organic folding.
"""

import math
import random
from scripts.generators import BaseGenerator
from scripts.svg_utils import SvgBuilder


# ── 2D gradient noise (for domain warping) ────────────────────────────
def _build_perm(seed):
    rng = random.Random(seed)
    p = list(range(256))
    rng.shuffle(p)
    return p + p

_GRADS = [(math.cos(a), math.sin(a)) for a in (math.pi * 2 * i / 12 for i in range(12))]

def _noise2(x, y, perm):
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255
    xf = x - math.floor(x)
    yf = y - math.floor(y)
    u = xf*xf*xf*(xf*(xf*6-15)+10)
    v = yf*yf*yf*(yf*(yf*6-15)+10)
    aa = perm[perm[xi]+yi] % 12
    ab = perm[perm[xi]+yi+1] % 12
    ba = perm[perm[xi+1]+yi] % 12
    bb = perm[perm[xi+1]+yi+1] % 12
    def dot(gi, fx, fy):
        g = _GRADS[gi]; return g[0]*fx + g[1]*fy
    x1 = dot(aa,xf,yf) + u*(dot(ba,xf-1,yf)-dot(aa,xf,yf))
    x2 = dot(ab,xf,yf-1) + u*(dot(bb,xf-1,yf-1)-dot(ab,xf,yf-1))
    return x1 + v*(x2-x1)

def _fbm(x, y, perm, octaves=6, lac=2.0, gain=0.5):
    total = 0.0; amp = 1.0; freq = 1.0; max_amp = 0.0
    for _ in range(octaves):
        total += _noise2(x*freq, y*freq, perm) * amp
        max_amp += amp; amp *= gain; freq *= lac
    return total / max_amp

def _warped_fbm(x, y, perm, perm2, octaves, warp_str, warp_scale, warp_oct):
    wx = _fbm(x*warp_scale, y*warp_scale, perm2, warp_oct) * warp_str
    wy = _fbm(x*warp_scale+5.2, y*warp_scale+1.3, perm2, warp_oct) * warp_str
    return _fbm(x+wx, y+wy, perm, octaves)


class TurbulentLines(BaseGenerator):
    def __init__(self, width=200, height=200, seed=42,
                 num_lines=45,
                 num_bumps=25,
                 max_amplitude=12.0,
                 smoothing=0.5,
                 max_passes=14,
                 spacing_decay=0.0,
                 child_spread=0.35,
                 child_freq_scale=0.10,
                 child_octaves=2,
                 gc_count=0,
                 gc_spread=0.20,
                 gc_freq_scale=0.15,
                 gc_octaves=3,
                 gc_amp_decay=0.6,
                 chaos_origin_x=0.0,
                 chaos_origin_y=0.0,
                 chaos_radius=0.85,
                 chaos_exponent=2.2,
                 warp_strength=0.0,
                 warp_scale=0.015,
                 warp_octaves=3,
                 stroke_width='0.30px'):
        super().__init__(width, height, seed)
        self.num_lines = num_lines
        self.num_bumps = num_bumps
        self.max_amplitude = max_amplitude
        self.smoothing = smoothing
        self.max_passes = max_passes
        self.spacing_decay = spacing_decay
        self.child_spread = child_spread
        self.child_freq_scale = child_freq_scale
        self.child_octaves = child_octaves
        self.gc_count = gc_count
        self.gc_spread = gc_spread
        self.gc_freq_scale = gc_freq_scale
        self.gc_octaves = gc_octaves
        self.gc_amp_decay = gc_amp_decay
        self.chaos_origin_x = chaos_origin_x
        self.chaos_origin_y = chaos_origin_y
        self.chaos_radius = chaos_radius
        self.chaos_exponent = chaos_exponent
        self.warp_strength = warp_strength
        self.warp_scale = warp_scale
        self.warp_octaves = warp_octaves
        self.stroke_width = stroke_width
        self.RES = 350

    def _chaos_factor(self, xn, yn):
        dx = xn - self.chaos_origin_x
        dy = yn - self.chaos_origin_y
        dist = math.sqrt(dx*dx + dy*dy)
        normalized = min(1, dist / max(self.chaos_radius, 0.01))
        return max(0, 1 - normalized) ** self.chaos_exponent

    @staticmethod
    def _catmull_rom(y0, y1, y2, y3, t):
        t2 = t*t; t3 = t2*t
        return 0.5*((2*y1)+(-y0+y2)*t+(2*y0-5*y1+4*y2-y3)*t2+(-y0+3*y1-3*y2+y3)*t3)

    def _sample_curve(self, ctrl):
        n = len(ctrl); out = []
        for i in range(self.RES + 1):
            pos = (i/self.RES)*(n-1); idx = min(int(pos), n-2); frac = pos - idx
            out.append(self._catmull_rom(
                ctrl[max(0,idx-1)], ctrl[idx],
                ctrl[min(n-1,idx+1)], ctrl[min(n-1,idx+2)], frac))
        return out

    def _smooth_ctrl(self, pts):
        n = len(pts); out = [0.0]*n
        for i in range(n):
            prev = pts[i-1] if i > 0 else pts[i]
            nxt = pts[i+1] if i < n-1 else pts[i]
            out[i] = pts[i]*(1-self.smoothing) + (prev+nxt)/2*self.smoothing
        return out

    def _derive_ctrl(self, parent, spread, amp_scale, y_norm):
        n = len(parent); out = [0.0]*n
        for k in range(n):
            xn = k/(n-1); chaos = self._chaos_factor(xn, y_norm)
            out[k] = parent[k] + (random.random()*2-1)*self.max_amplitude*spread*amp_scale*chaos
        if self.smoothing > 0: out = self._smooth_ctrl(out)
        return out

    def _wiggle(self, x, freq, phase, octaves):
        val=0; amp=1; f=freq; ph=phase
        for _ in range(octaves):
            val += amp*math.sin(f*x+ph); f*=1.9; amp*=0.45; ph+=2.7
        return val

    def _add_wiggle(self, curve, freq, phase, octaves, amp_factor, y_norm):
        out = []
        for i, v in enumerate(curve):
            xn = i/self.RES; x = xn*self.width
            chaos = self._chaos_factor(xn, y_norm)
            out.append(v + self._wiggle(x, freq*(1+chaos*2), phase, octaves)*self.max_amplitude*amp_factor*chaos)
        return out

    def _compute_line_ys(self):
        margin_y = self.height * 0.04
        usable_h = self.height - 2*margin_y
        ys = []
        for li in range(self.num_lines):
            t = li / (self.num_lines - 1)
            if self.spacing_decay > 0:
                t = (math.exp(self.spacing_decay*t)-1) / (math.exp(self.spacing_decay)-1)
            ys.append(margin_y + t*usable_h)
        return ys

    def generate(self):
        builder = self.builder
        w = self.width; h = self.height
        line_ys = self._compute_line_ys()

        # Domain warp tables
        perm = perm2 = None
        if self.warp_strength > 0:
            perm = _build_perm(self.seed + 111)
            perm2 = _build_perm(self.seed + 222)

        for li in range(self.num_lines):
            y_base = line_ys[li]
            y_norm = y_base / h

            # Master control points
            num_ctrl = max(3, self.num_bumps)
            master = [(random.random()*2-1)*self.max_amplitude*self._chaos_factor(ci/(num_ctrl-1), y_norm)
                      for ci in range(num_ctrl)]
            smoothed = master
            if self.smoothing > 0:
                for _ in range(2): smoothed = self._smooth_ctrl(smoothed)

            avg_chaos = self._chaos_factor(0.25, y_norm)
            n_children = max(1, round(self.max_passes * avg_chaos))

            for ci in range(n_children):
                child_phase = random.random() * 1000
                child_ctrl = self._derive_ctrl(smoothed, self.child_spread, 1.0, y_norm)
                child_curve = self._sample_curve(child_ctrl)
                final = self._add_wiggle(child_curve, self.child_freq_scale, child_phase, self.child_octaves, 0.08, y_norm)

                points = []
                for i in range(self.RES + 1):
                    x = (i/self.RES)*w; y = y_base + final[i]
                    if self.warp_strength > 0 and perm:
                        chaos = self._chaos_factor(i/self.RES, y_norm)
                        warp_amt = self.warp_strength * chaos
                        if warp_amt > 0.01:
                            y += _warped_fbm(x*self.warp_scale, y*self.warp_scale,
                                             perm, perm2, self.warp_octaves,
                                             warp_amt, self.warp_scale/0.015, self.warp_octaves) * warp_amt
                    points.append((x, y))
                builder.add_polyline(points, stroke='black', width=self.stroke_width)

                # Grandchildren
                if self.gc_count > 0:
                    n_gc = max(0, round(self.gc_count * avg_chaos))
                    for gi in range(n_gc):
                        gc_phase = random.random() * 1000
                        gc_ctrl = self._derive_ctrl(child_ctrl, self.gc_spread, self.gc_amp_decay, y_norm)
                        gc_curve = self._sample_curve(gc_ctrl)
                        gc_final = self._add_wiggle(gc_curve, self.gc_freq_scale, gc_phase, self.gc_octaves, 0.06, y_norm)

                        points = []
                        for i in range(self.RES + 1):
                            x = (i/self.RES)*w; y = y_base + gc_final[i]
                            if self.warp_strength > 0 and perm:
                                chaos = self._chaos_factor(i/self.RES, y_norm)
                                warp_amt = self.warp_strength * chaos
                                if warp_amt > 0.01:
                                    y += _warped_fbm(x*self.warp_scale, y*self.warp_scale,
                                                     perm, perm2, self.warp_octaves,
                                                     warp_amt, self.warp_scale/0.015, self.warp_octaves) * warp_amt
                            points.append((x, y))
                        builder.add_polyline(points, stroke='black', width=self.stroke_width)

    def describe(self):
        return "Turbulent Lines — master + child/grandchild bundles + domain warping"


if __name__ == '__main__':
    art = TurbulentLines(width=200, height=200, seed=42)
    art.render()
    art.display()
    art.save('turbulent_lines', output_dir='output')
