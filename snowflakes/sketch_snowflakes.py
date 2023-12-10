import vsketch
import numpy as np

class SnowflakesSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)
    # num arms of snowflake
    symmetry_number = vsketch.Param(value = 6, min_value=1, max_value=10, step=1) 
    variance_branching_angle = vsketch.Param(value=1, min_value=1, max_value=10, step=1)
    radius = vsketch.Param(value=200, min_value=100, max_value=300, step=50)
    # recursion stop condition
    stop_at_len = vsketch.Param(value=2, min_value=1, max_value=5, step=1)
    branches = [] #convert 

    #drawing parameters elsewhere
    def generate_branch(self, origin, length, angle, stop, var_angle):
        if len < self.stop_at_len:
            return
        
        if tmp_branch is None:
            tmp_branch = []

        random_angle = np.random.uniform(-np.pi/self.variance_branching_angle, np.pi/self.variance_branching_angle)
        end = origin + np.array([len * np.cos(angle), len * np.sin(angle)])
        tmp_branch.append((origin,end))
        #plt.plot([origin[0], end[0]], [origin[1], end[1]], color='white', linewidth=thickness)
        self.generate_branch(origin, length/2, angle - random_angle, self.stop_at_len, self.variance_branching_angle)
        self.generate_branch(origin, length/2, angle + random_angle, self.stop_at_len, self.variance_branching_angle)

        return np.array(tmp_branch)

    # def generate_snowflake(self, sym_num, var_angle, radius, stop):
    #     np.random.seed(255)
    #     for i in range(sym_num):
    #         branch = self.generate_branch(np.array([0,0]), self.radius, (2 * np.pi / self.symmetry_number) * i, self.stop_at_len, self.variance_branching_angle)
    #         self.branches.extend(branch)

    def generate_snowflake(self):
       np.random.seed(255)
       self.branches = [self.generate_branch(np.array([0,0]), self.radius, (2 * np.pi / self.symmetry_number) * i, self.stop_at_len, self.variance_branching_angle) for i in range(self.symmetry_number)]


    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")
        for branch in self.branches:
           for origin, end in branch:
               vsk.line(origin, end)


    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    SnowflakesSketch.display()

