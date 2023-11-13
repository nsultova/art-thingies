import vsketch
import numpy as np
import datetime
import os

# Example adapted from https://github.com/abey79/vsketch/tree/master/examples

class NoiseBezierSketch(vsketch.SketchClass):
    N = vsketch.Param(100, 0) 
    freq = vsketch.Param(0.03, decimals=3) 
    drift = vsketch.Param(0.06, decimals=2) # offset

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        t = np.arange(self.N) * self.freq
        perlin = vsk.noise(t, np.arange(8) * 1000)

        for i in range(self.N):
            offset = i * self.drift
            vsk.bezier(
                perlin[i, 0] * 10 + offset,
                perlin[i, 1] * 10 + offset,
                perlin[i, 2] * 10 + offset,
                perlin[i, 3] * 10 + offset,
                perlin[i, 4] * 10 + offset,
                perlin[i, 5] * 10 + offset,
                perlin[i, 6] * 10 + offset,
                perlin[i, 7] * 10 + offset,
            )
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        vsk.save(os.path.join("output", f"fig_{timestamp}.svg"))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    NoiseBezierSketch.display()
