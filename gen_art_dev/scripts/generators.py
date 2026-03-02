"""
Base generator class for algorithmic art.
Provides parametric control, SVG rendering, display, and export.
"""

import random
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .svg_utils import SvgBuilder, create_print_optimized, optimize_for_plotter


class BaseGenerator(ABC):
    """
    Foundation class for generative artwork.
    
    Override generate() to implement your algorithm.
    The class handles SVG output, parametric control, display, and exporting.
    """
    
    def __init__(self, width: float = 100, height: float = 100,
                 seed: Optional[int] = None, **params):
        """
        Args:
            width, height: Canvas size in mm
            seed: Random seed (None for random)
            **params: Additional algorithm-specific parameters
        """
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(0, 2**31 - 1)
        self.params = params
        
        # Set random seed
        random.seed(self.seed)
        
        # SVG builder - instantiated fresh for each render
        self.builder = None
        
        # Store generated SVG
        self.svg_standard = None
        self.svg_print_optimized = None
    
    @abstractmethod
    def generate(self) -> None:
        """
        Implement your algorithm here.
        Use self.builder to add elements.
        
        Example:
            def generate(self):
                for i in range(10):
                    x = i * 10
                    self.builder.add_circle(x, 50, 5)
        """
        pass
    
    def describe(self) -> str:
        """Brief description of what this generates. Override to customize."""
        return self.__class__.__name__
    
    def render(self) -> str:
        """
        Execute the algorithm and return standard SVG.
        
        Returns:
            SVG string
        """
        # Reset random seed for reproducibility
        random.seed(self.seed)
        
        # Create builder
        self.builder = SvgBuilder(self.width, self.height)
        
        # Run algorithm
        self.generate()
        
        # Store both versions
        self.svg_standard = self.builder.asstring()
        self.svg_print_optimized = create_print_optimized(
            self.svg_standard,
            algorithm_name=self.describe(),
            seed=self.seed,
            metadata=self.params
        )
        
        return self.svg_standard
    
    def display(self) -> None:
        """
        Display the artwork in notebook (if available).
        Falls back to text message if not in notebook.
        """
        if not self.svg_standard:
            self.render()
        
        try:
            # Try IPython display (notebooks)
            from IPython.display import SVG, display
            print(f"\n{self.describe()} (seed={self.seed})")
            print("Standard version:")
            display(SVG(self.svg_standard))
            print("\nPrint-optimized version:")
            display(SVG(self.svg_print_optimized))
        except ImportError:
            # Fallback: just print file size info
            if self.svg_standard:
                print(f"✓ Rendered: {self.describe()}")
                print(f"  Seed: {self.seed}")
                print(f"  Size: {self.width}×{self.height}mm")
                print(f"  SVG size: {len(self.svg_standard)} bytes")
                print("\n  Files saved with .save()")
    
    def save(self, base_filename: str = None, output_dir: str = '.') -> Dict[str, str]:
        """
        Save both standard and print-optimized versions.
        
        Args:
            base_filename: Base name (e.g., 'my_art'). If None, uses class name.
            output_dir: Directory to save in
        
        Returns:
            Dict with keys 'standard' and 'print_optimized' → file paths
        """
        if not self.svg_standard:
            self.render()
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if base_filename is None:
            base_filename = f"{self.__class__.__name__}_{self.seed}"
        
        # Remove .svg extension if present
        base_filename = base_filename.replace('.svg', '')
        
        # Save standard version
        path_standard = output_dir / f"{base_filename}.svg"
        with open(path_standard, 'w') as f:
            f.write(self.svg_standard)
        
        # Save print-optimized version
        path_print = output_dir / f"{base_filename}-print.svg"
        with open(path_print, 'w') as f:
            f.write(self.svg_print_optimized)
        
        print(f"✓ Saved:")
        print(f"  Standard:         {path_standard}")
        print(f"  Print-optimized:  {path_print}")
        
        return {
            'standard': str(path_standard),
            'print_optimized': str(path_print)
        }
    
    def copy_with_params(self, seed: Optional[int] = None, **new_params) -> 'BaseGenerator':
        """
        Create a copy with different seed and/or parameters.
        Useful for generating variations.
        
        Args:
            seed: New seed (if None, randomize)
            **new_params: Override any parameters
        
        Returns:
            New instance with updated parameters
        """
        new_seed = seed if seed is not None else random.randint(0, 2**31 - 1)
        merged_params = {**self.params, **new_params}
        return self.__class__(
            width=self.width,
            height=self.height,
            seed=new_seed,
            **merged_params
        )
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(seed={self.seed}, params={self.params})"
