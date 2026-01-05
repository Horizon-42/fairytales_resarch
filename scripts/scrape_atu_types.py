#!/usr/bin/env python3
"""Scrape ATU types from http://www.mftd.org/index.php?action=atu

This script fetches the ATU classification structure from mftd.org and generates
both CSV and Markdown documentation files.

Note: mftd.org does not appear to list every ATU number; its range pages contain
only the subset of types present in its database (currently ~890 unique types).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import html as html_lib
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional, Set, Tuple

try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover
    tqdm = None


BASE_URL = "http://www.mftd.org/index.php?action=atu"
USER_AGENT = "fairytales_resarch/1.0 (educational research; ATU classification scraper)"


@dataclass
class ATUCategory:
    """Represents a category/range in the ATU classification."""
    start_index: int
    end_index: int
    category_name: str
    level: int


@dataclass
class ATUType:
    """Represents a single ATU type."""
    atu_number: int
    title: str
    category_range: Optional[str] = None  # e.g., "1-299" for the range it belongs to
    level_1_category: Optional[str] = None
    level_2_category: Optional[str] = None
    level_3_category: Optional[str] = None
    detail_url: Optional[str] = None
    description: Optional[str] = None


def _fetch_html(url: str, timeout_s: int = 30) -> str:
    """Fetch HTML content from URL."""
    full_url = url if url.startswith('http') else f"http://www.mftd.org/{url}"
    req = urllib.request.Request(full_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} for {full_url}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error for {full_url}: {e}") from e


def _extract_categories_from_main_page(html: str) -> list[ATUCategory]:
    """Extract category structure from the main ATU page."""
    categories = []
    
    # Find the main content area
    main_ul_start = html.find('ANIMAL TALES')
    if main_ul_start < 0:
        return categories
    
    ul_start_pos = html.rfind('<ul>', 0, main_ul_start)
    if ul_start_pos < 0:
        return categories
    
    content_section = html[ul_start_pos:]
    
    # Find all patterns: <a...>Category</a> ... range
    pattern = r'<a[^>]*>([^<]+)</a>\s*(?:&nbsp;)?\s*(\d+)\s*-\s*(\d+)'
    
    for match in re.finditer(pattern, content_section):
        category = match.group(1).strip()
        start_str = match.group(2)
        end_str = match.group(3)
        
        try:
            start = int(start_str)
            end = int(end_str)
            
            # Calculate level by counting <ul> tags before this match
            text_before = content_section[:match.start()]
            ul_count = text_before.count('<ul>')
            ul_end_count = text_before.count('</ul>')
            depth = ul_count - ul_end_count
            level = max(1, depth)
            
            categories.append(ATUCategory(start, end, category, level))
        except ValueError:
            pass
    
    return categories


def _extract_range_links_from_main_page(html: str) -> list[Tuple[int, int, str]]:
    """Extract all range links (start, end, url) from the main page."""
    ranges = []
    
    # Find range links: index.php?action=atu&act=range&id=X-Y
    pattern = r'href=[\'"](index\.php\?action=atu[^\'"]*act=range[^\'"]*id=(\d+)-(\d+)[^\'"]*)[\'"]'
    
    for match in re.finditer(pattern, html):
        url = match.group(1).replace('&amp;', '&')
        start = int(match.group(2))
        end = int(match.group(3))
        ranges.append((start, end, url))
    
    return ranges


def _extract_atu_types_from_range_page(html: str, range_start: int, range_end: int) -> list[ATUType]:
    """Extract all ATU types from a range page."""
    atu_types = []
    
    # Find the table
    table_start = html.find('<table>')
    if table_start < 0:
        return atu_types
    
    # Extract all <tr> tags with id attributes
    # Format: <tr id="1"><td title='Folktale Type'>1. <td><a href='...'>Title</a>
    tr_pattern = r'<tr\s+id="(\d+[A-Z]?)"[^>]*>'
    
    pos = table_start
    while True:
        match = re.search(tr_pattern, html[pos:])
        if not match:
            break
        
        tr_start = pos + match.start()
        tr_id_str = match.group(1)
        
        # Find the next <tr> tag to get the content of this row
        next_tr = html.find('<tr', tr_start + 3)
        if next_tr < 0:
            # Last row, get content until </table> or end of reasonable section
            tr_end = html.find('</table>', tr_start)
            if tr_end < 0:
                tr_end = min(tr_start + 1000, len(html))
        else:
            tr_end = next_tr
        
        tr_content = html[tr_start:tr_end]
        
        # Extract ATU number and title
        # The id attribute gives us the ATU number (sometimes with suffixes like "2A")
        num_match = re.match(r"(\d+)", tr_id_str)
        if not num_match:
            pos = tr_end
            continue

        atu_number = int(num_match.group(1))
        
        # Extract title from the <a> tag
        link_match = re.search(r'<a[^>]*href=[\'\"]([^\'\"]*)[\'\"][^>]*>([^<]+)</a>', tr_content)
        if link_match:
            detail_url = link_match.group(1).strip().replace("&amp;", "&")
            title = link_match.group(2).strip()
            
            # Only include if within the expected range
            if range_start <= atu_number <= range_end:
                atu_types.append(
                    ATUType(
                        atu_number=atu_number,
                        title=title,
                        category_range=f"{range_start}-{range_end}",
                        detail_url=detail_url,
                    )
                )
        
        pos = tr_end
    
    return atu_types


def _get_all_range_urls(html: str) -> list[Tuple[int, int, str]]:
    """Get all range URLs to crawl, prioritizing smaller (more granular) ranges.
    
    Strategy: Process ranges from smallest to largest. For ranges that are
    subsumed by already-processed ranges, skip them to avoid duplicates.
    """
    ranges = _extract_range_links_from_main_page(html)
    
    # Extract categories to identify levels
    categories = _extract_categories_from_main_page(html)
    level3_categories = {(cat.start_index, cat.end_index): cat for cat in categories if cat.level == 3}
    level2_categories = {(cat.start_index, cat.end_index): cat for cat in categories if cat.level == 2}
    
    # Create a dictionary to map ranges to their level
    range_levels = {}
    for start, end, url in ranges:
        key = (start, end)
        if key in level3_categories:
            range_levels[key] = (3, url)
        elif key in level2_categories:
            range_levels[key] = (2, url)
        else:
            range_levels[key] = (1, url)
    
    # Sort ranges: level 3 first, then level 2, then level 1
    # Within each level, sort by span (smallest first)
    sorted_ranges = []
    for start, end, url in ranges:
        key = (start, end)
        level, _ = range_levels[key]
        span = end - start
        sorted_ranges.append((level, span, start, end, url))
    
    # Sort by level (descending: 3 before 2 before 1) and span (ascending)
    sorted_ranges.sort(key=lambda x: (-x[0], x[1], x[2], x[3]))
    
    # Return all ranges sorted by granularity (smallest first)
    # We'll handle deduplication when collecting ATU types (using seen_numbers set)
    # This ensures we get all types even if some are in both parent and child ranges
    return [(start, end, url) for _, _, start, end, url in sorted_ranges]


def _html_fragment_to_text(fragment_html: str) -> str:
    """Convert an HTML fragment to readable plain text."""
    text = fragment_html
    # Normalize line breaks first
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</\s*p\s*>", "\n", text, flags=re.IGNORECASE)
    # Drop scripts/styles
    text = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
    # Strip tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Unescape entities and normalize whitespace
    text = html_lib.unescape(text)
    text = re.sub(r"[\t\r ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _extract_description_from_type_page(type_page_html: str) -> Optional[str]:
    """Extract the Description field from a single ATU type page.

    The exact HTML structure can vary, so this uses a small set of fallback
    patterns and returns plain text.
    """
    patterns = [
        # Section-style headings (as seen on mftd.org): <h2>Description</h2> ... <h2>Examples</h2>
        r"<h[1-6][^>]*>\s*Description\s*</h[1-6]>\s*(.*?)(?=<h[1-6][^>]*>\s*(?:Examples|External\s+Examples|References|Notes)\s*</h[1-6]>|$)",
        # Table-style: <td>Description</td><td>...</td>
        r"<td[^>]*>\s*Description\s*</td>\s*<td[^>]*>(.*?)</td>",
        r"<th[^>]*>\s*Description\s*</th>\s*<td[^>]*>(.*?)</td>",
        # Bold label style: <b>Description:</b> ...
        r"<b[^>]*>\s*Description\s*:?\s*</b>\s*(.*?)(?:<br\b|</p>|</div>|</td>)",
        # Sometimes called Summary
        r"<h[1-6][^>]*>\s*Summary\s*</h[1-6]>\s*(.*?)(?=<h[1-6][^>]*>\s*(?:Examples|External\s+Examples|References|Notes)\s*</h[1-6]>|$)",
        r"<td[^>]*>\s*Summary\s*</td>\s*<td[^>]*>(.*?)</td>",
        r"<th[^>]*>\s*Summary\s*</th>\s*<td[^>]*>(.*?)</td>",
    ]

    for pattern in patterns:
        m = re.search(pattern, type_page_html, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            continue
        text = _html_fragment_to_text(m.group(1))
        if text:
            return text
    return None


def _populate_atu_type_descriptions(
    atu_types: list[ATUType],
    *,
    sleep_s: float,
    timeout_s: int = 30,
    threads: int = 8,
    max_types: Optional[int] = None,
) -> None:
    """Fetch and populate `description` for each ATU type using its detail page.

    Uses multi-threaded fetching for speed and shows a tqdm progress bar if
    available.
    """
    types_to_process = atu_types if max_types is None else atu_types[:max_types]

    # Deduplicate URLs so we fetch each detail page once.
    url_to_types: dict[str, list[ATUType]] = {}
    urls_in_order: list[str] = []
    for atu_type in types_to_process:
        if not atu_type.detail_url:
            continue
        url = atu_type.detail_url
        if url not in url_to_types:
            url_to_types[url] = []
            urls_in_order.append(url)
        url_to_types[url].append(atu_type)

    if not urls_in_order:
        return

    if tqdm is None:
        print("Note: install tqdm for a progress bar: pip install tqdm")

    url_to_description: dict[str, Optional[str]] = {}
    url_to_lock = threading.Lock()

    def _worker(url: str) -> tuple[str, Optional[str]]:
        if sleep_s > 0:
            time.sleep(sleep_s)
        try:
            page_html = _fetch_html(url, timeout_s=timeout_s)
            desc = _extract_description_from_type_page(page_html)
            return url, desc
        except Exception:
            return url, None

    max_workers = max(1, int(threads))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_worker, url) for url in urls_in_order]
        completed_iter = concurrent.futures.as_completed(futures)
        if tqdm is not None:
            completed_iter = tqdm(
                completed_iter,
                total=len(futures),
                desc="Fetching ATU descriptions",
                unit="page",
            )

        for fut in completed_iter:
            url, desc = fut.result()
            with url_to_lock:
                url_to_description[url] = desc

    for url, types in url_to_types.items():
        desc = url_to_description.get(url)
        for t in types:
            t.description = desc


def _write_csv(categories: list[ATUCategory], atu_types: list[ATUType], output_path: str) -> None:
    """Write categories and ATU types to CSV file."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start_index", "end_index", "category_name", "level"])
        
        # Write categories
        for cat in sorted(categories, key=lambda x: (x.start_index, x.level)):
            writer.writerow([
                cat.start_index,
                cat.end_index,
                cat.category_name,
                cat.level
            ])
        
        # Add separator or different section for ATU types?
        # For now, we'll create a separate file for ATU types


