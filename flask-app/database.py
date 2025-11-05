"""
Database module for ChemoPAD Annotation Matcher
Uses SQLite for reliable concurrent access and data persistence
"""

import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

def get_db_path():
    """Get the database file path"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(base_dir, 'database')

    # Create database directory if it doesn't exist
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    return os.path.join(db_dir, 'chemopad.db')

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(get_db_path(), timeout=30.0)  # 30 second timeout for locks
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging for better concurrency
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database tables"""
    with get_db() as conn:
        # Create matches table with annot_id as primary key
        conn.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                annot_id INTEGER PRIMARY KEY,
                card_id TEXT NOT NULL,
                api_name TEXT,
                pad_num INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create notes table with annot_id as primary key
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                annot_id INTEGER PRIMARY KEY,
                note_text TEXT NOT NULL,
                api_name TEXT,
                pad_num INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for better performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_matches_api_pad ON matches(api_name, pad_num)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_notes_api_pad ON notes(api_name, pad_num)')

        # Create backup table for recovery
        conn.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_type TEXT NOT NULL,
                backup_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        logger.info("Database initialized successfully")

def save_match(annot_id, card_id, api_name=None, pad_num=None):
    """Save a match to the database"""
    with get_db() as conn:
        if card_id is None:
            # Delete the match
            conn.execute('DELETE FROM matches WHERE annot_id = ?', (annot_id,))
        else:
            # Insert or update the match
            conn.execute('''
                INSERT OR REPLACE INTO matches (annot_id, card_id, api_name, pad_num, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (annot_id, str(card_id), api_name, pad_num))

        conn.commit()
        logger.info(f"Saved match: annot_id={annot_id}, card_id={card_id}")

def save_note(annot_id, note_text, api_name=None, pad_num=None):
    """Save a note to the database"""
    with get_db() as conn:
        if not note_text:
            # Delete the note if empty
            conn.execute('DELETE FROM notes WHERE annot_id = ?', (annot_id,))
        else:
            # Insert or update the note
            conn.execute('''
                INSERT OR REPLACE INTO notes (annot_id, note_text, api_name, pad_num, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (annot_id, note_text, api_name, pad_num))

        conn.commit()
        logger.info(f"Saved note: annot_id={annot_id}")

def get_all_matches():
    """Get all matches as a dictionary"""
    matches = {}
    with get_db() as conn:
        cursor = conn.execute('SELECT annot_id, card_id FROM matches')
        for row in cursor:
            # Keep "no_match" as string, convert others to int if possible
            card_id = row['card_id']
            if card_id != "no_match":
                try:
                    card_id = int(card_id)
                except (ValueError, TypeError):
                    pass
            matches[row['annot_id']] = card_id

    return matches

def get_all_notes():
    """Get all notes as a dictionary"""
    notes = {}
    with get_db() as conn:
        cursor = conn.execute('SELECT annot_id, note_text FROM notes')
        for row in cursor:
            notes[row['annot_id']] = row['note_text']

    return notes

def migrate_from_json():
    """Migrate existing JSON data to database"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    session_dir = os.path.join(base_dir, 'session')

    migrated = False

    # Migrate matches
    matches_file = os.path.join(session_dir, 'matches.json')
    if os.path.exists(matches_file):
        logger.info(f"Migrating matches from {matches_file}")
        try:
            with open(matches_file, 'r') as f:
                matches = json.load(f)

            with get_db() as conn:
                for row_id, card_id in matches.items():
                    conn.execute('''
                        INSERT OR REPLACE INTO matches (row_id, card_id)
                        VALUES (?, ?)
                    ''', (int(row_id), str(card_id)))

                conn.commit()

            # Rename old file to .migrated
            os.rename(matches_file, matches_file + '.migrated')
            logger.info(f"Migrated {len(matches)} matches successfully")
            migrated = True
        except Exception as e:
            logger.error(f"Failed to migrate matches: {e}")

    # Migrate notes
    notes_file = os.path.join(session_dir, 'notes.json')
    if os.path.exists(notes_file):
        logger.info(f"Migrating notes from {notes_file}")
        try:
            with open(notes_file, 'r') as f:
                notes = json.load(f)

            with get_db() as conn:
                for row_id, note_text in notes.items():
                    conn.execute('''
                        INSERT OR REPLACE INTO notes (row_id, note_text)
                        VALUES (?, ?)
                    ''', (int(row_id), note_text))

                conn.commit()

            # Rename old file to .migrated
            os.rename(notes_file, notes_file + '.migrated')
            logger.info(f"Migrated {len(notes)} notes successfully")
            migrated = True
        except Exception as e:
            logger.error(f"Failed to migrate notes: {e}")

    return migrated

def backup_database():
    """Create a backup of current data"""
    matches = get_all_matches()
    notes = get_all_notes()

    backup_data = {
        'matches': matches,
        'notes': notes,
        'timestamp': datetime.now().isoformat()
    }

    with get_db() as conn:
        conn.execute('''
            INSERT INTO backups (backup_type, backup_data)
            VALUES ('automatic', ?)
        ''', (json.dumps(backup_data),))

        # Keep only last 10 backups
        conn.execute('''
            DELETE FROM backups
            WHERE id NOT IN (
                SELECT id FROM backups
                ORDER BY created_at DESC
                LIMIT 10
            )
        ''')

        conn.commit()

    logger.info("Database backup created")

def get_stats():
    """Get database statistics"""
    with get_db() as conn:
        match_count = conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0]
        note_count = conn.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
        backup_count = conn.execute('SELECT COUNT(*) FROM backups').fetchone()[0]

        return {
            'total_matches': match_count,
            'total_notes': note_count,
            'total_backups': backup_count
        }

# Initialize database when module is imported
init_db()

# Try to migrate existing JSON data
if migrate_from_json():
    logger.info("Successfully migrated existing data to database")
    backup_database()  # Create initial backup after migration