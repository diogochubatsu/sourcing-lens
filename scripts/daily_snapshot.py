#!/usr/bin/env python3
"""Daily snapshot: records price + sales for all active products."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query, execute


def take_snapshot():
    """Record current price and sales for all active products."""
    products = query("SELECT id, price, sales_30d FROM products WHERE is_active=true")
    count = 0
    for p in products:
        execute(
            "INSERT INTO price_history (product_id, price, sales_30d) VALUES (%s, %s, %s)",
            (p['id'], p['price'], p['sales_30d'])
        )
        count += 1
    return count


if __name__ == "__main__":
    count = take_snapshot()
    print(f"Snapshots recorded: {count}")
