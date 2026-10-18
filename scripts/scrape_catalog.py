#!/usr/bin/env python3
"""Collect public LuLu category snapshots and distinct priced/image-backed SKUs.

Uses canonical sitemap categories, not disallowed pagination or private APIs.
The checkpoint makes an interrupted run resumable; never synthesizes products.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.catalog.sources import (
    BASE,
    CATEGORIES,
    category_for,
    listing,
    products_from_listing,
)  # noqa: E402


def allowed(url: str, robots: str) -> bool:
    # Read generic crawler rules; this application identifies itself explicitly.
    target = urlparse(url).path + (
        "?" + urlparse(url).query if urlparse(url).query else ""
    )
    active = False
    matches = []
    for line in robots.splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key, value = key.strip().lower(), value.split("#")[0].strip()
        if key == "user-agent":
            active = value == "*"
        elif active and key in {"allow", "disallow"} and value:
            pattern = re.escape(value).replace(r"\*", ".*").replace(r"\$", "$")
            if re.match(pattern, target):
                matches.append((len(value.replace("*", "")), key == "allow"))
    return max(matches, default=(0, True))[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-per-category", type=int, default=1000)
    parser.add_argument("--directory", type=Path, default=Path("data/local/catalog"))
    parser.add_argument("--max-pages", type=int, default=260)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    checkpoint = args.directory / "crawl-state.json"
    state = (
        json.loads(checkpoint.read_text())
        if checkpoint.exists()
        else {"completed": [], "errors": {}}
    )
    records_path = args.directory / "products.jsonl"
    records = {}
    if records_path.exists():
        for line in records_path.read_text().splitlines():
            row = json.loads(line)
            records[row["product_id"]] = row
    counts = Counter(r["category"] for r in records.values())
    client = httpx.Client(
        timeout=45,
        follow_redirects=True,
        headers={"User-Agent": "ARC-CatalogResearch/1.0"},
    )
    robots = client.get(BASE + "/robots.txt").raise_for_status().text
    sitemap = client.get(BASE + "/en-ae/sitemap/categories-1").raise_for_status().text
    urls = [
        e.text
        for e in ET.fromstring(sitemap).iter()
        if e.tag.endswith("loc") and e.text
    ]
    urls = [u for u in urls if "/grocery-food-cupboard" in u or "/fresh-food-" in u]
    urls = [u for u in urls if "flowers" not in u and "plants" not in u]
    # Visit specific leaf groups first to avoid repeatedly collecting broad-page leaders.
    urls.sort(key=lambda u: (-u.count("-"), u))
    last_request = 0.0
    with records_path.open("a") as output:
        for index, url in enumerate(urls[: args.max_pages]):
            if url in state["completed"]:
                continue
            guess = category_for({}, url)
            if guess and counts[guess] >= args.target_per_category:
                continue
            if all(counts[c] >= args.target_per_category for c in CATEGORIES):
                break
            if not allowed(url, robots):
                state["errors"][url] = "robots-disallowed"
                continue
            cache = args.directory / (
                "page-" + hashlib.sha256(url.encode()).hexdigest()[:20] + ".html.gz"
            )
            try:
                if cache.exists():
                    html = gzip.decompress(cache.read_bytes()).decode()
                else:
                    time.sleep(max(0, 1.1 - (time.monotonic() - last_request)))
                    response = client.get(url)
                    last_request = time.monotonic()
                    response.raise_for_status()
                    html = response.text
                    cache.write_bytes(gzip.compress(html.encode()))
                data = listing(html)
                for row in products_from_listing(data, url):
                    old = records.get(row["product_id"])
                    if (
                        old is None
                        and counts[row["category"]] >= args.target_per_category
                    ):
                        continue
                    if (
                        old
                        and old["source_stock_quantity"] is not None
                        and row["source_stock_quantity"] is None
                    ):
                        continue
                    if old is None or old["category"] != row["category"]:
                        if old is not None:
                            counts[old["category"]] -= 1
                        counts[row["category"]] += 1
                    records[row["product_id"]] = row
                    output.write(json.dumps(row, ensure_ascii=False) + "\n")
                output.flush()
                state["completed"].append(url)
                state["errors"].pop(url, None)
                print(
                    f"{index + 1}/{len(urls)} · unique={len(records)} · {dict(counts)}",
                    flush=True,
                )
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                state["errors"][url] = str(exc)[:250]
                print(f"Skipped {url}: {str(exc)[:100]}", flush=True)
            checkpoint.write_text(json.dumps(state, indent=2))
    report = {
        "distinct_products": len(records),
        "categories": dict(counts),
        "target_per_category": args.target_per_category,
        "completed_pages": len(state["completed"]),
        "errors": state["errors"],
        "sources": {
            "LuLu UAE": "public category SSR snapshots",
            "Carrefour UAE": "public pages returned empty HTML",
            "Noon UAE": "public grocery pages timed out",
        },
    }
    (args.directory / "coverage.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
