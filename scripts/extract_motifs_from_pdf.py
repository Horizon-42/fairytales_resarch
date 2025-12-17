#!/usr/bin/env python3
"""
Extract motif entries from Thompson_2016_Motif-Index.pdf and generate complete CSV and MD files.

This script:
1. Extracts all text from the PDF file
2. Parses motif entries with their hierarchical structure
3. Generates CSV and MD files with complete hierarchy information
"""

import re
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


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
        parts = self.code.split('.')
        parts = [p for p in parts if p]
        return len(parts)

    def _calculate_parent_code(self) -> str:
        """Calculate parent code by removing the last segment."""
        parts = self.code.split('.')
        parts = [p for p in parts if p]
        if len(parts) > 1:
            return '.'.join(parts[:-1])
        return ""

    def __repr__(self):
        return f"MotifEntry(code={self.code}, level={self.level}, desc={self.description[:50]}...)"


def extract_text_from_pdf_pdfplumber(pdf_path: Path) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            if i % 100 == 0:
                print(f"Processing page {i+1}/{len(pdf.pages)}...")
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_pdf_pypdf2(pdf_path: Path) -> str:
    """Extract text from PDF using PyPDF2 (fallback)."""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Total pages: {len(pdf_reader.pages)}")
        for i, page in enumerate(pdf_reader.pages):
            if i % 100 == 0:
                print(f"Processing page {i+1}/{len(pdf_reader.pages)}...")
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_pdf_pymupdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF (fitz)."""
    import fitz
    text = ""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"Total pages: {total_pages}")
    
    for page_num in range(total_pages):
        if page_num % 100 == 0:
            print(f"Processing page {page_num+1}/{total_pages}...")
        page = doc[page_num]
        page_text = page.get_text()
        if page_text:
            text += page_text + "\n"
    
    doc.close()
    return text


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using available library."""
    if PDFPLUMBER_AVAILABLE:
        print("Using pdfplumber for text extraction...")
        return extract_text_from_pdf_pdfplumber(pdf_path)
    elif PYMUPDF_AVAILABLE:
        print("Using PyMuPDF (fitz) for text extraction...")
        return extract_text_from_pdf_pymupdf(pdf_path)
    elif PYPDF2_AVAILABLE:
        print("Using PyPDF2 for text extraction...")
        return extract_text_from_pdf_pypdf2(pdf_path)
    elif PYPDF_AVAILABLE:
        print("Using pypdf for text extraction...")
        # pypdf is similar to PyPDF2, can reuse the same function
        return extract_text_from_pdf_pypdf2(pdf_path)
    else:
        raise ImportError("No PDF library available. Install pdfplumber (recommended), PyMuPDF, PyPDF2, or pypdf")


def parse_motif_line(line: str, line_num: int) -> Optional[MotifEntry]:
    """
    Parse a single line from the extracted text.
    
    Expected format examples:
    - A102. A102. Characteristics of deity.
    - A102.1. A102.1. Omniscient god. Icel.: MacCulloch Eddic 47 (Odin);
    - A102.2. A102.2. All-seeing god. Jewish: Neuman; Greek: Aeschylus...
    """
    line = line.strip()

    # Skip empty lines
    if not line or len(line) < 5:
        return None

    # Pattern to match motif code at the beginning
    # Examples: "A102.", "A102.1.", "A102.1.1.", etc.
    pattern = r'^([A-Z]\d+(?:\.\d+)*)\.?\s*(?:[A-Z]\d+(?:\.\d+)*\.\s*)?(.+)$'
    match = re.match(pattern, line)

    if not match:
        return None

    code = match.group(1)
    rest = match.group(2).strip()

    description = rest
    source = ""

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

        # Skip empty lines
        if not line_stripped:
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
                current_entry = current_entry.rstrip() + " " + line_stripped

    # Add the last entry if exists
    if current_entry:
        merged.append(current_entry)

    return merged