def _assign_hierarchical_categories(atu_types: list[ATUType], categories: list[ATUCategory]) -> None:
    """Assign hierarchical category information to each ATU type."""
    # Build maps for each level
    level1_map = {}  # start -> category
    level2_map = {}
    level3_map = {}
    
    for cat in categories:
        if cat.level == 1:
            for num in range(cat.start_index, cat.end_index + 1):
                if num not in level1_map:
                    level1_map[num] = cat.category_name
        elif cat.level == 2:
            for num in range(cat.start_index, cat.end_index + 1):
                if num not in level2_map:
                    level2_map[num] = cat.category_name
        elif cat.level == 3:
            for num in range(cat.start_index, cat.end_index + 1):
                if num not in level3_map:
                    level3_map[num] = cat.category_name
    
    # Assign categories to each ATU type
    for atu_type in atu_types:
        num = atu_type.atu_number
        atu_type.level_1_category = level1_map.get(num)
        atu_type.level_2_category = level2_map.get(num)
        atu_type.level_3_category = level3_map.get(num)


def _write_atu_types_csv(atu_types: list[ATUType], output_path: str) -> None:
    """Write ATU types to a separate CSV file with hierarchical information."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "atu_number", 
            "title", 
            "level_1_category",
            "level_2_category", 
            "level_3_category",
            "category_range",
            "detail_url",
            "description",
        ])
        
        for atu_type in sorted(atu_types, key=lambda x: x.atu_number):
            writer.writerow([
                atu_type.atu_number,
                atu_type.title,
                atu_type.level_1_category or "",
                atu_type.level_2_category or "",
                atu_type.level_3_category or "",
                atu_type.category_range or "",
                atu_type.detail_url or "",
                (atu_type.description or "").replace("\n", " ").strip(),
            ])


def _write_markdown(categories: list[ATUCategory], output_path: str) -> None:
    """Write categories to Markdown file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Resources\n")
        f.write("http://oaks.nvg.org/uther.html\n")
        f.write("https://sites.pitt.edu/~dash/folktexts2.html\n")
        f.write("http://www.mftd.org/index.php?action=atu\n")
        f.write("\n")
        f.write("# ATU (Aarne-Thompson-Uther) Index Structure\n\n")
        f.write("| ATU Range     | Category Name                                              | Level |\n")
        f.write("| :------------ | :--------------------------------------------------------- | :---- |\n")
        
        for cat in sorted(categories, key=lambda x: (x.start_index, x.level)):
            range_str = f"{cat.start_index}-{cat.end_index}"
            if cat.level == 1:
                range_str = f"**{range_str}**"
            
            category = cat.category_name
            if cat.level == 1:
                category = f"**{category}**"
            
            level_str = str(cat.level) if cat.level != 1 else f"**{cat.level}**"
            f.write(f"| {range_str:<13} | {category:<57} | {level_str:<5} |\n")


