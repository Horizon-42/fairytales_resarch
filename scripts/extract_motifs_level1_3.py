#!/usr/bin/env python3
"""
Extract motif entries from Thompson_2016_Motif-Index.pdf following specific patterns:
- Level 1: A-Z letter categories (from table of contents)
- Level 2: A0-A9. Creator (range format like A0-A99. Creator)
- Level 3: A10. A10. Nature of the creator. (code repeated format)

Only extracts entries matching these three patterns.
"""

import re
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class MotifEntry:
    """Represents a single motif entry."""
    
    def __init__(self, code: str, description: str, level: int, line_num: int = 0):
        self.code = code
        self.description = description.strip()
        self.level = level
        self.line_num = line_num
        self.parent_code = ""  # Will be set during processing
    
    def is_range(self) -> bool:
        """Check if this entry is a range (e.g., A0-A99, A100—A499)."""
        return '-' in self.code or '—' in self.code
    
    def get_range_bounds(self) -> Optional[Tuple[str, int, int]]:
        """
        Get range bounds if this is a range entry.
        Returns: (letter, start_num, end_num) or None
        """
        match = re.match(r'^([A-Z])(\d+)[—\-]([A-Z])(\d+)$', self.code)
        if match:
            letter1 = match.group(1)
            num1 = int(match.group(2))
            letter2 = match.group(3)
            num2 = int(match.group(4))
            if letter1 == letter2:
                return (letter1, num1, num2)
        return None
    
    def contains_code(self, code: str) -> bool:
        """
        Check if this range entry contains a given code.
        For example, A0-A99 contains A10.
        """
        if not self.is_range():
            return False
        
        bounds = self.get_range_bounds()
        if not bounds:
            return False
        
        letter, start, end = bounds
        code_match = re.match(r'^([A-Z])(\d+)', code)
        if not code_match:
            return False
        
        code_letter = code_match.group(1)
        code_num = int(code_match.group(2))
        
        return code_letter == letter and start <= code_num <= end
    
    def __repr__(self):
        return f"MotifEntry(code={self.code}, level={self.level}, desc={self.description[:50]}...)"


def extract_text_with_format(pdf_path: Path) -> List[Tuple[str, bool]]:
    """
    Extract text from PDF with bold format information.
    Returns list of (text, is_bold) tuples.
    """
    lines_with_format = []
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"Total pages: {total_pages}")
    
    for page_num in range(total_pages):
        if page_num % 100 == 0:
            print(f"Processing page {page_num+1}/{total_pages}...")
        page = doc[page_num]
        
        # Extract text blocks with format
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:  # Text block
                for line in block["lines"]:
                    line_text = ""
                    line_is_bold = False
                    
                    for span in line["spans"]:
                        text = span["text"]
                        # Check if text is bold (font flags or font name)
                        font_flags = span.get("flags", 0)
                        is_bold = (font_flags & 16) != 0  # Bit 4 indicates bold
                        # Also check font name for bold indicators
                        font_name = span.get("font", "").lower()
                        if "bold" in font_name or "black" in font_name:
                            is_bold = True
                        
                        line_text += text
                        # If any part of the line is bold, mark the line as potentially bold
                        if is_bold:
                            line_is_bold = True
                    
                    if line_text.strip():
                        lines_with_format.append((line_text.strip(), line_is_bold))
    
    doc.close()
    return lines_with_format


def parse_level1_entry(line: str) -> Optional[MotifEntry]:
    """
    Parse Level 1 entry: Letter category like "A. Mythological" or "A  Mythological"
    Pattern: Single letter followed by period/space and category name
    """
    line = line.strip()
    
    # Pattern: A. Category or A  Category (single letter, optional punctuation, category name)
    # Look for single uppercase letter at start, followed by period/space(s), then description
    pattern = r'^([A-Z])[\.\s]+\s*([A-Z][^\.]+?)(?:\.|$|$)'
    match = re.match(pattern, line)
    
    if match:
        letter = match.group(1)
        description = match.group(2).strip()
        # Clean up description
        description = re.sub(r'\.+$', '', description).strip()
        if description:
            return MotifEntry(letter, description, 1, 0)
    
    return None


