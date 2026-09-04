import sqlite3
import threading
from typing import Set

from config import DB_PATH

class SeenURLStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS seen_urls (
                        url TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    '''
                )
                conn.commit()

    def add(self, url: str) -> bool:
        """Returns True if inserted, False if already exists."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                try:
                    conn.execute('INSERT INTO seen_urls (url) VALUES (?)', (url,))
                    conn.commit()
                    return True
                except sqlite3.IntegrityError:
                    return False

    def is_seen(self, url: str) -> bool:
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT 1 FROM seen_urls WHERE url = ?', (url,))
                return cursor.fetchone() is not None
