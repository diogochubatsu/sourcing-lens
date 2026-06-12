"""
ArbitLens Database Connection Pool
"""
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager
from config import get_settings

_pool = None


def init_pool():
    global _pool
    settings = get_settings()
    _pool = psycopg2.pool.ThreadedConnectionPool(2, 10, dsn=settings.database_url)


def close_pool():
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None


@contextmanager
def get_conn():
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
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
        finally:
            cur.close()
