import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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

    # 'new' / 'old' - which Uzbek Latin alphabet this user wants results in
    # (see utils/uzbek_script.py). NULL = never chosen, callers use the default.
    if "uzbek_alphabet" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN uzbek_alphabet TEXT")

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

    # One row per user per day, incremented once per full pipeline run
    # (see handlers/link_handler.py's PER_USER_DAILY_LIMIT) - keeps a
    # single heavy user from burning through the whole bot's shared Groq
    # quota alone. usage_date is a plain 'YYYY-MM-DD' string (UTC, from
    # SQLite's own date('now')) rather than a datetime, since all that's
    # ever needed is "which calendar day" - never compared or sorted as
    # a real timestamp.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage (
            user_id INTEGER NOT NULL,
            usage_date TEXT NOT NULL,
            request_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, usage_date)
        )
    """)

    # One row per day, written once - marks that the owner has already
    # been sent today's "approaching Groq capacity" DM (see
    # GROQ_CAPACITY_WARNING_THRESHOLD in handlers/link_handler.py), so
    # that check doesn't re-fire on every request once the threshold is
    # crossed.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS capacity_alerts (
            alert_date TEXT PRIMARY KEY
        )
    """)

    # Per-day counters for the Gemini free-tier quotas (see
    # services/speech_service.py) - `day` is the GOOGLE quota day (Pacific
    # time, where Google's daily quotas reset), not UTC. Keys: cluster,
    # done:<tier>, id_calls, gemini_failed, quota_hit:<model>.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gemini_counters (
            day TEXT NOT NULL,
            key TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (day, key)
        )
    """)

    # Which owner alerts were already sent on which Google quota day, so
    # each fires once a day (same idea as capacity_alerts above).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS owner_alerts_sent (
            day TEXT NOT NULL,
            kind TEXT NOT NULL,
            PRIMARY KEY (day, kind)
        )
    """)

    # Results already produced for a public link, so the same video sent
    # again - by anyone - is served from memory instead of downloading and
    # transcribing again. `key` identifies the VIDEO (see
    # utils/link_detector.py's canonical_link_key). No user id is stored: this
    # is derived from a public link, not from a person. The audio is kept as
    # Telegram's own file_id (re-sent instantly, nothing stored here), the
    # transcript in the standard Latin spelling for Uzbek (re-rendered per user).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_cache (
            key TEXT PRIMARY KEY,
            title TEXT,
            audio_file_id TEXT,
            audio_cached_at TEXT,
            transcript TEXT,
            detected_language TEXT,
            transcript_cached_at TEXT
        )
    """)

    # Keyed by a hash of the source text (not the text itself - transcripts
    # can be long) plus the language pair, so an identical translation
    # request - a double-tap, a retry after a transient failure, or
    # reopening the same result from history - is served instantly instead
    # of spending another call against Google/MyMemory's shared free-tier
    # quota. No TTL/expiry: a translation of fixed source text doesn't go
    # stale, so there's nothing to invalidate.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translation_cache (
            text_hash TEXT NOT NULL,
            source_language TEXT NOT NULL,
            target_language TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (text_hash, source_language, target_language)
        )
    """)

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


def set_uzbek_alphabet(user_id, alphabet):
    """alphabet: 'new' or 'old'. Upsert for the same reason as set_interface_language."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (user_id, uzbek_alphabet)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET uzbek_alphabet = excluded.uzbek_alphabet
    """, (user_id, alphabet))

    connection.commit()
    connection.close()


def get_uzbek_alphabet(user_id):
    """Returns 'new' or 'old', or None if this user never chose (caller applies the default)."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT uzbek_alphabet FROM users WHERE user_id = ?", (user_id,))

    row = cursor.fetchone()
    connection.close()

    return row[0] if row and row[0] in ("new", "old") else None


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


def get_daily_usage_count(user_id):
    """Returns how many pipeline runs this user has started today (UTC), 0 if none yet."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT request_count FROM daily_usage
        WHERE user_id = ? AND usage_date = date('now')
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    return row[0] if row else 0


def increment_daily_usage(user_id):
    """
    Call once per pipeline run actually started (not per Groq call within
    it, and not for a run rejected by the cap check) - see
    PER_USER_DAILY_LIMIT in handlers/link_handler.py for where this is
    checked before a run begins.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO daily_usage (user_id, usage_date, request_count)
        VALUES (?, date('now'), 1)
        ON CONFLICT(user_id, usage_date) DO UPDATE SET
            request_count = request_count + 1
    """, (user_id,))

    connection.commit()
    connection.close()


def decrement_daily_usage(user_id):
    """Gives back one run (never below 0) - used when a run produced nothing
    (no speech detected), so the user isn't charged for it."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE daily_usage SET request_count = MAX(request_count - 1, 0)
        WHERE user_id = ? AND usage_date = date('now')
    """, (user_id,))

    connection.commit()
    connection.close()


GOOGLE_QUOTA_TZ = ZoneInfo("America/Los_Angeles")
OWNER_TZ = ZoneInfo("Asia/Tashkent")


def google_quota_day() -> str:
    return datetime.now(GOOGLE_QUOTA_TZ).strftime("%Y-%m-%d")


def next_quota_reset():
    """(timedelta until Google's daily quotas reset, that moment in Tashkent time)."""
    now = datetime.now(GOOGLE_QUOTA_TZ)
    reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return reset - now, reset.astimezone(OWNER_TZ)


def bump_counter(key, amount=1):
    connection = get_connection()
    connection.execute("""
        INSERT INTO gemini_counters (day, key, count) VALUES (?, ?, ?)
        ON CONFLICT(day, key) DO UPDATE SET count = count + excluded.count
    """, (google_quota_day(), key, amount))
    connection.commit()
    connection.close()


