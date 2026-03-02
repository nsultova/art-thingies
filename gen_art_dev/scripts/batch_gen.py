"""
Batch generation utilities for creating multiple variations efficiently.
"""

import itertools
from pathlib import Path
from typing import List, Dict, Any, Type, Optional
from .generators import BaseGenerator


class BatchGenerator:
    """
    Generate multiple variations of artwork efficiently.
    Supports parameter sweeps and multiple seeds.
    """
    
    def __init__(self, generator_class: Type[BaseGenerator],
                 base_params: Optional[Dict[str, Any]] = None):
        """
        Args:
            generator_class: The generator class to instantiate
            base_params: Base parameters to use for all (seed/params override these)
        """
        self.generator_class = generator_class
        self.base_params = base_params or {}
        self.generated_artworks = []
    
    def sweep(self, output_dir: str = './batch_output',
              seeds: Optional[List[int]] = None,
              **param_sweeps) -> List[str]:
        """
        Generate a grid of variations by sweeping parameters.
        
        Args:
            output_dir: Directory to save results
            seeds: List of seeds to use (if None, uses single seed 42)
            **param_sweeps: Each kwarg should be a list of values
                           Creates all combinations
        
        Returns:
            List of output file paths (standard versions)
        
        Example:
            batch = BatchGenerator(MyArt)
            batch.sweep(
                tracks=['seeds', 'scales'],
                seeds=[1, 2, 3],
                scales=[0.8, 1.0, 1.2]
            )
            # Generates 9 variations (3 seeds × 3 scales)
        """
        if seeds is None:
            seeds = [42]
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate all combinations
        param_names = list(param_sweeps.keys())
        param_lists = [param_sweeps[name] for name in param_names]
        
        combinations = list(itertools.product(seeds, *param_lists))
        
        output_files = []
        
        print(f"Generating {len(combinations)} variations...")
        
        for i, combo in enumerate(combinations, 1):
            seed = combo[0]
            params = dict(zip(param_names, combo[1:]))
            
            # Merge with base params
            merged = {**self.base_params, **params}
            
            # Create instance
            artwork = self.generator_class(seed=seed, **merged)
            artwork.render()
            
            # Build filename showing parameters
            param_str = '_'.join([f"{k}{v}" for k, v in params.items()])
            filename = f"{self.generator_class.__name__}_s{seed}_{param_str}"
            
            # Save
            artwork.save(filename, output_dir)
            output_files.append(str(output_dir / f"{filename}.svg"))
            
            print(f"  [{i}/{len(combinations)}] {filename}")
            self.generated_artworks.append(artwork)
        
        print(f"✓ Complete! {len(combinations)} variations saved to {output_dir}")
        return output_files
    
    def generate_series(self, name_prefix: str = 'art',
                       num_variations: int = 5,
                       output_dir: str = './batch_output',
                       **fixed_params) -> List[str]:
        """
        Simple: generate N variations with random seeds, fixed parameters.
        
        Args:
            name_prefix: Prefix for output filenames
            num_variations: How many to generate
            output_dir: Directory to save
            **fixed_params: Parameters to use for all (e.g., scale=1.5)
        
        Returns:
            List of output file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = []
        print(f"Generating {num_variations} variations...")
        
        for i in range(num_variations):
            artwork = self.generator_class(**fixed_params)
            artwork.render()
            
            filename = f"{name_prefix}_{i+1:02d}_s{artwork.seed}"
            artwork.save(filename, output_dir)
            output_files.append(str(output_dir / f"{filename}.svg"))
            
            print(f"  [{i+1}/{num_variations}] {filename}")
            self.generated_artworks.append(artwork)
        
        print(f"✓ Complete! {num_variations} variations saved to {output_dir}")
        return output_files
    
    def get_summary(self) -> str:
        """Get summary of generated artworks."""
        if not self.generated_artworks:
            return "No artworks generated yet."
        
        lines = [f"Generated {len(self.generated_artworks)} artworks:"]
        for art in self.generated_artworks:
            lines.append(f"  • {art}")
        
        return '\n'.join(lines)
