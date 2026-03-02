"""
Preview and display utilities for viewing generated artwork.
"""

from typing import Optional
import io


class SvgPreview:
    """Display SVG artwork in various contexts."""
    
    @staticmethod
    def display_in_notebook(svg_standard: str, svg_print: str,
                           title: str = "Artwork") -> None:
        """
        Display both versions in a Jupyter notebook side-by-side.
        
        Args:
            svg_standard: Standard SVG string
            svg_print: Print-optimized SVG string
            title: Title to show
        """
        try:
            from IPython.display import SVG, display, HTML
            
            # Create side-by-side view
            html = f"""
            <div style="display: flex; gap: 20px;">
                <div>
                    <h3>Standard</h3>
                    {svg_standard}
                </div>
                <div>
                    <h3>Print-Optimized</h3>
                    {svg_print}
                </div>
            </div>
            """
            
            print(f"\n{title}")
            display(HTML(html))
        except ImportError:
            print("IPython not available. Use .save() to export files.")
    
    @staticmethod
    def save_comparison_html(svg_standard: str, svg_print: str,
                            filepath: str,
                            title: str = "Artwork Comparison",
                            algorithm_info: str = "") -> None:
        """
        Save a standalone HTML file comparing both versions.
        Can be opened in any browser.
        
        Args:
            svg_standard: Standard SVG string
            svg_print: Print-optimized SVG string
            filepath: Where to save
            title: Title for the page
            algorithm_info: Additional info to display
        """
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
        }}
        .container {{
            display: flex;
            gap: 40px;
            margin-top: 20px;
        }}
        .column {{
            flex: 1;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .column h2 {{
            margin-top: 0;
            color: #0066cc;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }}
        svg {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .info {{
            background: #e8f4f8;
            padding: 12px;
            border-left: 4px solid #0066cc;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 14px;
        }}
        @media (max-width: 1200px) {{
            .container {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    {{algorithm_info}}
    
    <div class="container">
        <div class="column">
            <h2>Standard Version</h2>
            <p><small>For display and digital use. Transparent background.</small></p>
            {svg_standard}
        </div>
        <div class="column">
            <h2>Print-Optimized (AxiDraw)</h2>
            <p><small>Optimized for pen plotters. White background, reduced stroke width.</small></p>
            {svg_print}
        </div>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w') as f:
            f.write(html)
        
        print(f"✓ Comparison saved: {filepath}")
    
    @staticmethod
    def get_file_info(filepath: str) -> dict:
        """
        Get information about an SVG file.
        
        Args:
            filepath: Path to SVG file
        
        Returns:
            Dict with size, line count, etc.
        """
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Count paths/lines (rough estimate of complexity)
        path_count = content.count('<path')
        line_count = content.count('<line')
        circle_count = content.count('<circle')
        polygon_count = content.count('<polygon')
        
        return {
            'file_size_bytes': len(content),
            'lines_of_svg': content.count('\n'),
            'paths': path_count,
            'lines': line_count,
            'circles': circle_count,
            'polygons': polygon_count,
            'total_elements': path_count + line_count + circle_count + polygon_count
        }
    
    @staticmethod
    def print_file_info(filepath: str, title: str = "") -> None:
        """Pretty-print file info."""
        info = SvgPreview.get_file_info(filepath)
        print(f"\n📊 {title or filepath}")
        print(f"  File size: {info['file_size_bytes']:,} bytes")
        print(f"  Elements: {info['total_elements']}")
        print(f"    • Paths: {info['paths']}")
        print(f"    • Lines: {info['lines']}")
        print(f"    • Circles: {info['circles']}")
        print(f"    • Polygons: {info['polygons']}")
