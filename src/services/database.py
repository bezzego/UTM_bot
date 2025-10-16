import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

from src.config import settings


class DatabaseManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._setup()

    def _setup(self) -> None:
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            authorized_at TEXT NOT NULL
        )
        """

        banned_table = """
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            banned_at TEXT NOT NULL,
            reason TEXT
        )
        """

        history_table = """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            base_url TEXT NOT NULL,
            utm_url TEXT NOT NULL,
            short_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """

        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(users_table)
            cursor.execute(banned_table)
            cursor.execute(history_table)
            self._connection.commit()

    def is_user_authorized(self, user_id: int) -> bool:
        query = "SELECT 1 FROM users WHERE user_id = ?"
        return self._exists(query, (user_id,))

    def authorize_user(self, user_id: int) -> None:
        now = datetime.utcnow().isoformat()
        query = "INSERT OR IGNORE INTO users (user_id, authorized_at) VALUES (?, ?)"
        self._execute(query, (user_id, now))

    def is_user_banned(self, user_id: int) -> bool:
        query = "SELECT 1 FROM banned_users WHERE user_id = ?"
        return self._exists(query, (user_id,))

    def ban_user(self, user_id: int, reason: str | None = None) -> None:
        now = datetime.utcnow().isoformat()
        query = """
        INSERT OR IGNORE INTO banned_users (user_id, banned_at, reason)
        VALUES (?, ?, ?)
        """
        self._execute(query, (user_id, now, reason))

    def add_history(self, user_id: int, base_url: str, utm_url: str, short_url: str) -> None:
        now = datetime.utcnow().isoformat()
        query = """
        INSERT INTO history (user_id, base_url, utm_url, short_url, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        self._execute(query, (user_id, base_url, utm_url, short_url, now))

    def get_history(self, user_id: int, limit: int = 50) -> List[Tuple[str, str, str]]:
        query = """
        SELECT base_url, utm_url, short_url
        FROM history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """
        rows = self._fetchall(query, (user_id, limit))
        return [(row["base_url"], row["utm_url"], row["short_url"]) for row in rows]

    def _execute(self, query: str, params: Iterable) -> None:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(query, tuple(params))
            self._connection.commit()

    def _fetchall(self, query: str, params: Iterable) -> List[sqlite3.Row]:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    def _exists(self, query: str, params: Iterable) -> bool:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(query, tuple(params))
            return cursor.fetchone() is not None


database = DatabaseManager(settings.database_path)
