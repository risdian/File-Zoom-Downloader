# db/database.py

import sqlite3
from models.user import User  # Import the User model

def get_db_connection():
    return sqlite3.connect('app_data.db')

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS app_config 
                    (id INTEGER PRIMARY KEY,
                     key TEXT UNIQUE,
                     prefix TEXT,
                     value TEXT)''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            display_name TEXT,
            type INTEGER,
            timezone TEXT,
            verified INTEGER,
            created_at TEXT,
            last_login_time TEXT,
            status TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS download_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            recording_id TEXT,
            meeting_id TEXT,
            file_name TEXT,
            download_url TEXT,
            download_date TEXT,
            status TEXT
        )
    ''')
    # Modify users table to include a 'deleted' column
    try:
        conn.execute('ALTER TABLE users ADD COLUMN deleted BOOLEAN DEFAULT FALSE')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists, so we can safely ignore this error
    conn.commit()
    conn.close()

def upsert_config_item(key, value, prefix=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO app_config (key, prefix, value)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, prefix = excluded.prefix
    ''', (key, prefix, value))
    conn.commit()
    conn.close()

def get_config_item(key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM app_config WHERE key = ?', (key,))
    item = cursor.fetchone()
    conn.close()
    return item[0] if item else None

def delete_config_item(key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM app_config WHERE key = ?', (key,))
    conn.commit()
    conn.close()


def upsert_user(user_data):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (id, first_name, last_name, display_name, email, type, timezone, verified, created_at, last_login_time, status, deleted)
            VALUES (:id, :first_name, :last_name, :display_name, :email, :type, :timezone, :verified, :created_at, :last_login_time, :status, FALSE)
            ON CONFLICT(id) DO UPDATE SET
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                display_name=excluded.last_name,
                email=excluded.email,
                type=excluded.type,
                timezone=excluded.timezone,
                verified=excluded.verified,
                created_at=excluded.created_at,
                last_login_time=excluded.last_login_time,
                status=excluded.status,
                deleted = FALSE

        ''', user_data)
        conn.commit()

def get_all_users():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            user_rows = cursor.fetchall()
            return [User(*row) for row in user_rows]  # Create a User instance for each row
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []  # Return an empty list in case of an error
    
def delete_all_users():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()

def mark_users_as_deleted():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET deleted = TRUE")
        conn.commit()

def record_download(user_id, recording_id, meeting_id, file_name, download_url, status):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO download_history (user_id, recording_id, meeting_id, file_name, download_url, status, download_date)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (user_id, recording_id, meeting_id, file_name, download_url, status))
        conn.commit()

def get_download_history():
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM download_history')
            downloads = cursor.fetchall()
            return downloads
        except Exception as e:
            print(f"Error fetching download history: {e}")
            return []


def update_download_record(recording_id, status):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE download_history 
            SET status = ?, download_date = datetime('now') 
            WHERE recording_id = ?
        ''', (status, recording_id))
        conn.commit()


def is_already_downloaded(recording_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM download_history WHERE recording_id = ?", (recording_id,))
        return cursor.fetchone() is not None


def record_or_update_download_status(user_id, recording_id, meeting_id, file_name, download_url, status):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if the record exists
        cursor.execute("SELECT id FROM download_history WHERE recording_id = ?", (recording_id,))
        record = cursor.fetchone()

        if record is None:
            # Insert new record
            cursor.execute('''
                INSERT INTO download_history (user_id, recording_id, meeting_id, file_name, download_url, status, download_date)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (user_id, recording_id, meeting_id, file_name, download_url, status))
        else:
            # Update existing record
            cursor.execute('''
                UPDATE download_history 
                SET status = ?, download_date = datetime('now') 
                WHERE recording_id = ?
            ''', (status, recording_id))
        conn.commit()


def check_download_status(recording_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Correctly format the tuple with a single element
        cursor.execute("SELECT * FROM download_history WHERE recording_id = ?", (recording_id,))
        return cursor.fetchone() is not None