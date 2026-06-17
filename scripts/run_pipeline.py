#!/usr/bin/env python3
"""Run Pipeline — Execute the full scraping and matching pipeline.

Usage:
    python3 scripts/run_pipeline.py --all                    # Full pipeline
    python3 scripts/run_pipeline.py --scrape                 # Scrape only
    python3 scripts/run_pipeline.py --match                  # Match only
    python3 scripts/run_pipeline.py --embed                  # Generate embeddings only
    python3 scripts/run_pipeline.py --category Audio         # Single category
"""
import sys
import os
import argparse
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    return result.returncode == 0


def run_pipeline(scrape=True, embed=True, match=True, category=None):
    """Run the full pipeline."""
    start_time = datetime.now()
    
    print(f"\n{'#'*60}")
    print(f"  ARBITLENS PIPELINE")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    success = True
    
    # Step 1: Scrape
    if scrape:
        cmd = "cd /home/hermeshideki/arbt.ly && .venv/bin/python3 scripts/scrape_best_sellers.py --all"
        if category:
            cmd += f" --category {category}"
        
        if not run_command(cmd, "Step 1: Scraping Best Sellers"):
            print("  Warning: Scraping had errors")
    
    # Step 2: Generate Embeddings
    if embed:
        cmd = "cd /home/hermeshideki/arbt.ly && .venv/bin/python3 scripts/generate_embeddings.py --limit 500"
        if category:
            cmd += f" --category {category}"
        
        if not run_command(cmd, "Step 2: Generating CLIP Embeddings"):
            print("  Warning: Embedding generation had errors")
    
    # Step 3: Match Products
    if match:
        cmd = "cd /home/hermeshideki/arbt.ly && .venv/bin/python3 scripts/matching_v6.py"
        
        if not run_command(cmd, "Step 3: Matching Products"):
            print("  Warning: Matching had errors")
    
    # Step 4: Validate
    if not run_command("cd /home/hermeshideki/arbt.ly && .venv/bin/python3 scripts/validate_mappings.py", 
                      "Step 4: Validating Mappings"):
        print("  Warning: Validation had issues")
    
    # Step 5: Snapshot
    if not run_command("cd /home/hermeshideki/arbt.ly && .venv/bin/python3 scripts/daily_snapshot.py",
                      "Step 5: Daily Snapshot"):
        print("  Warning: Snapshot had errors")
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'#'*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"  Duration: {duration}")
    print(f"  Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    # Print stats
    stats = query("""
        SELECT 
            (SELECT COUNT(*) FROM products WHERE is_active=true) as products,
            (SELECT COUNT(*) FROM matches) as matches,
            (SELECT COUNT(*) FROM category_mappings) as categories,
            (SELECT COUNT(*) FROM products WHERE embedding IS NOT NULL) as embedded
    """)
    
    if stats:
        s = stats[0]
        print(f"\n  Current State:")
        print(f"    Products: {s['products']}")
        print(f"    Matches: {s['matches']}")
        print(f"    Categories: {s['categories']}")
        print(f"    Embedded: {s['embedded']}")


def main():
    parser = argparse.ArgumentParser(description='Run Pipeline')
    parser.add_argument('--all', action='store_true', help='Run full pipeline')
    parser.add_argument('--scrape', action='store_true', help='Scrape only')
    parser.add_argument('--embed', action='store_true', help='Generate embeddings only')
    parser.add_argument('--match', action='store_true', help='Match only')
    parser.add_argument('--category', type=str, help='Process specific L1 category')
    args = parser.parse_args()
    
    if args.all or (not args.scrape and not args.embed and not args.match):
        run_pipeline(scrape=True, embed=True, match=True, category=args.category)
    else:
        run_pipeline(scrape=args.scrape, embed=args.embed, match=args.match, category=args.category)


if __name__ == '__main__':
    main()
