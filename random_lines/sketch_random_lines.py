"""
Inspired by tutorial:
https://www.generativehut.com/post/generative-art-python-tutorial-for-penplotter
"""
import vsketch
import numpy as np
import datetime
import os


class RandomLinesSketch(vsketch.SketchClass):
    ROWS = vsketch.Param(20, 0)
    COLS = vsketch.Param(25, 0)
    INTERPOLATION_STEPS = vsketch.Param(5,0)
    RND01 = vsketch.Param(0.30, decimals=2)
    RND02 = vsketch.Param(3.00, decimals=2)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=False)
        vsk.scale("cm")

        # outer loop: list(pts) per row
        # inner loop: create (x,y) for each col in current row
        # [ [(0, 0), (0,1), (0,2)], [(1,0),(1,1), (1,2)], ..]
        all_column_pts = [ 
            [(row + vsk.random(self.RND01), col + vsk.random(self.RND02)) for col in range(self.COLS)]
            for row in range(self.ROWS)
        ]

        for idx in range(len(all_column_pts) -1):
            curr = list(zip(*all_column_pts[idx]))
            nxt = list(zip(*all_column_pts[idx+1]))
                       
            x_curr, y_curr = map(np.array, curr)
            x_nxt, y_nxt = map(np.array, nxt)

            for step in range(self.INTERPOLATION_STEPS):
                x_inp = vsk.lerp(x_curr, x_nxt, step/self.INTERPOLATION_STEPS)
                y_inp = vsk.lerp(y_curr, y_nxt, step/self.INTERPOLATION_STEPS)

                vsk.polygon(zip(x_inp, y_inp))
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        vsk.save(os.path.join("output", f"fig_{timestamp}.svg"))
            
    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    RandomLinesSketch.display()
