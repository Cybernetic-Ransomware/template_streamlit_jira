import json
import sqlite3
from pathlib import Path
from typing import Any

import pendulum

from src.config.conf_logger import setup_logger
from src.core.db.sql import CREATE_TABLE, SAVE_SNAPSHOT

logger = setup_logger(__name__, "sqlite")


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

    def snapshot_issues_to_db(self, issues: list[dict[str, Any]]):
        assert self.cursor is not None
        assert self.conn is not None

        now = pendulum.now(tz='Europe/Warsaw').to_iso8601_string()

        for issue in issues:
            try:
                issue_key = issue.get("issue_link", "").split("/")[-1]
                payload = json.dumps(issue, default=str)
                self.cursor.execute(SAVE_SNAPSHOT, (issue_key, now, payload))
            except Exception as e:
                logger.error(e)
        self.conn.commit()
