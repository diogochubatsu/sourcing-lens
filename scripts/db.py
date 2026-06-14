"""Database connection helper for arbtbr.

Usage:
    from scripts.db import query, execute
    
    # Simple query
    rows = query("SELECT * FROM products WHERE platform = %s", ('ml',))
    
    # Execute (INSERT/UPDATE/DELETE)
    execute("INSERT INTO products ...", params)
"""

import os
import sys

# Add backend to path for database module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'backend'))

from database import init_pool, close_pool, query, execute, execute_returning, get_conn, get_cursor
