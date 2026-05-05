import sqlite3
import html
from pathlib import Path

DB_NAME = "classroom.db"
OUTPUT_FILE = "events_table_preview.html"

db_path = Path(DB_NAME)

if not db_path.exists():
    raise FileNotFoundError(f"Could not find {DB_NAME} in this folder.")

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Check available tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print("Tables found:", tables)

if "events" not in tables:
    raise Exception("No 'events' table found. Check the table name in your database.")

# Get column names
cursor.execute("PRAGMA table_info(events);")
columns = [row[1] for row in cursor.fetchall()]

print("Events table columns:", columns)

# Select rows
cursor.execute("SELECT * FROM events ORDER BY rowid DESC LIMIT 30;")
rows = cursor.fetchall()

conn.close()

# Build HTML
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ICPS SQLite Events Table</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            color: #1f2937;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 8px;
        }
        p {
            color: #4b5563;
            margin-bottom: 24px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
        }
        th {
            background: #e5e7eb;
            text-align: left;
            padding: 10px;
            border: 1px solid #9ca3af;
        }
        td {
            padding: 10px;
            border: 1px solid #d1d5db;
        }
        tr:nth-child(even) {
            background: #f9fafb;
        }
    </style>
</head>
<body>
    <h1>SQLite Events Table - classroom.db</h1>
    <p>Recent ICPS feedback events stored in the local SQLite database.</p>
    <table>
        <thead>
            <tr>
"""

for col in columns:
    html_content += f"<th>{html.escape(col)}</th>"

html_content += """
            </tr>
        </thead>
        <tbody>
"""

for row in rows:
    html_content += "<tr>"
    for value in row:
        html_content += f"<td>{html.escape(str(value))}</td>"
    html_content += "</tr>"

html_content += """
        </tbody>
    </table>
</body>
</html>
"""

Path(OUTPUT_FILE).write_text(html_content, encoding="utf-8")

print(f"Created {OUTPUT_FILE}. Open it in your browser and screenshot the table.")