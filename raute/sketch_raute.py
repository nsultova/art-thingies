import vsketch
import numpy as np
import datetime
import os

# Example adapted from https://github.com/abey79/vsketch/tree/master/examples

class RauteSketch(vsketch.SketchClass):
    def __init__(self):
        super().__init__()
        self.N = vsketch.Param(value = 30, min_value=1, max_value=100, step=5) 
        self.K = vsketch.Param(value = 5, min_value=1, max_value=30, step=5)
        self.M = vsketch.Param(value = 5, min_value=1, max_value=30, step=5)
        self.rot_mat = None
        self.rot_angle = vsketch.Param(value=180, min_value=0, max_value=360, step=45)
        self.xs = []
        self.ys = []

    def calculate_rot_mat(self, rot_angle=None):
        if rot_angle is None:
            rot_angle = self.rot_angle
        # Define the rotation matrix
        theta = np.radians(rot_angle)
        c, s = np.cos(theta), np.sin(theta)
        self.rot_mat = np.array(((c, -s), (s, c)))
        return self.rot_mat

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        # square    
        vsk.line(0,0,0,1)
        vsk.line(0,1,1,1)
        vsk.line(1,0, 1,1)
        vsk.line(0,0,1,0)

        # self.rot_mat = self.calculate_rot_mat(180)
        # for i, r0 in enumerate(np.linspace(0,1, self.N.value)):
        #     alpha = np.linspace(-np.pi, np.pi, self.K.value)
        #     r = r0 * (1 + 0.5*np.sin(2*alpha * self.M.value*r0))
        #     x, y = r * np.cos(alpha), r * np.sin(alpha)
        #     x1, y1 = self.rot_mat @ [x,y]

        #     # # bc we have sets (x,y), (x1,y1)
        #     # for xi, yi, x1i, y1i in zip(x, y, x1, y1):
        #     #     vsk.polygon([(xi, yi), (-x1i, y1i)])  # Create a path that passes through the points
         
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.getcwd(), "raute/output")
        print(path)
        vsk.save(os.path.join(path, f"fig_{timestamp}.svg"))
        # print(path)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    RauteSketch.display()
