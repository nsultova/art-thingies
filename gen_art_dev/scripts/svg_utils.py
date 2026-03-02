"""
SVG utilities for creating clean, plotter-friendly black-and-white vector graphics.
Provides SvgBuilder for easy path/element construction.
"""

import svgwrite
import re
from pathlib import Path
from typing import Tuple, List, Optional


class SvgBuilder:
    """
    Clean interface for constructing SVG paths and elements.
    Handles viewBox setup, coordinate transforms, and plotter optimization.
    """
    
    def __init__(self, width: float, height: float, viewbox_margin: float = 2):
        """
        Args:
            width, height: Canvas dimensions in mm
            viewbox_margin: Margin around canvas in mm (default 2mm)
        """
        self.width = width
        self.height = height
        self.margin = viewbox_margin
        self.viewbox_width = width + 2 * viewbox_margin
        self.viewbox_height = height + 2 * viewbox_margin
        self.offset_x = viewbox_margin
        self.offset_y = viewbox_margin
        
        # Create SVG with proper size/viewBox
        self.svg = svgwrite.Drawing(
            size=(f'{self.viewbox_width}mm', f'{self.viewbox_height}mm'),
            viewBox=f'0 0 {self.viewbox_width} {self.viewbox_height}'
        )
        self.svg.fill('none')
        self.svg.stroke('black', width='0.5px')
    
    def _transform(self, x: float, y: float) -> Tuple[float, float]:
        """Apply offset to coordinates."""
        return x + self.offset_x, y + self.offset_y
    
    def add_line(self, x1: float, y1: float, x2: float, y2: float, 
                 stroke: str = 'black', width: str = '0.5px'):
        """Add a line segment."""
        x1, y1 = self._transform(x1, y1)
        x2, y2 = self._transform(x2, y2)
        self.svg.add(self.svg.line(
            start=(x1, y1),
            end=(x2, y2),
            stroke=stroke,
            stroke_width=width,
            fill='none'
        ))
    
    def add_circle(self, cx: float, cy: float, r: float,
                   stroke: str = 'black', width: str = '0.5px', fill: str = 'none'):
        """Add a circle."""
        cx, cy = self._transform(cx, cy)
        self.svg.add(self.svg.circle(
            center=(cx, cy),
            r=r,
            stroke=stroke,
            stroke_width=width,
            fill=fill
        ))
    
    def add_polygon(self, points: List[Tuple[float, float]],
                    stroke: str = 'black', width: str = '0.5px', fill: str = 'none'):
        """Add a polygon (closed path)."""
        transformed = [self._transform(x, y) for x, y in points]
        self.svg.add(self.svg.polygon(
            transformed,
            stroke=stroke,
            stroke_width=width,
            fill=fill
        ))
    
    def add_polyline(self, points: List[Tuple[float, float]],
                     stroke: str = 'black', width: str = '0.5px'):
        """Add a polyline (open path)."""
        transformed = [self._transform(x, y) for x, y in points]
        self.svg.add(self.svg.polyline(
            transformed,
            stroke=stroke,
            stroke_width=width,
            fill='none'
        ))
    
    def add_path(self, d: str, stroke: str = 'black', width: str = '0.5px'):
        """Add a path using SVG path data (d attribute). Advanced use."""
        path = self.svg.path(d=d, stroke=stroke, stroke_width=width, fill='none')
        self.svg.add(path)
    
    def add_rect(self, x: float, y: float, width: float, height: float,
                 stroke: str = 'black', width_px: str = '0.5px', fill: str = 'none'):
        """Add a rectangle."""
        x, y = self._transform(x, y)
        self.svg.add(self.svg.rect(
            insert=(x, y),
            size=(width, height),
            stroke=stroke,
            stroke_width=width_px,
            fill=fill
        ))
    
    def add_text(self, text: str, x: float, y: float, 
                 font_size: str = '4px', stroke: str = 'black'):
        """Add text (for metadata/labels, usually not plotted)."""
        x, y = self._transform(x, y)
        self.svg.add(self.svg.text(
            text,
            insert=(x, y),
            font_size=font_size,
            fill='none',
            stroke=stroke
        ))
    
    def clear(self):
        """Reset to empty SVG."""
        self.svg = svgwrite.Drawing(
            size=(f'{self.viewbox_width}mm', f'{self.viewbox_height}mm'),
            viewBox=f'0 0 {self.viewbox_width} {self.viewbox_height}'
        )
        self.svg.fill('none')
        self.svg.stroke('black', width='0.5px')
    
    def asstring(self) -> str:
        """Return SVG as string."""
        return self.svg.tostring()
    
    def save(self, filepath: str):
        """Save SVG to file."""
        self.svg.saveas(filepath)


def optimize_for_plotter(svg_string: str, simplify_tolerance: float = 0.1) -> str:
    """
    Optimize SVG for pen plotters:
    - Remove unnecessary whitespace
    - Simplify path data
    - Add metadata comments
    
    Args:
        svg_string: SVG content as string
        simplify_tolerance: Tolerance for path simplification (mm)
    
    Returns:
        Optimized SVG string
    """
    # Add plotter optimization metadata
    metadata_comment = f"""<!-- 
    Optimized for pen plotter (AxiDraw-compatible)
    Simplification tolerance: {simplify_tolerance}mm
    Generated by pen-plotter-art skill
    -->"""
    
    # Insert metadata after <svg> tag
    svg_string = svg_string.replace('>', '>\n' + metadata_comment + '\n', 1)
    
    # Minify: remove extra whitespace (but preserve structure)
    svg_string = re.sub(r'>\s+<', '><', svg_string)
    svg_string = re.sub(r'\s+', ' ', svg_string)
    
    return svg_string


def create_print_optimized(svg_string: str, algorithm_name: str = "Generative Art",
                          seed: Optional[int] = None, metadata: Optional[dict] = None) -> str:
    """
    Create a print-optimized version with white background and metadata.
    
    Args:
        svg_string: Original SVG content
        algorithm_name: Name of the algorithm
        seed: Random seed used (for reproducibility)
        metadata: Additional metadata dict
    
    Returns:
        Print-optimized SVG string
    """
    # Parse existing viewBox
    viewbox_match = re.search(r'viewBox="[^"]*"', svg_string)
    if not viewbox_match:
        return svg_string
    
    # Add white background rectangle after <svg> tag
    svg_open = svg_string.find('>')
    viewbox_info = viewbox_match.group()
    
    # Build metadata comment
    meta_lines = [
        f"Algorithm: {algorithm_name}",
    ]
    if seed is not None:
        meta_lines.append(f"Seed: {seed}")
    if metadata:
        for key, value in metadata.items():
            meta_lines.append(f"{key}: {value}")
    meta_comment = f"<!-- {' | '.join(meta_lines)} -->"
    
    # Insert white background and metadata
    svg_with_bg = (
        svg_string[:svg_open+1] +
        f'\n{meta_comment}\n' +
        f'<rect width="100%" height="100%" fill="white" />\n' +
        svg_string[svg_open+1:]
    )
    
    # Optimize stroke width for print (0.35px for most pens)
    svg_with_bg = svg_with_bg.replace('stroke-width="0.5px"', 'stroke-width="0.35px"')
    
    return svg_with_bg
