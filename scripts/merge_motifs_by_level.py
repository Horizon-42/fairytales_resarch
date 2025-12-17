#!/usr/bin/env python3
"""
Merge motif entries by level and convert codes to ranges.

For example, if merging to level 3:
- All level 4+ entries under A13.1 will be merged into A13.1
- Code will show as range like "A13.1" (or "A13.1-A13.1.x" format)
- Category name will be from the target level
"""

import csv
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict


def calculate_level(motif_code: str) -> int:
    """Calculate hierarchy level based on number of dots in code."""
    # Handle range format like "A13.1-A13.1.9"
    if '-' in motif_code:
        # Take the first part before '-'
        motif_code = motif_code.split('-')[0]
    
    parts = motif_code.split('.')
    parts = [p for p in parts if p]  # Remove empty parts
    return len(parts)


def get_code_prefix(code: str, target_level: int) -> str:
    """Get code prefix up to target level."""
    parts = code.split('.')
    parts = [p for p in parts if p]
    if len(parts) >= target_level:
        return '.'.join(parts[:target_level])
    return code


def get_code_range(codes: List[str], prefix: str) -> str:
    """Generate a code range string from a list of codes."""
    if not codes:
        return prefix
    
    if len(codes) == 1:
        # If only one code and it matches prefix, return prefix
        if codes[0] == prefix:
            return prefix
        return codes[0]
    
    # Sort codes
    sorted_codes = sorted(codes)
    first_code = sorted_codes[0]
    last_code = sorted_codes[-1]
    
    # Extract numeric parts for range
    # If all codes share the same prefix, show as range
    if first_code == prefix:
        # If prefix itself is in the list, use prefix only
        if all(code.startswith(prefix + '.') for code in sorted_codes[1:]):
            return prefix
        # Otherwise show range
        return f"{first_code}-{last_code}"
    
    # Return range format: A13.1.1-A13.1.9
    return f"{first_code}-{last_code}"


def merge_motifs_by_level(input_csv: Path, output_csv: Path, target_level: int):
    """
    Merge motifs CSV to specified level, grouping entries by their prefix.
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file
        target_level: Target level to merge to (1, 2, 3, or 4)
    """
    # Read all entries
    entries = []
    with open(input_csv, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            motif_code = row.get('motif_code', '').strip()
            if motif_code:
                level = calculate_level(motif_code)
                entries.append({
                    'code': motif_code,
                    'level': level,
                    'row': row
                })
    
    # Group entries by their prefix at target level
    groups = defaultdict(list)
    
    for entry in entries:
        code = entry['code']
        level = entry['level']
        
        # Get prefix at target level
        if level <= target_level:
            # This entry is at or above target level, use its own code as prefix
            prefix = code
        else:
            # This entry is below target level, get prefix up to target level
            prefix = get_code_prefix(code, target_level)
            # If prefix is empty or invalid, skip this entry
            if not prefix:
                continue
        
        groups[prefix].append(entry)
    
    # Generate merged entries
    merged_rows = []
    
    # Sort group keys for consistent output
    sorted_prefixes = sorted(groups.keys())
    
    for prefix in sorted_prefixes:
        group_entries = groups[prefix]
        
        # Find the entry at target level (if exists)
        target_entry = None
        for entry in group_entries:
            if entry['level'] == target_level:
                target_entry = entry
                break
        
        # If no exact match at target level, use the first entry that's at or below target level
        if not target_entry:
            for entry in group_entries:
                if entry['level'] <= target_level:
                    target_entry = entry
                    break
        
        # If still no match, use the entry with shortest code (closest to target)
        if not target_entry:
            target_entry = min(group_entries, key=lambda x: len(x['code']))
        
        # Get all codes in this group
        all_codes = [e['code'] for e in group_entries]
        
        # Generate code range - only if there are multiple entries
        if len(all_codes) == 1:
            merged_code = prefix
        else:
            merged_code = get_code_range(all_codes, prefix)
        
        # Verify merged_code is at or below target level
        merged_level = calculate_level(merged_code)
        if merged_level > target_level:
            # If merged code is still above target level, use prefix
            merged_code = prefix
            merged_level = calculate_level(prefix)
        
        # Use target entry's row as base
        base_row = target_entry['row'].copy()
        
        # Update code to range
        base_row['motif_code'] = merged_code
        
        # Update title to indicate it's a merged entry
        original_title = base_row.get('title', '')
        if len(all_codes) > 1:
            base_row['title'] = f"{original_title} (合并了 {len(all_codes)} 个子条目)"
        
        # Keep category information from target level
        # Level 1 category
        level_1_category = base_row.get('level_1_category', '')
        
        # Level 2 category - use from target entry
        level_2_category = base_row.get('level_2_category', '')
        
        # Level 3 category - use if target level >= 3
        level_3_category = base_row.get('level_3_category', '') if target_level >= 3 else ''
        
        # Level 4 category - use if target level >= 4
        level_4_category = base_row.get('level_4_category', '') if target_level >= 4 else ''
        
        # Level 5 category - not used when merging
        level_5_category = ''
        
        # First level code
        first_level_code = base_row.get('first_level_code', '')
        
        merged_rows.append({
            'motif_code': merged_code,
            'title': base_row.get('title', ''),
            'level_1_category': level_1_category,
            'level_2_category': level_2_category,
            'level_3_category': level_3_category,
            'level_4_category': level_4_category,
            'level_5_category': level_5_category,
            'first_level_code': first_level_code,
            'merged_count': len(all_codes)  # Keep track for statistics
        })
    
    # Write merged CSV
    fieldnames = [
        'motif_code',
        'title',
        'level_1_category',
        'level_2_category',
        'level_3_category',
        'level_4_category',
        'level_5_category',
        'first_level_code'
    ]
    
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in merged_rows:
            # Remove merged_count before writing
            row_to_write = {k: v for k, v in row.items() if k != 'merged_count'}
            writer.writerow(row_to_write)
    
    # Print statistics
    total_merged = sum(row['merged_count'] for row in merged_rows)
    print(f"Merged motifs CSV:")
    print(f"  Input file: {input_csv}")
    print(f"  Output file: {output_csv}")
    print(f"  Target level: {target_level}")
    print(f"  Total entries in input: {len(entries)}")
    print(f"  Merged entries in output: {len(merged_rows)}")
    print(f"  Entries merged: {total_merged - len(merged_rows)}")
    print(f"  Total sub-entries merged: {total_merged}")


def main():
    """Main function to merge motifs CSV by level."""
    import sys
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Default: merge to level 3
    target_level = 3
    if len(sys.argv) > 1:
        try:
            target_level = int(sys.argv[1])
            if target_level < 1 or target_level > 4:
                print("Error: Target level must be between 1 and 4")
                return
        except ValueError:
            print("Error: Target level must be an integer")
            return
    
    # Input and output files
    input_csv = project_root / "Motifs_complete.csv"
    output_csv = project_root / f"Motifs_merged_level{target_level}.csv"
    
    if not input_csv.exists():
        print(f"Error: Input file not found: {input_csv}")
        return
    
    print(f"Merging motifs CSV to level {target_level}...")
    merge_motifs_by_level(input_csv, output_csv, target_level)
    print("\nDone!")


if __name__ == "__main__":
    main()
