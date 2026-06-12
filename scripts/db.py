"""Database connection helper for arbtbr.

Usage:
    from scripts.db import get_conn, query, execute
    
    # Get raw connection
    conn = get_conn()
    
    # Simple query
    rows = query("SELECT * FROM products WHERE platform = %s", ('ml',))
    
    # Execute (INSERT/UPDATE/DELETE)
    execute("INSERT INTO products ...", params)
"""

import os
import psycopg2
import psycopg2.extras

# Load .env manually (dotenv doesn't handle our format well)
_ENV_LOADED = False

def _load_env():
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k not in os.environ:  # Don't override existing env vars
                        os.environ[k] = v
    _ENV_LOADED = True

def get_conn():
    """Get a psycopg2 connection to arbtbr database."""
    _load_env()
    # Use keyword args to avoid URL parsing issues with special chars in password
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user='hermes1688',
        password='Lndgcp@#12',
        dbname='arbtbr'
    )

def query(sql, params=None, dict_cursor=True):
    """Execute a SELECT query and return rows."""
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor if dict_cursor else None)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()

def execute(sql, params=None):
    """Execute an INSERT/UPDATE/DELETE and return rowcount."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        rowcount = cur.rowcount
        cur.close()
        return rowcount
    finally:
        conn.close()

def execute_returning(sql, params=None):
    """Execute INSERT ... RETURNING and return the result."""
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = cur.fetchall()
        conn.commit()
        cur.close()
        return result
    finally:
        conn.close()
