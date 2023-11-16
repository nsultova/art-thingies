import vsketch
import numpy as np
import datetime
import os

# Example adapted from https://github.com/abey79/vsketch/tree/master/examples

class NoiseBezierSketch(vsketch.SketchClass):
    N = vsketch.Param(150, 0) 
    freq = vsketch.Param(0.03, decimals=3) 
    drift = vsketch.Param(0.06, decimals=2) # offset

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        t = np.arange(self.N) * self.freq
        perlin = vsk.noise(t, np.arange(8) * 1000)

        for i,offset in enumerate(np.arange(self.N) * self.drift):
            vsk.bezier(*(perlin[i]* 10 + offset))

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.getcwd(), "random_lines/output")
        print(path)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    NoiseBezierSketch.display()