def parse_extracted_text(text: str) -> Tuple[List[MotifEntry], List[Dict]]:
    """Parse the extracted PDF text and extract all motif entries."""
    entries = []

    # Split into lines
    lines = text.split('\n')

    # Merge continuation lines
    merged_lines = merge_continuation_lines(lines)

    # Parse merged lines
    for line_num, line in enumerate(merged_lines, 1):
        entry = parse_motif_line(line, line_num)
        if entry:
            entries.append(entry)

    # Build entries lookup - don't create missing parent entries
    # Instead, we'll handle missing parents by using the closest available parent
    entries_by_code = {entry.code: entry for entry in entries}
    
    # Filter out entries whose parent doesn't exist at their expected level
    # and adjust their parent_code to the closest existing parent
    filtered_entries = []
    orphaned_entries = []
    
    for entry in entries:
        original_parent_code = entry.parent_code
        current_parent_code = entry.parent_code
        
        # Find the closest existing parent by going up the hierarchy
        while current_parent_code and current_parent_code not in entries_by_code:
            # Extract parent of parent
            parent_parts = current_parent_code.split('.')
            if len(parent_parts) > 1:
                parent_parts.pop()
                current_parent_code = '.'.join(parent_parts)
            else:
                # No parent exists, this entry is orphaned
                current_parent_code = None
                break
        
        if current_parent_code or entry.level == 1:
            # Update parent_code to the closest existing parent
            entry.parent_code = current_parent_code if current_parent_code else ""
            filtered_entries.append(entry)
        else:
            # This is an orphaned entry - save it with original parent info
            orphaned_entries.append({
                'entry': entry,
                'original_parent_code': original_parent_code
            })
    
    return filtered_entries, orphaned_entries

    return entries


def load_category_names(csv_path: Path) -> Dict[str, str]:
    """Load category names from Motifs.csv mapping letter codes to category names."""
    category_map = {}
    if not csv_path.exists():
        return category_map

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get('Category Code', '').strip()
            category = row.get('General Category', '').strip()
            if code and category:
                category_map[code] = category

    return category_map


def build_hierarchy_path(entry: MotifEntry, entries_by_code: Dict[str, MotifEntry]) -> List[MotifEntry]:
    """
    Build the full hierarchy path for an entry.
    Returns a list of MotifEntry objects from root to this entry.
    """
    path = []
    current_entry = entry

    # Build path from root to current entry by traversing up
    codes_in_path = []
    while current_entry:
        codes_in_path.insert(0, current_entry.code)
        if current_entry.parent_code and current_entry.parent_code in entries_by_code:
            current_entry = entries_by_code[current_entry.parent_code]
        else:
            break

    # Build path list
    for code in codes_in_path:
        e = entries_by_code.get(code)
        if e:
            path.append(e)

    return path


def generate_csv(entries: List[MotifEntry], output_path: Path, project_root: Path):
    """Generate CSV file with motif entries in ATU_types_complete.csv format."""

    # Load category names from Motifs.csv
    motifs_csv = project_root / "Motifs.csv"
    category_names = load_category_names(motifs_csv)

    # Build entries lookup
    entries_by_code = {entry.code: entry for entry in entries}

    # Build CSV rows
    rows = []

    for entry in entries:
        # Build hierarchy path from root to current entry (excluding current entry itself)
        parent_path = []
        current = entry
        while current and current.parent_code:
            parent = entries_by_code.get(current.parent_code)
            if parent:
                parent_path.insert(0, parent)
                current = parent
            else:
                break

        # Extract letter code (e.g., "A" from "A102")
        letter_match = re.match(r'^([A-Z])', entry.code)
        letter_code = letter_match.group(1) if letter_match else ""
        level_1_category = category_names.get(letter_code, "")

        # Initialize all level categories
        level_2_category = ""
        level_3_category = ""
        level_4_category = ""
        level_5_category = ""

        # Assign descriptions from parent path
        for parent_entry in parent_path:
            if parent_entry.level == 1:
                level_2_category = parent_entry.description
            elif parent_entry.level == 2:
                level_3_category = parent_entry.description
            elif parent_entry.level == 3:
                level_4_category = parent_entry.description
            elif parent_entry.level == 4:
                level_5_category = parent_entry.description

        # For level 1 entries, they are their own level_2_category
        if entry.level == 1:
            level_2_category = entry.description

        # Get description for title (current entry's description)
        title = entry.description
        # Truncate if too long
        if len(title) > 200:
            title = title[:197] + "..."

        # Get first level motif_code (root entry code)
        first_level_code = ""
        if parent_path:
            first_level_code = parent_path[0].code
        elif entry.level == 1:
            first_level_code = entry.code

        rows.append({
            'motif_code': entry.code,
            'title': title,
            'level_1_category': level_1_category,
            'level_2_category': level_2_category,
            'level_3_category': level_3_category,
            'level_4_category': level_4_category,
            'level_5_category': level_5_category,
            'first_level_code': first_level_code
        })

    # Write CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
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
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated CSV file: {output_path}")
    print(f"  Total entries: {len(entries)}")


