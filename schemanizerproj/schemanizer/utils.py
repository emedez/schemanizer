"""Utility functions."""

def fetchall(conn, query, args=None):
    """Executes query and returns all rows."""
    rows = None
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        rows = cur.fetchall()
    finally:
        cur.close()
    return rows


def fetchone(conn, query, args=None):
    """Executes query and returns a single row."""
    row = None
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        row = cur.fetchone()
    finally:
        cur.close()
    return row


def execute(conn, query, args=None):
    """Executes query only."""
    cur = conn.cursor()
    try:
        cur.execute(query, args)
    finally:
        cur.close()