def save_extracted_hierarchy(level1_entries: List[MotifEntry], 
                             level2_entries: List[MotifEntry],
                             level3_entries: List[MotifEntry] = None,
                             output_path: Path = None):
    """
    Save extracted Level 1, Level 2, and Level 3 entries to a CSV file for future use.
    """
    if output_path is None:
        return
    
    if level3_entries is None:
        level3_entries = []
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['level', 'code', 'description', 'parent_code']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in level1_entries:
            writer.writerow({
                'level': entry.level,
                'code': entry.code,
                'description': entry.description,
                'parent_code': entry.parent_code
            })
        
        for entry in level2_entries:
            writer.writerow({
                'level': entry.level,
                'code': entry.code,
                'description': entry.description,
                'parent_code': entry.parent_code
            })
        
        for entry in level3_entries:
            writer.writerow({
                'level': entry.level,
                'code': entry.code,
                'description': entry.description,
                'parent_code': entry.parent_code
            })
    
    print(f"\nSaved extracted hierarchy to: {output_path}")
    print(f"  Level 1 entries: {len(level1_entries)}")
    print(f"  Level 2 entries: {len(level2_entries)}")
    if level3_entries:
        print(f"  Level 3 entries: {len(level3_entries)}")


def load_extracted_hierarchy(csv_path: Path) -> Tuple[List[MotifEntry], List[MotifEntry], List[MotifEntry]]:
    """
    Load Level 1, Level 2, and Level 3 entries from saved CSV file.
    Returns: (level1_entries, level2_entries, level3_entries)
    """
    level1_entries = []
    level2_entries = []
    level3_entries = []
    
    if not csv_path.exists():
        return level1_entries, level2_entries, level3_entries
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            level = int(row.get('level', 0))
            code = row.get('code', '').strip()
            description = row.get('description', '').strip()
            parent_code = row.get('parent_code', '').strip()
            
            if code and description:
                entry = MotifEntry(code, description, level, 0)
                entry.parent_code = parent_code
                if level == 1:
                    level1_entries.append(entry)
                elif level == 2:
                    level2_entries.append(entry)
                elif level == 3:
                    level3_entries.append(entry)
    
    return level1_entries, level2_entries, level3_entries


def parse_level2_entry(line: str) -> Optional[MotifEntry]:
    """
    Parse Level 2 entry: Range format like:
    - "A0-A99. Creator." 
    - "A100—A499. GODS" (with em dash)
    Pattern: [Letter][Number][-—][Letter][Number]. Description
    Supports both hyphen (-) and em dash (—)
    Returns Level 2 entry (top-level ranges)
    """
    line = line.strip()
    
    # Pattern: A0-A99. Creator. or A100—A499. The Gods
    # Supports both hyphen (-) and em dash (—)
    # Must have range format with dash/em dash, followed by period, then description
    pattern = r'^([A-Z])(\d+)[—\-]([A-Z])(\d+)\.\s+(.+)$'
    match = re.match(pattern, line)
    
    if match:
        letter1 = match.group(1)
        num1 = match.group(2)
        letter2 = match.group(3)
        num2 = match.group(4)
        description = match.group(5).strip()
        
        # Verify both letters are the same
        if letter1 == letter2:
            # Normalize to hyphen for consistency
            code = f"{letter1}{num1}-{letter1}{num2}"
            # Clean description (remove trailing period if it's just punctuation)
            if description.endswith('.') and len(description.split()) <= 3:
                description = description.rstrip('.')
            return MotifEntry(code, description, 2, 0)
    
    return None


def parse_level3_range_entry(line: str) -> Optional[MotifEntry]:
    """
    Parse Level 3 entry: Sub-range format like:
    - "A100—A199. The gods in general." (with em dash)
    These are sub-ranges within Level 2 ranges.
    Pattern: [Letter][Number][-—][Letter][Number]. Description
    """
    line = line.strip()
    
    # Same pattern as Level 2, but we'll distinguish them by checking if they're contained in Level 2 ranges
    pattern = r'^([A-Z])(\d+)[—\-]([A-Z])(\d+)\.\s+(.+)$'
    match = re.match(pattern, line)
    
    if match:
        letter1 = match.group(1)
        num1 = match.group(2)
        letter2 = match.group(3)
        num2 = match.group(4)
        description = match.group(5).strip()
        
        # Verify both letters are the same
        if letter1 == letter2:
            # Normalize to hyphen for consistency
            code = f"{letter1}{num1}-{letter1}{num2}"
            # Clean description
            if description.endswith('.') and len(description.split()) <= 3:
                description = description.rstrip('.')
            # Initially mark as Level 3, will be adjusted during processing
            return MotifEntry(code, description, 3, 0)
    
    return None


