"""
ArbitLens Database Connection Pool
"""
import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager

_pool = None
_env_loaded = False


def _load_env():
    """Load .env file into environment variables (once)."""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    
    # Search for .env in multiple locations
    candidates = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env'),
        os.path.join(os.path.dirname(__file__), '..', 'config', '.env'),
        os.path.join(os.getcwd(), 'config', '.env'),
        os.path.join(os.getcwd(), '..', 'config', '.env'),
    ]
    for env_path in candidates:
        env_path = os.path.normpath(env_path)
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() not in os.environ:
                            os.environ[k.strip()] = v.strip()
            return


def init_pool(minconn=2, maxconn=10):
    """Initialize the connection pool. Call once at startup."""
    global _pool
    if _pool is not None:
        return
    
    _load_env()
    
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', '5432'))
    user = os.environ.get('DB_USER', 'hermes1688')
    password = os.environ.get('DB_PASSWORD', '')
    dbname = os.environ.get('DB_NAME', 'arbtbr')
    
    _pool = psycopg2.pool.ThreadedConnectionPool(
        minconn, maxconn,
        host=host, port=port, user=user, password=password, dbname=dbname
    )


def close_pool():
    """Close all connections in the pool."""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None


@contextmanager
def get_conn():
    """Context manager that yields a connection and handles commit/rollback."""
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


@contextmanager
def get_cursor():
    """Context manager that yields a RealDictCursor."""
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
        finally:
            cur.close()


def query(sql, params=None):
    """Execute a SELECT query and return rows as list of dicts."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def execute(sql, params=None):
    """Execute an INSERT/UPDATE/DELETE and return rowcount."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def execute_returning(sql, params=None):
    """Execute INSERT/UPDATE/DELETE ... RETURNING and return results."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()
