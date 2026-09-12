import sqlite3

DATABASE_NAME = "bot.db"


def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            interface_language TEXT
        )
    """)

    # Migration for databases created before interface_language existed -
    # CREATE TABLE IF NOT EXISTS above only affects brand new databases.
    # NULL means "never chosen" - callers default to English and prompt via
    # /language rather than guessing from Telegram's own language_code.
    user_columns = [row[1] for row in cursor.execute("PRAGMA table_info(users)")]
    if "interface_language" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN interface_language TEXT")

    # Stores the cleaned transcript only - not the raw ASR output (only
    # useful for live debugging, not history) and not translations (cheap
    # to regenerate on demand via the re-translate flow, would otherwise
    # bloat storage with one row per language per transcript).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            detected_language TEXT,
            title TEXT,
            transcript TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transcripts_user_id
        ON transcripts(user_id)
    """)

    # Migration for databases created before the title column existed -
    # CREATE TABLE IF NOT EXISTS above only affects brand new databases.
    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(transcripts)")]
    if "title" not in existing_columns:
        cursor.execute("ALTER TABLE transcripts ADD COLUMN title TEXT")

    connection.commit()
    connection.close()


def add_user(user_id, username, first_name):
    connection = get_connection()
    cursor = connection.cursor()

    # Upsert rather than INSERT OR REPLACE - REPLACE deletes and reinserts
    # the whole row, which would silently wipe interface_language back to
    # NULL every time an existing user runs /start again.
    cursor.execute("""
        INSERT INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
    """, (user_id, username, first_name))

    connection.commit()
    connection.close()


def set_interface_language(user_id, language_code):
    connection = get_connection()
    cursor = connection.cursor()

    # Upsert rather than a bare UPDATE - a plain UPDATE silently affects
    # zero rows (no error) if this user's very first interaction is
    # /language rather than /start, since add_user would never have run.
    cursor.execute("""
        INSERT INTO users (user_id, interface_language)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET interface_language = excluded.interface_language
    """, (user_id, language_code))

    connection.commit()
    connection.close()


def get_interface_language(user_id):
    """Returns the saved language code, or None if never chosen (caller should default to English)."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT interface_language FROM users WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    return row[0] if row else None


def add_transcript(user_id, platform, detected_language, title, transcript):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transcripts (user_id, platform, detected_language, title, transcript)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, platform, detected_language, title, transcript))

    connection.commit()
    transcript_id = cursor.lastrowid
    connection.close()

    return transcript_id


def get_transcripts_for_user(user_id, limit=10):
    connection = get_connection()
    cursor = connection.cursor()

    # created_at has only second-level resolution, so two transcripts saved
    # within the same second would otherwise tie - break ties with id DESC
    # (insertion order) so "newest first" is always correct, not arbitrary.
    cursor.execute("""
        SELECT id, platform, detected_language, title, transcript, created_at
        FROM transcripts
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()
    connection.close()

    return rows


def get_transcript_by_id(transcript_id, user_id):
    """
    Fetch one transcript, scoped to user_id so a user can never retrieve
    another user's transcript via a crafted/replayed callback.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, platform, detected_language, title, transcript, created_at
        FROM transcripts
        WHERE id = ? AND user_id = ?
    """, (transcript_id, user_id))

    row = cursor.fetchone()
    connection.close()

    return row