CREATE_TABLE = r"""
CREATE TABLE issue_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_key TEXT NOT NULL,
    snapshot_datetime TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""

SAVE_SNAPSHOT = r"""
    INSERT INTO issue_snapshots (issue_key, snapshot_datetime, payload_json)
    VALUES (?, ?, ?)
"""
