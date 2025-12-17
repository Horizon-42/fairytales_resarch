#!/usr/bin/env python3
"""
Parse motif_index_2016.md and generate CSV and MD files with hierarchical structure.

The script extracts motif entries from the markdown file, identifies their hierarchical
structure based on dot notation (A102, A102.1, A102.1.1, etc.), and generates:
1. A CSV file with all motifs and their hierarchy information
2. A formatted MD file preserving the hierarchical structure
"""

import re
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class MotifEntry:
    """Represents a single motif entry with its code, description, and hierarchy."""
    
    def __init__(self, code: str, description: str, source: str = "", line_num: int = 0):
        self.code = code
        self.description = description.strip()
        self.source = source.strip()
        self.line_num = line_num
        self.level = self._calculate_level()
        self.parent_code = self._calculate_parent_code()
        
    def _calculate_level(self) -> int:
        """Calculate hierarchy level based on number of dots in code."""
        # Count dots, but handle special cases like "A12." (which is level 1)
        # Actually, the pattern is: A102 (level 1), A102.1 (level 2), A102.1.1 (level 3), etc.
        parts = self.code.split('.')
        # Remove empty parts from trailing dots
        parts = [p for p in parts if p]
        return len(parts)
    
    def _calculate_parent_code(self) -> str:
        """Calculate parent code by removing the last segment."""
        parts = self.code.split('.')
        parts = [p for p in parts if p]  # Remove empty parts
        if len(parts) > 1:
            return '.'.join(parts[:-1])
        return ""
    
    def __repr__(self):
        return f"MotifEntry(code={self.code}, level={self.level}, desc={self.description[:50]}...)"


def parse_motif_line(line: str, line_num: int) -> Optional[MotifEntry]:
    """
    Parse a single line from the motif index file.
    
    Expected format examples:
    - A102. A102. Characteristics of deity.
    - A102.1. A102.1. Omniscient god. Icel.: MacCulloch Eddic 47 (Odin);
    - A102.2. A102.2. All-seeing god. Jewish: Neuman; Greek: Aeschylus...
    """
    line = line.strip()
    
    # Skip empty lines, page numbers, and metadata
    if not line or line.isdigit() or "Page Width" in line or len(line) < 5:
        return None
    
    # Pattern to match motif code at the beginning
    # Examples: "A102.", "A102.1.", "A102.1.1.", etc.
    # Some entries have the code repeated (e.g., "A102. A102. Description")
    pattern = r'^([A-Z]\d+(?:\.\d+)*)\.?\s*(?:[A-Z]\d+(?:\.\d+)*\.\s*)?(.+)$'
    match = re.match(pattern, line)
    
    if not match:
        return None
    
    code = match.group(1)
    rest = match.group(2).strip()
    
    # Extract description and source
    # Description is usually before citations or sources
    # Sources often start with cultural indicators or end with citations
    description = rest
    source = ""
    
    # Try to separate description from source citations
    # Sources often appear after a period or colon with cultural/geographic indicators
    # But we'll keep the full text in description for now, source as separate field
    # The pattern seems to be: "Description. Source1: Reference; Source2: Reference"
    
    return MotifEntry(code, description, source, line_num)


def merge_continuation_lines(lines: List[str]) -> List[str]:
    """
    Merge continuation lines that don't start with a motif code.
    Some entries span multiple lines where continuation lines don't start with codes.
    """
    merged = []
    current_entry = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Skip empty lines, page numbers, and metadata
        if not line_stripped or line_stripped.isdigit() or "Page Width" in line_stripped:
            if current_entry:
                merged.append(current_entry)
                current_entry = None
            continue
        
        # Check if this line starts with a motif code
        pattern = r'^([A-Z]\d+(?:\.\d+)*)\.?\s*(?:[A-Z]\d+(?:\.\d+)*\.\s*)?'
        match = re.match(pattern, line_stripped)
        
        if match:
            # This is a new entry
            if current_entry:
                merged.append(current_entry)
            current_entry = line
        else:
            # This is a continuation of the previous entry
            if current_entry:
                # Append to current entry with a space
                current_entry = current_entry.rstrip() + " " + line_stripped
            # If no current_entry, skip this line (shouldn't happen, but be safe)
    
    # Add the last entry if exists
    if current_entry:
        merged.append(current_entry)
    
    return merged


