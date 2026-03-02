"""
Example generator implementations showcasing the template.
These serve as both documentation and test cases.
"""

import math
import random
from scripts.generators import BaseGenerator
from scripts.svg_utils import SvgBuilder


class ConcentricCircles(BaseGenerator):
    """Geometric: Simple concentric circles with parametric control."""
    
    def __init__(self, width=100, height=100, seed=None, 
                 num_circles=10, spacing=5, **kwargs):
        super().__init__(width, height, seed, **kwargs)
        self.num_circles = num_circles
        self.spacing = spacing
    
    def generate(self):
        """Draw concentric circles centered on canvas."""
        cx, cy = self.width / 2, self.height / 2
        max_radius = min(cx, cy) - 5
        
        for i in range(self.num_circles):
            radius = (i + 1) * (max_radius / self.num_circles)
            self.builder.add_circle(cx, cy, radius)
    
    def describe(self):
        return f"Concentric Circles ({self.num_circles} rings)"


class RecursiveTree(BaseGenerator):
    """Organic: Recursive tree branches with random angles and lengths."""
    
    def __init__(self, width=100, height=100, seed=None,
                 depth=8, angle_variance=30, length_ratio=0.7, **kwargs):
        super().__init__(width, height, seed, **kwargs)
        self.depth = depth
        self.angle_variance = angle_variance
        self.length_ratio = length_ratio
    
    def generate(self):
        """Recursive branch drawing."""
        # Start from bottom center, pointing up
        x, y = self.width / 2, self.height - 5
        self._draw_branch(x, y, 90, 20, 0)
    
    def _draw_branch(self, x, y, angle, length, depth):
        """Recursively draw branches."""
        if depth >= self.depth or length < 0.5:
            return
        
        # Calculate end point
        rad = math.radians(angle)
        x2 = x + length * math.cos(rad)
        y2 = y - length * math.sin(rad)
        
        # Draw line
        self.builder.add_line(x, y, x2, y2)
        
        # Recurse with angle variation
        for angle_offset in [-self.angle_variance, self.angle_variance]:
            new_angle = angle + angle_offset
            new_length = length * self.length_ratio
            self._draw_branch(x2, y2, new_angle, new_length, depth + 1)
    
    def describe(self):
        return f"Recursive Tree (depth={self.depth})"


class VoronoiDots(BaseGenerator):
    """Abstract/Mathematical: Random points with surrounding circles."""
    
    def __init__(self, width=100, height=100, seed=None,
                 num_points=12, radius=15, **kwargs):
        super().__init__(width, height, seed, **kwargs)
        self.num_points = num_points
        self.radius = radius
    
    def generate(self):
        """Place random points and draw circles around them."""
        points = []
        
        # Generate random points
        for _ in range(self.num_points):
            x = random.uniform(10, self.width - 10)
            y = random.uniform(10, self.height - 10)
            points.append((x, y))
        
        # Draw circles
        for x, y in points:
            self.builder.add_circle(x, y, self.radius)
        
        # Optional: connect nearby points
        for i, (x1, y1) in enumerate(points):
            for x2, y2 in points[i+1:]:
                dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                if dist < self.radius * 2:
                    self.builder.add_line(x1, y1, x2, y2)
    
    def describe(self):
        return f"Voronoi Dots ({self.num_points} points)"


class GridPattern(BaseGenerator):
    """Geometric: Grid of rotated squares."""
    
    def __init__(self, width=100, height=100, seed=None,
                 grid_size=10, square_size=5, rotation_step=5, **kwargs):
        super().__init__(width, height, seed, **kwargs)
        self.grid_size = grid_size
        self.square_size = square_size
        self.rotation_step = rotation_step
    
    def generate(self):
        """Draw grid of rotated squares."""
        cell_width = self.width / self.grid_size
        cell_height = self.height / self.grid_size
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                cx = col * cell_width + cell_width / 2
                cy = row * cell_height + cell_height / 2
                rotation = (row + col) * self.rotation_step
                
                # Draw rotated square (as polygon)
                points = self._rotated_square(cx, cy, self.square_size, rotation)
                self.builder.add_polygon(points)
    
    @staticmethod
    def _rotated_square(cx, cy, size, rotation_degrees):
        """Return corners of rotated square."""
        rad = math.radians(rotation_degrees)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        half_size = size / 2
        
        corners = [
            (-half_size, -half_size),
            (half_size, -half_size),
            (half_size, half_size),
            (-half_size, half_size),
        ]
        
        rotated = []
        for x, y in corners:
            rx = x * cos_r - y * sin_r + cx
            ry = x * sin_r + y * cos_r + cy
            rotated.append((rx, ry))
        
        return rotated
    
    def describe(self):
        return f"Grid Pattern ({self.grid_size}×{self.grid_size})"


class FlowField(BaseGenerator):
    """Flow-based: Particles following a noise-based flow field."""
    
    def __init__(self, width=100, height=100, seed=None,
                 particle_count=30, speed=1, steps=100, **kwargs):
        super().__init__(width, height, seed, **kwargs)
        self.particle_count = particle_count
        self.speed = speed
        self.steps = steps
    
    def generate(self):
        """Draw particle trails guided by angle field."""
        # Simple: use angle based on x,y position
        for _ in range(self.particle_count):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            
            points = [(x, y)]
            for _ in range(self.steps):
                # Angle based on position (creates flow field effect)
                angle = (x + y) * 0.1 + random.uniform(-0.3, 0.3)
                
                dx = self.speed * math.cos(angle)
                dy = self.speed * math.sin(angle)
                
                x += dx
                y += dy
                
                # Wrap around
                x = x % self.width
                y = y % self.height
                
                points.append((x, y))
            
            # Draw trail
            self.builder.add_polyline(points)
    
    def describe(self):
        return f"Flow Field ({self.particle_count} particles)"


if __name__ == '__main__':
    # Quick test
    print("Pen Plotter Art Examples")
    print("=" * 40)
    
    examples = [
        ConcentricCircles(seed=1),
        RecursiveTree(seed=2),
        VoronoiDots(seed=3),
        GridPattern(seed=4),
        FlowField(seed=5),
    ]
    
    for example in examples:
        example.render()
        print(f"✓ {example.describe()}")
