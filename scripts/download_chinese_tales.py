#!/usr/bin/env python3
"""Download (public/CC-licensed) Chinese folktale texts in CSV order.

This script fetches texts from MediaWiki projects (Wikisource first, then Wikipedia)
using their public API, and saves each story into datasets/ChineseTales/texts.

Notes
- Many items in the list are story *episodes* or modern works that may not have a
  public-domain full text online. The script will skip items where it can't find a
  sufficiently long text.
- Wikipedia/Wikisource content is generally licensed under CC BY-SA. The script
  stores basic attribution metadata at the top of each downloaded file.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable, Optional


DEFAULT_CSV = "datasets/ChineseTales/ChineseFolktalesList.csv"
DEFAULT_OUT_DIR = "datasets/ChineseTales/texts"

WIKISOURCE_API = "https://zh.wikisource.org/w/api.php"
WIKIPEDIA_API = "https://zh.wikipedia.org/w/api.php"

USER_AGENT = "fairytales_resarch/1.0 (MediaWiki API downloader; educational research)"


@dataclass(frozen=True)
class MediaWikiHit:
    title: str
    pageid: int


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._in_script_style = False

    def handle_starttag(self, tag: str, attrs):
        if tag in {"script", "style"}:
            self._in_script_style = True
        if tag in {"p", "br", "li", "div", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str):
        if tag in {"script", "style"}:
            self._in_script_style = False
        if tag in {"p", "li", "div"}:
            self._chunks.append("\n")

    def handle_data(self, data: str):
        if self._in_script_style:
            return
        text = data.strip()
        if not text:
            return
        self._chunks.append(text)

    def get_text(self) -> str:
        joined = " ".join(self._chunks)
        joined = html.unescape(joined)
        joined = re.sub(r"[ \t\u00A0]+", " ", joined)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        return joined.strip()


def _http_get_json(url: str, params: dict[str, str], timeout_s: int = 30) -> dict:
    query = urllib.parse.urlencode(params)
    full = f"{url}?{query}"
    req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} for {full}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error for {full}: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from {full}") from e


def _mediawiki_search(api: str, query: str, limit: int = 5) -> list[MediaWikiHit]:
    data = _http_get_json(
        api,
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(limit),
            "format": "json",
        },
    )
    hits: list[MediaWikiHit] = []
    for item in data.get("query", {}).get("search", []) or []:
        title = item.get("title")
        pageid = item.get("pageid")
        if isinstance(title, str) and isinstance(pageid, int):
            hits.append(MediaWikiHit(title=title, pageid=pageid))
    return hits


def _mediawiki_get_parse_html(api: str, title: str) -> Optional[str]:
    data = _http_get_json(
        api,
        {
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json",
            "redirects": "1",
        },
    )
    parse = data.get("parse")
    if not isinstance(parse, dict):
        return None
    text = parse.get("text")
    if not isinstance(text, dict):
        return None
    html_str = text.get("*")
    if not isinstance(html_str, str) or not html_str.strip():
        return None
    return html_str


def _mediawiki_get_extract(api: str, title: str) -> Optional[str]:
    # Wikipedia supports extracts well; Wikisource may or may not depending on config.
    data = _http_get_json(
        api,
        {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "exsectionformat": "plain",
            "redirects": "1",
            "titles": title,
            "format": "json",
        },
    )
    pages = data.get("query", {}).get("pages", {})
    if not isinstance(pages, dict):
        return None
    for _, page in pages.items():
        if not isinstance(page, dict):
            continue
        extract = page.get("extract")
        if isinstance(extract, str) and extract.strip():
            return extract.strip()
    return None


def _html_to_text(html_str: str) -> str:
    parser = _TextExtractor()
    parser.feed(html_str)
    return parser.get_text()


def _clean_title_for_filename(title: str) -> str:
    title = title.strip()
    title = re.sub(r"[\\/:*?\"<>|]", "_", title)
    title = re.sub(r"\s+", " ", title)
    return title


def _strip_source_markers(source: str) -> str:
    s = source or ""
    s = s.replace("《", "").replace("》", "")
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _looks_like_chinese_text(text: str) -> bool:
    # Quick heuristic: contains enough CJK chars.
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return cjk >= 200


def _download_from_wikisource(
    title: str,
    primary_source: str,
    min_chars: int,
    sleep_s: float,
) -> Optional[tuple[str, str]]:
    queries = [title, f"{title} 原文"]
    src = _strip_source_markers(primary_source)
    if src and src not in queries:
        queries.append(src)

    for q in queries:
        hits = _mediawiki_search(WIKISOURCE_API, q, limit=5)
        time.sleep(sleep_s)
        for hit in hits:
            html_str = _mediawiki_get_parse_html(WIKISOURCE_API, hit.title)
            time.sleep(sleep_s)
            if not html_str:
                continue
            text = _html_to_text(html_str)
            text = re.sub(r"\n\s*\[编辑\]\s*\n", "\n", text)
            if len(text) < min_chars:
                continue
            if not _looks_like_chinese_text(text):
                continue
            url = f"https://zh.wikisource.org/wiki/{urllib.parse.quote(hit.title)}"
            return text, url
    return None


def _download_from_wikipedia(
    title: str,
    min_chars: int,
    sleep_s: float,
) -> Optional[tuple[str, str]]:
    # Wikipedia is a fallback; it usually contains a synopsis, not a full text.
    hits = _mediawiki_search(WIKIPEDIA_API, title, limit=5)
    time.sleep(sleep_s)
    for hit in hits:
        extract = _mediawiki_get_extract(WIKIPEDIA_API, hit.title)
        time.sleep(sleep_s)
        if not extract:
            continue
        if len(extract) < min_chars:
            continue
        if not _looks_like_chinese_text(extract):
            continue
        url = f"https://zh.wikipedia.org/wiki/{urllib.parse.quote(hit.title)}"
        return extract, url
    return None


def _compose_file_header(
    rank: int,
    chinese_title: str,
    english_title: str,
    category: str,
    primary_source: str,
    source_url: str,
) -> str:
    now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    return (
        f"Title: {chinese_title}\n"
        f"Rank: {rank}\n"
        f"EnglishTitle: {english_title}\n"
        f"Category: {category}\n"
        f"PrimarySource: {primary_source}\n"
        f"SourceURL: {source_url}\n"
        f"License: CC BY-SA (MediaWiki projects)\n"
        f"DownloadedAt: {now}\n"
        "---\n\n"
    )


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=DEFAULT_CSV)
    p.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    p.add_argument("--target", type=int, default=30, help="Minimum number of texts to have")
    p.add_argument("--force", action="store_true", help="Overwrite existing files")
    p.add_argument(
        "--count-existing",
        action="store_true",
        default=True,
        help="Count already-present files toward the target (default: true)",
    )
    p.add_argument(
        "--no-count-existing",
        dest="count_existing",
        action="store_false",
        help="Do not count already-present files toward the target",
    )
    p.add_argument("--min-chars", type=int, default=1200, help="Minimum length to accept a text")
    p.add_argument("--sleep", type=float, default=0.5, help="Delay between requests (seconds)")

    args = p.parse_args(argv)

    csv_path = args.csv
    out_dir = args.out_dir

    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 2

    os.makedirs(out_dir, exist_ok=True)

    saved = 0
    skipped_existing = 0
    failures: list[str] = []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        if saved >= args.target:
            break

        try:
            rank = int((row.get("Rank") or "").strip())
        except ValueError:
            continue

        chinese_title = (row.get("Chinese Title") or "").strip()
        if not chinese_title:
            continue

        english_title = (row.get("English Title") or "").strip()
        category = (row.get("Category") or "").strip()
        primary_source = (row.get("Primary Source (出处)") or "").strip()

        safe_title = _clean_title_for_filename(chinese_title)
        out_name = f"{rank:03d}_{safe_title}.txt"
        out_path = os.path.join(out_dir, out_name)

        if os.path.exists(out_path) and not args.force:
            skipped_existing += 1
            if args.count_existing:
                saved += 1
            continue

        print(f"[{saved + 1}/{args.target}] Fetching: {rank} {chinese_title}")

        text_and_url = _download_from_wikisource(
            chinese_title,
            primary_source=primary_source,
            min_chars=args.min_chars,
            sleep_s=args.sleep,
        )
        if text_and_url is None:
            text_and_url = _download_from_wikipedia(
                chinese_title,
                min_chars=max(args.min_chars, 1500),
                sleep_s=args.sleep,
            )

        if text_and_url is None:
            failures.append(chinese_title)
            print(f"  - Skip (not found / too short): {chinese_title}")
            continue

        text, source_url = text_and_url
        header = _compose_file_header(
            rank=rank,
            chinese_title=chinese_title,
            english_title=english_title,
            category=category,
            primary_source=primary_source,
            source_url=source_url,
        )

        with open(out_path, "w", encoding="utf-8") as out:
            out.write(header)
            out.write(text.strip())
            out.write("\n")

        saved += 1

    print("\nDone.")
    print(f"Saved/Counted: {saved}")
    if skipped_existing:
        print(f"Existing skipped: {skipped_existing}")
    if failures:
        print(f"Failed ({len(failures)}): " + ", ".join(failures[:20]) + ("..." if len(failures) > 20 else ""))

    return 0 if saved >= args.target else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
