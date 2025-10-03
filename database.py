import sqlite3
from contextlib import contextmanager
import json

DB_NAME = "data.db"

@contextmanager
def get_db():
    """Context manager for SQLite connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    try:
        yield conn
    finally:
        conn.close()


# ---------- Optional helper functions for each table ----------

def fetch_admins():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin")
        return [dict(row) for row in cursor.fetchall()]

def fetch_experience():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experience")
        return [dict(row) for row in cursor.fetchall()]

def fetch_skills():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills")
        return [dict(row) for row in cursor.fetchall()]

def fetch_projects():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        # Convert stack JSON string back to list
        projects = []
        for row in rows:
            project = dict(row)
            project["stack"] = json.loads(project["stack"])
            projects.append(project)
        return projects

def fetch_research():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research")
        return [dict(row) for row in cursor.fetchall()]
