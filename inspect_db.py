import sqlite3

DB_NAME = "data.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# List all tables
print("📂 Tables in DB:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for t in tables:
    print(" -", t[0])

# Show schema of skills table
print("\n📝 Schema of skills:")
cursor.execute("PRAGMA table_info(skills);")
for col in cursor.fetchall():
    print(col)

# Optional: show first 5 rows
print("\n📊 First 5 rows in skills:")
cursor.execute("SELECT * FROM skills LIMIT 10;")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
