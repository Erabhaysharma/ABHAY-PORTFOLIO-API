import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Pick up DATABASE_URL from Render env vars
DATABASE_URL = os.getenv("DATABASE_URL")  # <-- use the env var name, not the URL itself

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True, future=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------- Helper functions ----------

def fetch_admins():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM admin"))
        return [dict(row._mapping) for row in result]


def fetch_experience():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM experience"))
        return [dict(row._mapping) for row in result]


def fetch_skills():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM skills"))
        return [dict(row._mapping) for row in result]


def fetch_projects():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM projects"))
        rows = result.fetchall()
        projects = []
        for row in rows:
            project = dict(row._mapping)
            # Convert stack JSON string back to list
            if project.get("stack"):
                project["stack"] = json.loads(project["stack"])
            projects.append(project)
        return projects


def fetch_research():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM research"))
        return [dict(row._mapping) for row in result]
