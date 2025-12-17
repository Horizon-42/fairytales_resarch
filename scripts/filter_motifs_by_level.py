#!/usr/bin/env python3
"""
Filter Motifs_complete.csv to only include entries up to level 4.
Creates a new CSV file without modifying the original.
"""

import csv
import re
from pathlib import Path
from typing import List, Dict


def calculate_level(motif_code: str) -> int:
    """Calculate hierarchy level based on number of dots in code."""
    parts = motif_code.split('.')
    parts = [p for p in parts if p]  # Remove empty parts
    return len(parts)


def filter_motifs_by_level(input_csv: Path, output_csv: Path, max_level: int = 4):
    """
    Filter motifs CSV to only include entries up to specified level.
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file
        max_level: Maximum level to include (default: 4)
    """
    filtered_rows = []
    total_rows = 0
    filtered_count = 0
    
    # Read input CSV
    with open(input_csv, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            print("Error: CSV file has no header row")
            return
        
        # Read header
        filtered_rows.append(fieldnames)
        
        # Filter rows
        for row in reader:
            total_rows += 1
            motif_code = row.get('motif_code', '').strip()
            
            if not motif_code:
                continue
            
            # Calculate level
            level = calculate_level(motif_code)
            
            # Include if level <= max_level
            if level <= max_level:
                filtered_rows.append([row.get(field, '') for field in fieldnames])
                filtered_count += 1
    
    # Write filtered CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(filtered_rows)
    
    print(f"Filtered motifs CSV:")
    print(f"  Input file: {input_csv}")
    print(f"  Output file: {output_csv}")
    print(f"  Total entries in input: {total_rows}")
    print(f"  Entries up to level {max_level}: {filtered_count}")
    print(f"  Filtered out (level > {max_level}): {total_rows - filtered_count}")
    
    # Print level statistics
    level_counts = {}
    for row in filtered_rows[1:]:  # Skip header
        if len(row) > 0:
            motif_code = row[0].strip()
            if motif_code:
                level = calculate_level(motif_code)
                level_counts[level] = level_counts.get(level, 0) + 1
    
    print("\nLevel distribution in filtered file:")
    for level in sorted(level_counts.keys()):
        print(f"  Level {level}: {level_counts[level]} entries")


def main():
    """Main function to filter motifs CSV by level."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Input and output files
    input_csv = project_root / "Motifs_complete.csv"
    output_csv = project_root / "Motifs_complete_level3.csv"
    
    if not input_csv.exists():
        print(f"Error: Input file not found: {input_csv}")
        return
    
    print(f"Filtering motifs CSV to level 3...")
    filter_motifs_by_level(input_csv, output_csv, max_level=3)
    print("\nDone!")


if __name__ == "__main__":
    main()
