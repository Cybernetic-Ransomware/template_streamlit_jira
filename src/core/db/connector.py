import sqlite3
from pathlib import Path

from src.core.db.sql import CREATE_TABLE


class SQLiteConnector:
    def __init__(self, db_filename: str = "baza.db"):
        self.db_path = Path(__file__).parent / "temp" / db_filename
        self._ensure_database_file()
        self.conn = None
        self.cursor = None

    def _ensure_database_file(self):
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Tworzenie nowej bazy danych pod: {self.db_path}")
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute(CREATE_TABLE)

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None
            self.cursor = None

    def insert_issue(self, name: str):
        assert self.cursor is not None
        assert self.conn is not None

        self.cursor.execute(r"INSERT INTO blacklist (name) VALUES (?)", (name,))
        self.conn.commit()

    def remove_by_id(self, record_id: int) -> bool:
        assert self.cursor is not None
        assert self.conn is not None

        self.cursor.execute(
            "SELECT * FROM blacklist WHERE id = ?", (record_id,)
        ).fetchall()
        self.cursor.execute("DELETE FROM blacklist WHERE id = ?", (record_id,))
        self.conn.commit()

        return self.cursor.rowcount > 0

    def fetch_all(self):
        self.cursor.execute(r"SELECT * FROM blacklist")
        return self.cursor.fetchall()
