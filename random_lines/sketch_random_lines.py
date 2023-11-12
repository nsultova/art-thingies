import vsketch
import numpy as np

INTERPOLATION_STEPS = 9

class RandomLinesSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=False)
        vsk.scale("cm")

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")
        allColumnsPoints = []
        for row in range(20):
            columnPoints = []
            for col in range(25):
                x = row + vsk.random(1.5)
                y = col + vsk.random(1)
                # vsk.point(x,y)
                columnPoints.append((x,y))
            allColumnsPoints.append(columnPoints)
        
        for idx in range(len(allColumnsPoints) -1):
            currentColumnPoints = allColumnsPoints[idx]
            nextColumnPoints = allColumnsPoints[idx+1]

            curr = list(zip(*currentColumnPoints))
            x_curr = np.array(curr[0]) # (x1,x2,x3,…)
            y_curr = np.array(curr[1]) # (y1,y2,y3,…)

            nxt = list(zip(*nextColumnPoints))
            x_nxt = np.array(nxt[0])
            y_nxt = np.array(nxt[1])

            for step in range(INTERPOLATION_STEPS):
                x_inp = vsk.lerp(x_curr, x_nxt, step/INTERPOLATION_STEPS)
                y_inp = vsk.lerp(y_curr, y_nxt, step/INTERPOLATION_STEPS)

                coords_inp = zip(x_inp, y_inp)
                vsk.polygon(coords_inp)
            


    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    RandomLinesSketch.display()
