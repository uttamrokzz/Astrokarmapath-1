# -*- coding: utf-8 -*-
"""Add research tables. Run once."""

import turso_serverless as turso

URL   = "libsql://astrokarmapath-astrokarmapath.aws-ap-south-1.turso.io"
TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTAyNTQyNDEsImlkIjoiMDFhMGQzNmYtNzAwMS03ODc2LWI3YWYtNTA2YjRkYTlmZTJmIiwia2lkIjoib1NqRHltUlBYSDZaNmZYYWdKZkJia1h4WjJFNVZaSFZxQi1NVXhlY0hEcyIsInJpZCI6IjYzNWU1YzVhLWY5YWYtNGMxYi05ZGJhLTc3OTJlODkwNzQ0MSJ9.WQmRAnUNJtNkGYHoo8KtRWBg1REU0uxYKwOFvVauF01vgywN5rhAXj-jfdqktkrRH10Bct54IXpWrf2r97vZAQ"

conn = turso.connect(URL, auth_token=TOKEN)
cur = conn.cursor()

# --- research table ---
cur.execute("""
    CREATE TABLE IF NOT EXISTS research (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id       INTEGER NOT NULL,
        combination_id INTEGER,
        chart_ref      TEXT,
        research_date  TEXT,
        observation    TEXT,
        notes          TEXT,
        created_at     TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(event_id)       REFERENCES events(id)        ON DELETE CASCADE,
        FOREIGN KEY(combination_id) REFERENCES combinations(id)  ON DELETE SET NULL
    )
""")
print("research table ready")

cur.execute("CREATE INDEX IF NOT EXISTS idx_research_event ON research(event_id)")
print("idx_research_event ready")

# --- research_people link ---
cur.execute("""
    CREATE TABLE IF NOT EXISTS research_people (
        research_id INTEGER NOT NULL,
        person_id   INTEGER NOT NULL,
        PRIMARY KEY (research_id, person_id),
        FOREIGN KEY(research_id) REFERENCES research(id) ON DELETE CASCADE,
        FOREIGN KEY(person_id)   REFERENCES people(id)   ON DELETE CASCADE
    )
""")
print("research_people table ready")

conn.commit()
conn.close()
print("\nMigration complete.")