def _write_atu_types_markdown(atu_types: list[ATUType], output_path: str) -> None:
    """Write ATU types to Markdown file with hierarchical structure."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# ATU Types (Complete List with Hierarchy)\n\n")
        f.write("This file contains all individual ATU types scraped from mftd.org with hierarchical category information.\n\n")
        f.write("| ATU Number | Title | Level 1 | Level 2 | Level 3 | Range | Description |\n")
        f.write("| :--------- | :---- | :------ | :------ | :------ | :---- | :---------- |\n")
        
        for atu_type in sorted(atu_types, key=lambda x: x.atu_number):
            desc = (atu_type.description or "").replace("\n", " ").strip()
            # Escape pipe to keep Markdown table valid
            desc = desc.replace("|", "\\|")
            f.write(f"| {atu_type.atu_number} | {atu_type.title} | "
                   f"{atu_type.level_1_category or ''} | "
                   f"{atu_type.level_2_category or ''} | "
                   f"{atu_type.level_3_category or ''} | "
                   f"{atu_type.category_range or ''} | "
                   f"{desc} |\n")


def main(argv: list[str]) -> int:
    """Main entry point."""
    p = argparse.ArgumentParser(
        description="Scrape ATU types from mftd.org and generate CSV/MD files"
    )
    p.add_argument(
        "--csv",
        default="ATU_types.csv",
        help="Output CSV file for categories (default: ATU_types.csv)"
    )
    p.add_argument(
        "--md",
        default="ATU_types.md",
        help="Output Markdown file for categories (default: ATU_types.md)"
    )
    p.add_argument(
        "--atu-csv",
        default="ATU_types_complete.csv",
        help="Output CSV file for all ATU types (default: ATU_types_complete.csv)"
    )
    p.add_argument(
        "--atu-md",
        default="ATU_types_complete.md",
        help="Output Markdown file for all ATU types (default: ATU_types_complete.md)"
    )
    p.add_argument(
        "--url",
        default=BASE_URL,
        help=f"URL to scrape (default: {BASE_URL})"
    )
    p.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Delay between requests (seconds, default: 0.5)"
    )
    p.add_argument(
        "--with-descriptions",
        action="store_true",
        help="Also fetch each ATU type page to extract its Description (adds many requests)"
    )
    p.add_argument(
        "--desc-sleep",
        type=float,
        default=0.5,
        help="Delay between per-type description requests (seconds, default: 0.5)"
    )
    p.add_argument(
        "--desc-timeout",
        type=int,
        default=30,
        help="Timeout (seconds) for per-type description requests (default: 30)"
    )
    p.add_argument(
        "--desc-threads",
        type=int,
        default=8,
        help="Number of threads for fetching descriptions (default: 8)"
    )
    p.add_argument(
        "--max-types",
        type=int,
        default=None,
        help="Maximum number of ATU type pages to fetch descriptions for (for testing, default: all)"
    )
    p.add_argument(
        "--max-ranges",
        type=int,
        default=None,
        help="Maximum number of range pages to crawl (for testing, default: all)"
    )
    
    args = p.parse_args(argv)
    
    print(f"Fetching main ATU classification page from {args.url}...")
    time.sleep(args.sleep)
    
    try:
        main_html = _fetch_html(args.url)
        print(f"Fetched {len(main_html)} bytes of HTML")
    except Exception as e:
        print(f"Error fetching HTML: {e}", file=sys.stderr)
        return 1
    
    # Extract category structure
    print("Extracting category structure...")
    categories = _extract_categories_from_main_page(main_html)
    print(f"Found {len(categories)} categories")
    
    # Get all range URLs to crawl
    print("Finding range pages to crawl...")
    range_urls = _get_all_range_urls(main_html)
    print(f"Found {len(range_urls)} range pages")
    
    if args.max_ranges:
        range_urls = range_urls[:args.max_ranges]
        print(f"Limiting to first {len(range_urls)} ranges (--max-ranges)")
    
    # Crawl all range pages to extract ATU types
    print(f"\nCrawling {len(range_urls)} range pages to extract ATU types...")
    all_atu_types = []
    seen_numbers: Set[int] = set()
    
    for i, (start, end, url) in enumerate(range_urls, 1):
        print(f"[{i}/{len(range_urls)}] Fetching range {start}-{end}...", end=" ")
        try:
            time.sleep(args.sleep)
            range_html = _fetch_html(url)
            atu_types = _extract_atu_types_from_range_page(range_html, start, end)
            
            # Filter duplicates
            new_types = [t for t in atu_types if t.atu_number not in seen_numbers]
            for t in new_types:
                seen_numbers.add(t.atu_number)
            
            all_atu_types.extend(new_types)
            print(f"found {len(atu_types)} types ({len(new_types)} new)")
        except Exception as e:
            print(f"ERROR: {e}")
            continue
    
    print(f"\nTotal ATU types extracted: {len(all_atu_types)}")
    
    # Assign hierarchical category information to ATU types
    print("Assigning hierarchical categories to ATU types...")
    _assign_hierarchical_categories(all_atu_types, categories)

    if args.with_descriptions:
        print(f"Writing pre-fetch ATU types snapshot (with URLs) to {args.atu_csv}...")
        _write_atu_types_csv(all_atu_types, args.atu_csv)
        print("Fetching per-type descriptions (this can take a while)...")
        _populate_atu_type_descriptions(
            all_atu_types,
            sleep_s=args.desc_sleep,
            timeout_s=args.desc_timeout,
            threads=args.desc_threads,
            max_types=args.max_types,
        )
    
    # Write category files
    print(f"Writing categories to {args.csv} and {args.md}...")
    _write_csv(categories, all_atu_types, args.csv)
    _write_markdown(categories, args.md)
    
    # Write ATU types files
    print(f"Writing ATU types to {args.atu_csv} and {args.atu_md}...")
    _write_atu_types_csv(all_atu_types, args.atu_csv)
    _write_atu_types_markdown(all_atu_types, args.atu_md)
    
    print("\nDone!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