def generate_markdown(entries: List[MotifEntry], output_path: Path):
    """Generate markdown file with hierarchical structure preserved."""

    # Build hierarchy tree
    entries_by_code = {entry.code: entry for entry in entries}
    root_entries = [e for e in entries if e.level == 1]

    # Sort entries by code for consistent ordering
    def sort_key(entry):
        parts = []
        code_parts = entry.code.split('.')
        for i, part in enumerate(code_parts):
            if not part:
                continue
            if i == 0:
                match = re.match(r'([A-Z])(\d+)', part)
                if match:
                    letter = match.group(1)
                    number = int(match.group(2))
                    parts.append((ord(letter), number))
            else:
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
        prefix = "#" * min(indent + 1, 6)

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
        f.write("# Thompson Motif Index (Complete)\n\n")
        f.write(f"*Generated from Thompson_2016_Motif-Index.pdf*\n\n")
        f.write(f"Total entries: {len(entries)}\n\n")
        f.write("---\n\n")

        # Write all root entries and their descendants
        for root_entry in root_entries:
            write_entry_recursive(f, root_entry, 0)

    print(f"Generated Markdown file: {output_path}")
    print(f"  Total entries: {len(entries)}")
    print(f"  Root entries: {len(root_entries)}")


def generate_orphaned_csv(orphaned_entries: List[Dict], output_path: Path, project_root: Path):
    """Generate CSV file with orphaned entries (entries without valid parents)."""
    
    # Load category names from Motifs.csv
    motifs_csv = project_root / "Motifs.csv"
    category_names = load_category_names(motifs_csv)
    
    rows = []
    
    for item in orphaned_entries:
        entry = item['entry']
        original_parent_code = item['original_parent_code']
        
        # Extract letter code
        letter_match = re.match(r'^([A-Z])', entry.code)
        letter_code = letter_match.group(1) if letter_match else ""
        level_1_category = category_names.get(letter_code, "")
        
        # Get description for title
        title = entry.description
        if len(title) > 200:
            title = title[:197] + "..."
        
        rows.append({
            'motif_code': entry.code,
            'title': title,
            'level': entry.level,
            'expected_parent_code': original_parent_code,
            'level_1_category': level_1_category,
            'description': entry.description,
            'line_number': entry.line_num
        })
    
    # Write CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            'motif_code',
            'title',
            'level',
            'expected_parent_code',
            'level_1_category',
            'description',
            'line_number'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Generated orphaned entries CSV file: {output_path}")
    print(f"  Total orphaned entries: {len(orphaned_entries)}")


def save_extracted_text(text: str, output_path: Path):
    """Save extracted text to a file for debugging."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Saved extracted text to: {output_path}")


def main():
    """Main function to extract motifs from PDF and generate output files."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Input PDF file
    pdf_file = project_root / "papers" / "Thompson_2016_Motif-Index.pdf"

    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_file}")
        return

    print(f"Extracting text from PDF: {pdf_file}")
    print("This may take several minutes for a large PDF...")

    # Extract text from PDF
    try:
        extracted_text = extract_text_from_pdf(pdf_file)
        print(f"Extracted {len(extracted_text)} characters of text")
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        print("\nPlease install pdfplumber for better extraction:")
        print("  pip install pdfplumber")
        return

    # Save extracted text for debugging (optional)
    text_output = project_root / "motif_index_extracted.txt"
    save_extracted_text(extracted_text, text_output)

    # Parse entries
    print("\nParsing motif entries...")
    entries, orphaned_entries = parse_extracted_text(extracted_text)

    if not entries:
        print("Error: No entries found in the extracted text")
        return

    print(f"Parsed {len(entries)} valid motif entries")
    print(f"Found {len(orphaned_entries)} orphaned entries (entries without valid parents)")

    # Generate output files
    csv_output = project_root / "Motifs_complete.csv"
    md_output = project_root / "Motifs_complete.md"
    orphaned_csv_output = project_root / "Motifs_orphaned.csv"

    generate_csv(entries, csv_output, project_root)
    generate_markdown(entries, md_output)
    
    # Generate orphaned entries CSV
    if orphaned_entries:
        generate_orphaned_csv(orphaned_entries, orphaned_csv_output, project_root)

    # Print statistics
    level_counts = {}
    for entry in entries:
        level_counts[entry.level] = level_counts.get(entry.level, 0) + 1

    print("\nHierarchy statistics:")
    for level in sorted(level_counts.keys()):
        print(f"  Level {level}: {level_counts[level]} entries")

    print("\nDone!")


if __name__ == "__main__":
    main()
