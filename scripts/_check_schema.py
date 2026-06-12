"""Check products table schema."""
import sys, os
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

cols = query("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='products' ORDER BY ordinal_position")
for c in cols:
    print(f'{c["column_name"]:25s} {c["data_type"]}')
