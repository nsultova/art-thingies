import vsketch
import numpy as np
import datetime
import os

# Example adapted from https://github.com/abey79/vsketch/tree/master/examples

class RauteSketch(vsketch.SketchClass):
    N = vsketch.Param(value = 30, min_value=1, max_value=100, step=5) 
    print(f"N: {N}")
    K = vsketch.Param(value = 5, min_value=1, max_value=30, step=5) #K=4 also nice
    M = vsketch.Param(value = 5, min_value=1, max_value=30, step=5)
    # rot_mat = None
    # rot_angle = vsketch.Param(value=180, min_value=0, max_value=360, step=45)
    xs = []
    ys = []

    # def calculate_rot_mat(self, rot_angle=None):
    #     if rot_angle is None:
    #         rot_angle = self.rot_angle
    #     # Define the rotation matrix
    #     theta = np.radians(rot_angle)
    #     c, s = np.cos(theta), np.sin(theta)
    #     self.rot_mat = np.array(((c, -s), (s, c)))
    #     return self.rot_mat

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("7cm")

        # self.rot_mat = self.calculate_rot_mat(180)
        for i, r0 in enumerate(np.linspace(0,1, self.N)):
            with vsk.pushMatrix():
                alpha = np.linspace(-np.pi, np.pi, self.K)
                r = r0 * (1 + 0.5*np.sin(2*alpha * self.M*r0))
                x, y = r * np.cos(alpha), r * np.sin(alpha)
                vsk.rotate(180)
                x1,y1 = x,y 
                vsk.rotate(180) #reset
                # x1, y1 = self.rot_mat @ [x,y]
                # print(f"x {x}")
                # print(f"y: {y}")
                self.xs.append(x)
                self.xs.append(x1)
                self.ys.append(y)
                self.ys.append(-y1)


        for (x,y) in zip(self.xs,self.ys):
            # print(f"x: {x}, len(x): {len(x)}")
            for i in range(len(x) -1):
                vsk.line(x[i],y[i], x[i+1], y[i+1])
                print(f"x[{i}]: {x[i]},  y[{i}]: {y[i]} | x1[{i+1}]: {x[i+1]}  y1[{i+1}]]")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # path = os.path.join(os.getcwd(), "raute/output")
        # print(path)
        # vsk.save(os.path.join(path, f"fig_{timestamp}.svg"))
        # print(path)
        vsk.save(f"fig_{timestamp}.svg")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    RauteSketch.display()