def parse_level4_entry(line: str, is_bold: bool = False) -> Optional[MotifEntry]:
    """
    Parse Level 4 entry: Code repeated format like "A10. A10. Nature of the creator."
    Pattern: [Letter][Numbers]. [Letter][Numbers]. Description
    IMPORTANT: 
    - Code must NOT contain dots (no sub-numbers like A10.1)
    - Only extract if description text is bold (or line is marked as bold)
    These are the specific motif entries (previously called Level 3)
    """
    line = line.strip()
    
    # Pattern: A10. A10. Description
    # Code must be: one letter followed by digits only (no dots)
    # Must be repeated exactly
    pattern = r'^([A-Z]\d+)\.\s+\1\.\s+(.+)$'
    match = re.match(pattern, line)
    
    if match:
        code = match.group(1)
        description = match.group(2).strip()
        
        # Verify code has no dots (just letter + numbers)
        if '.' not in code:
            # Only extract if line is marked as bold
            if is_bold:
                return MotifEntry(code, description, 4, 0)
            # Also check if description starts with capital letter (common for bold text)
            # But prefer bold flag
    
    return None


def determine_parent_range(entry: MotifEntry, 
                           level2_ranges: List[MotifEntry],
                           level3_ranges: List[MotifEntry]) -> str:
    """
    Determine which range a code belongs to.
    For ranges (Level 3), find parent Level 2 range.
    For codes (Level 4), find the most specific parent (Level 3 if available, else Level 2).
    """
    if entry.is_range():
        # For Level 3 ranges, find parent Level 2 range
        bounds = entry.get_range_bounds()
        if not bounds:
            return ""
        
        letter, start, end = bounds
        
        # Find the smallest Level 2 range that contains this range
        matching_level2 = []
        for level2_entry in level2_ranges:
            if level2_entry.contains_code(f"{letter}{start}") and level2_entry.contains_code(f"{letter}{end}"):
                bounds2 = level2_entry.get_range_bounds()
                if bounds2:
                    _, start2, end2 = bounds2
                    matching_level2.append((level2_entry.code, end2 - start2))
        
        if matching_level2:
            matching_level2.sort(key=lambda x: x[1])  # Most specific first
            return matching_level2[0][0]
    else:
        # For Level 4 codes, find most specific parent (Level 3 first, then Level 2)
        letter_match = re.match(r'^([A-Z])(\d+)', entry.code)
        if not letter_match:
            return ""
        
        letter = letter_match.group(1)
        number = int(letter_match.group(2))
        code_str = entry.code
        
        # First try Level 3 ranges (more specific)
        matching_level3 = []
        for level3_entry in level3_ranges:
            if level3_entry.contains_code(code_str):
                bounds = level3_entry.get_range_bounds()
                if bounds:
                    _, start, end = bounds
                    matching_level3.append((level3_entry.code, end - start))
        
        if matching_level3:
            matching_level3.sort(key=lambda x: x[1])  # Most specific first
            return matching_level3[0][0]
        
        # Then try Level 2 ranges
        matching_level2 = []
        for level2_entry in level2_ranges:
            if level2_entry.contains_code(code_str):
                bounds = level2_entry.get_range_bounds()
                if bounds:
                    _, start, end = bounds
                    matching_level2.append((level2_entry.code, end - start))
        
        if matching_level2:
            matching_level2.sort(key=lambda x: x[1])  # Most specific first
            return matching_level2[0][0]
    
    return ""