def get_counters(day=None) -> dict:
    connection = get_connection()
    rows = connection.execute(
        "SELECT key, count FROM gemini_counters WHERE day = ?", (day or google_quota_day(),)
    ).fetchall()
    connection.close()
    return dict(rows)


def owner_alert_already_sent(kind) -> bool:
    connection = get_connection()
    row = connection.execute(
        "SELECT 1 FROM owner_alerts_sent WHERE day = ? AND kind = ?", (google_quota_day(), kind)
    ).fetchone()
    connection.close()
    return row is not None


def mark_owner_alert_sent(kind):
    connection = get_connection()
    connection.execute(
        "INSERT OR IGNORE INTO owner_alerts_sent (day, kind) VALUES (?, ?)", (google_quota_day(), kind)
    )
    connection.commit()
    connection.close()


def get_stats_today() -> dict:
    """Bot-wide numbers for the owner's /stats (UTC day, like daily_usage)."""
    connection = get_connection()
    requests_today, active_users = connection.execute("""
        SELECT COALESCE(SUM(request_count), 0), COUNT(*) FROM daily_usage WHERE usage_date = date('now')
    """).fetchone()
    total_users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_transcripts = connection.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0]
    connection.close()
    return {
        "requests_today": requests_today, "active_users": active_users,
        "total_users": total_users, "total_transcripts": total_transcripts,
    }


# How long a saved result stays usable. Audio file_ids are long-lived; a
# transcript is kept shorter so a weak result (e.g. produced while the best
# models' daily quota was used up) doesn't stick forever.
LINK_AUDIO_TTL_DAYS = 60
LINK_TRANSCRIPT_TTL_DAYS = 14


def get_link_cache(key):
    """Saved result for this video, or None. Expired parts come back as None."""
    connection = get_connection()
    row = connection.execute("""
        SELECT title,
               CASE WHEN audio_cached_at >= datetime('now', ?) THEN audio_file_id END,
               CASE WHEN transcript_cached_at >= datetime('now', ?) THEN transcript END,
               detected_language
        FROM link_cache WHERE key = ?
    """, (f"-{LINK_AUDIO_TTL_DAYS} days", f"-{LINK_TRANSCRIPT_TTL_DAYS} days", key)).fetchone()
    connection.close()

    if not row or not (row[1] or row[2]):
        return None

    return {"title": row[0], "audio_file_id": row[1], "transcript": row[2], "detected_language": row[3]}


def save_link_audio(key, title, audio_file_id):
    connection = get_connection()
    connection.execute("""
        INSERT INTO link_cache (key, title, audio_file_id, audio_cached_at) VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(key) DO UPDATE SET title = excluded.title, audio_file_id = excluded.audio_file_id,
                                       audio_cached_at = excluded.audio_cached_at
    """, (key, title, audio_file_id))
    connection.commit()
    connection.close()


def save_link_transcript(key, transcript, detected_language, title=None):
    connection = get_connection()
    connection.execute("""
        INSERT INTO link_cache (key, title, transcript, detected_language, transcript_cached_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(key) DO UPDATE SET transcript = excluded.transcript,
                                       detected_language = excluded.detected_language,
                                       transcript_cached_at = excluded.transcript_cached_at,
                                       title = COALESCE(link_cache.title, excluded.title)
    """, (key, title, transcript, detected_language))
    connection.commit()
    connection.close()


def forget_link_audio(key):
    """Telegram no longer accepts the saved file_id - stop offering it."""
    connection = get_connection()
    connection.execute("UPDATE link_cache SET audio_file_id = NULL WHERE key = ?", (key,))
    connection.commit()
    connection.close()


def get_total_usage_today():
    """Sum of every user's pipeline runs today (UTC) - the number that
    actually matters against Groq's shared free-tier daily cap, unlike
    get_daily_usage_count() which is scoped to one user."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(request_count), 0) FROM daily_usage
        WHERE usage_date = date('now')
    """)

    total = cursor.fetchone()[0]
    connection.close()

    return total


def has_sent_capacity_alert_today():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT 1 FROM capacity_alerts WHERE alert_date = date('now')")
    row = cursor.fetchone()
    connection.close()

    return row is not None


def mark_capacity_alert_sent():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("INSERT OR IGNORE INTO capacity_alerts (alert_date) VALUES (date('now'))")

    connection.commit()
    connection.close()


def _hash_text(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_cached_translation(text, source_language, target_language):
    """Returns a previously-translated result for this exact (text, source,
    target) combination, or None if it's never been translated before -
    see translation_cache's comment in init_database() for why this exists."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT translated_text FROM translation_cache
        WHERE text_hash = ? AND source_language = ? AND target_language = ?
    """, (_hash_text(text), source_language, target_language))

    row = cursor.fetchone()
    connection.close()

    return row[0] if row else None


def cache_translation(text, source_language, target_language, translated_text):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO translation_cache (text_hash, source_language, target_language, translated_text)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(text_hash, source_language, target_language) DO UPDATE SET
            translated_text = excluded.translated_text
    """, (_hash_text(text), source_language, target_language, translated_text))

    connection.commit()
    connection.close()


def delete_user_data(user_id):
    """
    Permanently deletes everything this user_id is identifiable in - see
    /privacy (handlers/command_handler.py). Deliberately does NOT touch
    translation_cache: it's keyed only by a hash of the source text plus
    the language pair, with no user_id stored anywhere in that table, so
    there's nothing there to attribute back to this (or any) user.

    Removing the users row (not just clearing its fields) means the next
    /start looks exactly like a first-time user - the onboarding language
    picker runs again, which is the correct behavior after a full data
    deletion rather than a special-cased "deleted but still remembered"
    state.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM transcripts WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM daily_usage WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    connection.commit()
    connection.close()