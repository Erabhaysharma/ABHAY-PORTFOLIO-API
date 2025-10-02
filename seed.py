import sqlite3
import json

# Connect to SQLite
conn = sqlite3.connect("data.db")
cursor = conn.cursor()

# ---------- CREATE TABLES ----------
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT,
    company TEXT,
    type TEXT,
    duration TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    icon TEXT,
    name TEXT,
    percent INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    stack TEXT,
    code TEXT,
    image TEXT,
    snippet TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    short_description TEXT,
    author TEXT,
    link TEXT
)
""")

# ---------- LOAD JSON & INSERT ----------

# Admin
with open("data/admin.json", "r", encoding="utf-8") as f:
    admin = json.load(f)
cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)",
               (admin["username"], admin["password"]))

# Experience
with open("data/exprence.json", "r", encoding="utf-8") as f:
    data = json.load(f)
experiences = data["experience"]  # get the list inside the "experience" key
for exp in experiences:
    cursor.execute("INSERT INTO experience (role, company, type, duration) VALUES (?, ?, ?, ?)",
                   (exp["role"], exp["company"], exp["type"], exp["duration"]))


# Skills
with open("data/skill.json", "r", encoding="utf-8") as f:
    skills = json.load(f)
for category in skills:
    for skill in category["skills"]:
        cursor.execute("INSERT INTO skills (category, icon, name, percent) VALUES (?, ?, ?, ?)",
                       (category["name"], category["icon"], skill["name"], skill["percent"]))

# Projects
with open("data/projects_demo.json", "r", encoding="utf-8") as f:
    projects = json.load(f)
for project in projects:
    cursor.execute("INSERT INTO projects (id, title, description, stack, code, image, snippet) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (project["id"], project["title"], project["description"], 
                    json.dumps(project["stack"]), project["code"], project["image"], project["snippet"]))

# Research
with open("data/research.json", "r", encoding="utf-8") as f:
    researches = json.load(f)
for res in researches:
    cursor.execute("INSERT INTO research (title, short_description, author, link) VALUES (?, ?, ?, ?)",
                   (res["title"], res["short_description"], res["author"], res["link"]))

# ---------- SAVE & CLOSE ----------
conn.commit()
conn.close()

print("✅ Database seeded successfully!")