def parse_extracted_text_with_format(lines_with_format: List[Tuple[str, bool]], 
                                     project_root: Path,
                                     hierarchy_cache_path: Path) -> Tuple[List[MotifEntry], List[MotifEntry], List[MotifEntry], List[MotifEntry]]:
    """
    Parse extracted text with format information and extract entries matching the patterns.
    Returns: (level1_entries, level2_entries, level3_entries, level4_entries)
    - Level 1: Letter categories (A-Z)
    - Level 2: Top-level ranges (A0-A99, A100—A499)
    - Level 3: Sub-ranges (A100—A199)
    - Level 4: Specific entries (A100, A110)
    """
    # Try to load cached hierarchy first
    level1_entries, level2_entries, level3_entries_cached = load_extracted_hierarchy(hierarchy_cache_path)
    
    if level1_entries or level2_entries or level3_entries_cached:
        print(f"\nLoaded cached hierarchy from: {hierarchy_cache_path}")
        print(f"  Level 1 entries: {len(level1_entries)}")
        print(f"  Level 2 entries: {len(level2_entries)}")
        print(f"  Level 3 entries: {len(level3_entries_cached)}")
        level3_entries = level3_entries_cached
    else:
        # Extract Level 1 and ranges from PDF text
        print("\nExtracting Level 1 and range entries from PDF text...")
        level1_entries = []
        all_range_entries = []  # All range entries (will classify later)
        
        # Extract Level 1 and all ranges from PDF
        for line_num, (line, is_bold) in enumerate(lines_with_format, 1):
            line_stripped = line.strip()
            
            if not line_stripped or len(line_stripped) < 3:
                continue
            
            # Try to parse as level 1
            entry = parse_level1_entry(line_stripped)
            if entry:
                # Only add if we don't already have this letter
                if not any(e.code == entry.code for e in level1_entries):
                    entry.line_num = line_num
                    level1_entries.append(entry)
                continue
            
            # Try to parse as any range (both Level 2 and Level 3 use same pattern initially)
            entry = parse_level2_entry(line_stripped)  # This function works for both
            if entry:
                # Store all ranges, will classify later
                entry.line_num = line_num
                all_range_entries.append(entry)
        
        # Classify ranges: determine which are Level 2 (top-level) and which are Level 3 (sub-ranges)
        # Sort ranges by start number to process larger ranges first
        all_range_entries.sort(key=lambda e: (e.code[0], int(e.code.split('-')[0][1:]) if e.code[0].isalpha() else 0))
        
        level2_entries = []
        level3_entries_final = []
        
        # First pass: identify Level 2 ranges (not contained in any other range)
        for entry in all_range_entries:
            is_sub_range = False
            entry_bounds = entry.get_range_bounds()
            if not entry_bounds:
                continue
            
            letter, start, end = entry_bounds
            
            # Check if this range is contained within any existing Level 2 range
            for level2_entry in level2_entries:
                if level2_entry.contains_code(f"{letter}{start}") and level2_entry.contains_code(f"{letter}{end}"):
                    # This is a sub-range (Level 3)
                    is_sub_range = True
                    entry.level = 3
                    entry.parent_code = level2_entry.code
                    level3_entries_final.append(entry)
                    break
            
            if not is_sub_range:
                # This is a top-level range (Level 2)
                entry.level = 2
                entry.parent_code = letter  # Parent is the letter
                level2_entries.append(entry)
        
        # Second pass: re-check Level 3 ranges against all Level 2 ranges (including newly added ones)
        # and update parent relationships for Level 3 ranges that might be contained in Level 3 ranges
        final_level3 = []
        for entry in level3_entries_final:
            entry_bounds = entry.get_range_bounds()
            if not entry_bounds:
                continue
            
            letter, start, end = entry_bounds
            
            # Find the most specific Level 2 range that contains this
            best_parent = None
            best_parent_size = float('inf')
            
            for level2_entry in level2_entries:
                if level2_entry.contains_code(f"{letter}{start}") and level2_entry.contains_code(f"{letter}{end}"):
                    bounds = level2_entry.get_range_bounds()
                    if bounds:
                        _, s, e = bounds
                        size = e - s
                        if size < best_parent_size:
                            best_parent_size = size
                            best_parent = level2_entry
            
            if best_parent:
                entry.parent_code = best_parent.code
                final_level3.append(entry)
        
        level3_entries_final = final_level3
        
        # Set parent codes for Level 2 entries
        for entry in level2_entries:
            if not entry.parent_code:
                entry.parent_code = entry.code[0]  # Parent is the letter
        
        # Sort entries
        level1_entries.sort(key=lambda e: e.code)
        level2_entries.sort(key=lambda e: e.code)
        level3_entries_final.sort(key=lambda e: e.code)
        
        print(f"  Found {len(level1_entries)} Level 1 entries")
        print(f"  Found {len(level2_entries)} Level 2 entries")
        print(f"  Found {len(level3_entries_final)} Level 3 entries (sub-ranges)")
        
        # Save extracted hierarchy (Level 1, Level 2, and Level 3)
        save_extracted_hierarchy(level1_entries, level2_entries, level3_entries_final, hierarchy_cache_path)
        
        level3_entries = level3_entries_final
    
    # Extract Level 4 entries (specific codes) from PDF
    level4_entries = []
    print("\nParsing Level 4 entries from PDF text...")
    
    for line_num, (line, is_bold) in enumerate(lines_with_format, 1):
        line_stripped = line.strip()
        
        if not line_stripped or len(line_stripped) < 5:
            continue
        
        # Try to parse as level 4 (specific codes, only if bold)
        entry = parse_level4_entry(line_stripped, is_bold)
        if entry:
            entry.line_num = line_num
            level4_entries.append(entry)
    
    print(f"  Found {len(level4_entries)} Level 4 entries (bold text only)")
    
    # Update parent codes for level 4 entries (find most specific parent: Level 3 first, then Level 2)
    for entry in level4_entries:
        entry.parent_code = determine_parent_range(entry, level2_entries, level3_entries)
    
    return level1_entries, level2_entries, level3_entries, level4_entries


