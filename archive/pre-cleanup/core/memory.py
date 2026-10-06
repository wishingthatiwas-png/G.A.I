import sqlite3
from pathlib import Path
from time import time

class Memory:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, ts REAL NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL)')
        self.db.commit()

    def remember(self, kind, data):
        import json
        self.db.execute('INSERT INTO events(ts, kind, data) VALUES (?, ?, ?)', (time(), kind, json.dumps(data)))
        self.db.commit()
