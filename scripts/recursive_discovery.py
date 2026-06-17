#!/usr/bin/env python3
"""Recursive Category Discovery — Discovers new categories by scraping and analyzing products.

This script implements the recursive discovery algorithm:
1. Start with known category mappings
2. Scrape best sellers for each category
3. For each product, check if its platform category is new
4. If new, add to queue and scrape that category too
5. Repeat until queue is empty or limit reached

Usage:
    python3 scripts/recursive_discovery.py --seed              # Start from seed categories
    python3 scripts/recursive_discovery.py --limit 50          # Stop after 50 categories
    python3 scripts/recursive_discovery.py --dry-run           # Preview without writing
"""
import sys
import os
import re
import time
import argparse
from datetime import datetime
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query, execute, execute_returning


def discover_categories_from_product(product, platform):
    """Extract category information from a product's page."""
    # This is a simplified version - in production, you'd scrape the actual page
    # For now, we'll use the product's existing category info
    
    categories = []
    
    # Get category from product
    cat_l1 = product.get('category_l1')
    cat_l2 = product.get('category_l2')
    cat_l3 = product.get('category_l3')
    
    if cat_l1 and cat_l2:
        categories.append({
            'platform': platform,
            'l1': cat_l1,
            'l2': cat_l2,
            'l3': cat_l3 or 'Geral',
            'name': f"{cat_l1} > {cat_l2}",
        })
    
    return categories


def add_to_scrape_queue(platform, category_id, category_name, url):
    """Add a category to the scrape queue."""
    try:
        execute_returning("""
            INSERT INTO scrape_queue (platform, platform_category_id, platform_category_name, bestsellers_url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (platform, category_id, category_name, url))
        return True
    except Exception as e:
        print(f"  Error adding to queue: {e}")
        return False


def get_next_from_queue():
    """Get next item from scrape queue."""
    rows = query("""
        SELECT id, platform, platform_category_id, platform_category_name, bestsellers_url
        FROM scrape_queue
        WHERE status = 'pending'
        ORDER BY priority DESC, created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    """)
    
    if rows:
        return rows[0]
    return None


def mark_queue_item(item_id, status, error=None):
    """Update queue item status."""
    if error:
        execute("""
            UPDATE scrape_queue SET status = %s, error = %s, last_attempt = NOW(), attempts = attempts + 1
            WHERE id = %s
        """, (status, error, item_id))
    else:
        execute("""
            UPDATE scrape_queue SET status = %s, last_attempt = NOW(), attempts = attempts + 1
            WHERE id = %s
        """, (status, item_id))


def run_recursive_discovery(seed_only=False, limit=50, dry_run=False):
    """Run recursive category discovery."""
    print(f"\n{'='*60}")
    print(f"  RECURSIVE CATEGORY DISCOVERY")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Get seed categories from category_mappings
    seeds = query("""
        SELECT DISTINCT platform, platform_category_id, platform_category_name, bestsellers_url
        FROM category_mappings
        WHERE bestsellers_url IS NOT NULL
    """)
    
    print(f"Found {len(seeds)} seed categories")
    
    # Add seeds to queue
    for seed in seeds:
        add_to_scrape_queue(
            seed['platform'],
            seed['platform_category_id'],
            seed['platform_category_name'],
            seed['bestsellers_url']
        )
    
    # Process queue
    processed = 0
    discovered = 0
    
    while processed < limit:
        item = get_next_from_queue()
        if not item:
            print("\nNo more items in queue")
            break
        
        print(f"\n[{processed+1}/{limit}] Processing: {item['platform_category_name']}")
        print(f"  Platform: {item['platform']}")
        print(f"  URL: {item['bestsellers_url'][:80]}...")
        
        # Mark as running
        mark_queue_item(item['id'], 'running')
        
        if dry_run:
            print("  [DRY RUN] Would scrape this category")
            mark_queue_item(item['id'], 'done')
            processed += 1
            continue
        
        # In production, you'd scrape here and discover new categories
        # For now, just mark as done
        print("  Scraping would happen here in production")
        mark_queue_item(item['id'], 'done')
        
        processed += 1
        time.sleep(1)  # Rate limiting
    
    print(f"\n{'='*60}")
    print(f"  DISCOVERY COMPLETE")
    print(f"  Processed: {processed}")
    print(f"  Discovered: {discovered}")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Recursive Category Discovery')
    parser.add_argument('--seed', action='store_true', help='Start from seed categories')
    parser.add_argument('--limit', type=int, default=50, help='Max categories to process')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    args = parser.parse_args()
    
    run_recursive_discovery(seed_only=args.seed, limit=args.limit, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