def generate_csv(level1_entries: List[MotifEntry], 
                 level2_entries: List[MotifEntry], 
                 level3_entries: List[MotifEntry],
                 level4_entries: List[MotifEntry],
                 output_path: Path):
    """
    Generate CSV file with only Level 4 entries (specific motif codes).
    Columns: motif_code, title, level_1_category, level_2_category, level_2_range, level_3_category, level_3_range
    """
    
    # Build entries lookup
    entries_by_code = {entry.code: entry for entry in level1_entries}
    level2_ranges = {e.code: e for e in level2_entries}
    level3_ranges = {e.code: e for e in level3_entries}
    
    rows = []
    
    # Process only Level 4 entries
    for entry in level4_entries:
        # Extract letter code
        letter_match = re.match(r'^([A-Z])', entry.code)
        letter_code = letter_match.group(1) if letter_match else ""
        
        # Get level 1 category
        level1_entry = entries_by_code.get(letter_code)
        level_1_category = level1_entry.description if level1_entry else ""
        
        # Find parent ranges
        level_2_category = ""
        level_2_range = ""
        level_3_category = ""
        level_3_range = ""
        
        # Check if parent is Level 3 range
        if entry.parent_code in level3_ranges:
            level3_entry = level3_ranges[entry.parent_code]
            level_3_category = level3_entry.description
            level_3_range = level3_entry.code
            # Find Level 2 parent of Level 3
            if level3_entry.parent_code in level2_ranges:
                level2_entry = level2_ranges[level3_entry.parent_code]
                level_2_category = level2_entry.description
                level_2_range = level2_entry.code
        # Check if parent is Level 2 range
        elif entry.parent_code in level2_ranges:
            level2_entry = level2_ranges[entry.parent_code]
            level_2_category = level2_entry.description
            level_2_range = level2_entry.code
        
        # Get title
        title = entry.description
        if len(title) > 200:
            title = title[:197] + "..."
        
        rows.append({
            'motif_code': entry.code,
            'title': title,
            'level_1_category': level_1_category,
            'level_2_category': level_2_category,
            'level_2_range': level_2_range,
            'level_3_category': level_3_category,
            'level_3_range': level_3_range
        })
    
    # Write CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            'motif_code',
            'title',
            'level_1_category',
            'level_2_category',
            'level_2_range',
            'level_3_category',
            'level_3_range'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nGenerated CSV file: {output_path}")
    print(f"  Total Level 4 entries: {len(rows)}")


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Input PDF file
    pdf_file = project_root / "papers" / "Thompson_2016_Motif-Index.pdf"
    
    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_file}")
        return
    
    if not PYMUPDF_AVAILABLE:
        print("Error: PyMuPDF (fitz) not available. Please install it in conda aviation environment.")
        return
    
    print(f"Extracting text from PDF: {pdf_file}")
    print("This may take several minutes for a large PDF...")
    
    # Extract text from PDF with format information
    try:
        lines_with_format = extract_text_with_format(pdf_file)
        print(f"Extracted {len(lines_with_format)} lines with format information")
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return
    
    # Set cache path for extracted hierarchy
    hierarchy_cache_path = project_root / "Motifs_extracted_hierarchy.csv"
    
    # Parse entries
    level1_entries, level2_entries, level3_entries, level4_entries = parse_extracted_text_with_format(
        lines_with_format, project_root, hierarchy_cache_path
    )
    
    if not (level1_entries or level2_entries or level3_entries or level4_entries):
        print("Error: No entries found matching the patterns")
        return
    
    # Generate output file
    output_csv = project_root / "Motifs_level1_3.csv"
    generate_csv(level1_entries, level2_entries, level3_entries, level4_entries, output_csv)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
