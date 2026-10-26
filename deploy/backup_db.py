"""
Daily backup of bot.db (users, history, usage counters).

Uses SQLite's own online-backup API, so it is safe to run while the bot is
running (a plain file copy could catch the database mid-write). Keeps the
most recent KEEP_DAYS backups and deletes older ones - only files in the
backup folder whose names look exactly like bot-YYYY-MM-DD.db.

Usage:  python deploy/backup_db.py [database_path] [backup_dir]
"""

import os
import re
import sqlite3
import sys
from datetime import date, timedelta

KEEP_DAYS = 14
NAME_PATTERN = re.compile(r"^bot-(\d{4})-(\d{2})-(\d{2})\.db$")


def main():
    database_path = sys.argv[1] if len(sys.argv) > 1 else "bot.db"
    backup_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(database_path)), "..", "backups")
    backup_dir = os.path.abspath(backup_dir)
    os.makedirs(backup_dir, exist_ok=True)
    os.chmod(backup_dir, 0o700)

    target = os.path.join(backup_dir, f"bot-{date.today().isoformat()}.db")
    temporary = target + ".partial"

    source = sqlite3.connect(database_path)
    destination = sqlite3.connect(temporary)
    with destination:
        source.backup(destination)
    destination.close()
    source.close()

    # Only keep the backup if it is a readable database with the expected tables.
    check = sqlite3.connect(temporary)
    tables = {row[0] for row in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    users = check.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    check.close()
    if "users" not in tables or "transcripts" not in tables:
        os.remove(temporary)
        raise SystemExit("Backup check failed: expected tables are missing")

    os.replace(temporary, target)
    os.chmod(target, 0o600)

    cutoff = date.today() - timedelta(days=KEEP_DAYS)
    removed = 0
    for name in os.listdir(backup_dir):
        match = NAME_PATTERN.match(name)
        if match and date(*map(int, match.groups())) < cutoff:
            os.remove(os.path.join(backup_dir, name))
            removed += 1

    print(f"Backed up {users} users to {target} ({os.path.getsize(target)} bytes); removed {removed} old backup(s)")


if __name__ == "__main__":
    main()
