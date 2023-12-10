import vsketch


class SnowflakesSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)
    # num arms of snowflake
    symmetry_number = vsketch.Param(value = 6, min_value=1, max_value=10, step=1) 
    variance_branching_angle = vsketch.Param(value=1, min_value=1, max_value=10, step=1)
    radius = vsketch.Param(value=200, min_value=100, max_value=300, step=50)
    # recursion stop condition
    stop_at_len = vsketch.Param(value=2, min_value=1, max_value=5, step=1)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    SnowflakesSketch.display()