def parse_motif_file(file_path: Path) -> List[MotifEntry]:
    """Parse the motif index markdown file and extract all entries."""
    entries = []
    
    # First, read all lines and merge continuations
    with open(file_path, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    
    # Merge continuation lines
    merged_lines = merge_continuation_lines(all_lines)
    
    # Parse merged lines
    for line_num, line in enumerate(merged_lines, 1):
        entry = parse_motif_line(line, line_num)
        if entry:
            entries.append(entry)
    
    # Create missing parent entries (e.g., if we have A106.0.1 but no A106.0)
    entries_by_code = {entry.code: entry for entry in entries}
    missing_parents = []
    
    for entry in entries:
        if entry.parent_code and entry.parent_code not in entries_by_code:
            # Check if parent is a valid pattern (not just empty)
            if re.match(r'^[A-Z]\d+(?:\.\d+)*$', entry.parent_code):
                # Create a placeholder parent entry
                parent_entry = MotifEntry(
                    entry.parent_code,
                    f"[Missing parent entry for {entry.code}]",
                    "",
                    entry.line_num
                )
                missing_parents.append(parent_entry)
                entries_by_code[entry.parent_code] = parent_entry
    
    # Add missing parents to entries
    entries.extend(missing_parents)
    
    return entries


def generate_csv(entries: List[MotifEntry], output_path: Path):
    """Generate CSV file with motif entries and hierarchy information."""
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            'Code',
            'Level',
            'Parent Code',
            'Description',
            'Source',
            'Line Number'
        ])
        
        # Write entries
        for entry in entries:
            writer.writerow([
                entry.code,
                entry.level,
                entry.parent_code,
                entry.description,
                entry.source,
                entry.line_num
            ])
    
    print(f"Generated CSV file: {output_path}")
    print(f"  Total entries: {len(entries)}")


def generate_markdown(entries: List[MotifEntry], output_path: Path):
    """Generate markdown file with hierarchical structure preserved."""
    
    # Build hierarchy tree
    entries_by_code = {entry.code: entry for entry in entries}
    root_entries = [e for e in entries if e.level == 1]
    
    # Sort entries by code for consistent ordering
    def sort_key(entry):
        # Convert "A102.1.2" to tuples for proper sorting
        # Handles both "A102" and "A102.1.2" formats
        parts = []
        code_parts = entry.code.split('.')
        for i, part in enumerate(code_parts):
            if not part:
                continue
            # Extract letter and number from first part (e.g., "A102")
            if i == 0:
                match = re.match(r'([A-Z])(\d+)', part)
                if match:
                    letter = match.group(1)
                    number = int(match.group(2))
                    parts.append((ord(letter), number))
            else:
                # Subsequent parts are just numbers (e.g., "1", "2")
                try:
                    number = int(part)
                    parts.append(number)
                except ValueError:
                    parts.append(part)
        return tuple(parts)
    
    root_entries.sort(key=sort_key)
    
    def get_children(parent_code: str) -> List[MotifEntry]:
        """Get all direct children of a parent code."""
        children = [e for e in entries if e.parent_code == parent_code]
        children.sort(key=sort_key)
        return children
    
    def write_entry_recursive(f, entry: MotifEntry, indent: int = 0):
        """Recursively write entry and its children with proper indentation."""
        indent_str = "  " * indent
        prefix = "#" * min(indent + 1, 6)  # Use markdown headers, max h6
        
        # Write the entry
        f.write(f"{indent_str}{prefix} {entry.code}. {entry.description}\n")
        
        # Write source if present
        if entry.source:
            f.write(f"{indent_str}*Source: {entry.source}*\n")
        
        f.write("\n")
        
        # Write children recursively
        children = get_children(entry.code)
        for child in children:
            write_entry_recursive(f, child, indent + 1)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Thompson Motif Index\n\n")
        f.write(f"*Generated from motif_index_2016.md*\n\n")
        f.write(f"Total entries: {len(entries)}\n\n")
        f.write("---\n\n")
        
        # Write all root entries and their descendants
        for root_entry in root_entries:
            write_entry_recursive(f, root_entry, 0)
    
    print(f"Generated Markdown file: {output_path}")
    print(f"  Total entries: {len(entries)}")
    print(f"  Root entries: {len(root_entries)}")


def main():
    """Main function to parse motif index and generate output files."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Input file
    input_file = project_root / "motif_index_2016.md"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return
    
    print(f"Parsing motif index file: {input_file}")
    
    # Parse entries
    entries = parse_motif_file(input_file)
    
    if not entries:
        print("Error: No entries found in the file")
        return
    
    print(f"Parsed {len(entries)} motif entries")
    
    # Generate output files
    csv_output = project_root / "Motifs_complete.csv"
    md_output = project_root / "Motifs_complete.md"
    
    generate_csv(entries, csv_output)
    generate_markdown(entries, md_output)
    
    # Print statistics
    level_counts = {}
    for entry in entries:
        level_counts[entry.level] = level_counts.get(entry.level, 0) + 1
    
    print("\nHierarchy statistics:")
    for level in sorted(level_counts.keys()):
        print(f"  Level {level}: {level_counts[level]} entries")


if __name__ == "__main__":
    main()
