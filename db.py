import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'noticeboard.db')
ADMIN_EMAIL_DOMAIN = '.edu.in'
ADMIN_EMAIL_ERROR_MESSAGE = 'Admin registration requires a valid institutional email ending with .edu.in'

def get_db_connection():
    """Establishes a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_valid_institutional_email(email):
    """Returns True when an email ends with the institutional .edu.in suffix."""
    return bool(email and email.strip().lower().endswith(ADMIN_EMAIL_DOMAIN))


def _ensure_users_email_column(cursor):
    """Adds the users.email column when upgrading an older database schema."""
    cursor.execute('PRAGMA table_info(users)')
    columns = [row[1] for row in cursor.fetchall()]
    if 'email' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')

def init_db():
    """Initializes the database tables if they do not exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'student')),
            email TEXT,
            branch TEXT DEFAULT 'All',
            year TEXT DEFAULT 'All',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    _ensure_users_email_column(cursor)
    
    # Create Notices Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT,
            category TEXT NOT NULL CHECK(category IN ('Exams', 'Placements', 'Events', 'Assignments', 'Workshops', 'General')),
            branch TEXT NOT NULL DEFAULT 'All',
            year TEXT NOT NULL DEFAULT 'All',
            priority TEXT NOT NULL CHECK(priority IN ('High', 'Medium', 'Low')) DEFAULT 'Medium',
            deadlines TEXT,  -- comma-separated strings of detected dates
            file_path TEXT,  -- path to uploaded document/image
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''');
    
    conn.commit()
    conn.close()
    print("Database tables initialized successfully.")

# --- User Management Functions ---

def register_user(username, password, role, branch='All', year='All', email=None):
    """Registers a new user in the system with a hashed password."""
    normalized_role = (role or '').lower()
    normalized_email = (email or '').strip() if email else None

    if normalized_role == 'admin' and not is_valid_institutional_email(normalized_email):
        return {"success": False, "message": ADMIN_EMAIL_ERROR_MESSAGE}

    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_pwd = generate_password_hash(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password, role, email, branch, year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hashed_pwd, normalized_role, normalized_email, branch, year))
        conn.commit()
        user_id = cursor.lastrowid
        return {"success": True, "user_id": user_id, "message": "Registration successful."}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username already exists."}
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticates a user against stored hashed password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        return {
            "success": True,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role'],
                "email": user['email'],
                "branch": user['branch'],
                "year": user['year']
            }
        }
    return {"success": False, "message": "Invalid username or password."}

# --- Notice Management Functions ---

def add_notice(title, content, summary, category, branch='All', year='All', priority='Medium', deadlines=None, file_path=None):
    """Inserts a new notice into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO notices (title, content, summary, category, branch, year, priority, deadlines, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, content, summary, category, branch, year, priority, deadlines, file_path))
        conn.commit()
        notice_id = cursor.lastrowid
        return {"success": True, "notice_id": notice_id, "message": "Notice added successfully."}
    except Exception as e:
        return {"success": False, "message": f"Error adding notice: {str(e)}"}
    finally:
        conn.close()

def delete_notice(notice_id):
    """Deletes a notice by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First retrieve file_path to delete the actual file if present
        cursor.execute('SELECT file_path FROM notices WHERE id = ?', (notice_id,))
        row = cursor.fetchone()
        if row and row['file_path']:
            # Safe delete of the file on disk
            try:
                if os.path.exists(row['file_path']):
                    os.remove(row['file_path'])
            except Exception as fe:
                print(f"Error removing file {row['file_path']}: {fe}")
                
        cursor.execute('DELETE FROM notices WHERE id = ?', (notice_id,))
        conn.commit()
        return {"success": True, "message": "Notice deleted successfully."}
    except Exception as e:
        return {"success": False, "message": f"Error deleting notice: {str(e)}"}
    finally:
        conn.close()

def get_notices(branch=None, year=None, category=None, priority=None, search_query=None):
    """Fetches notices based on filtering criteria."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM notices WHERE 1=1"
    params = []
    
    # Standard filtering logic
    if branch and branch != 'All':
        query += " AND (branch = ? OR branch = 'All')"
        params.append(branch)
    if year and year != 'All':
        query += " AND (year = ? OR year = 'All')"
        params.append(year)
    if category and category != 'All':
        query += " AND category = ?"
        params.append(category)
    if priority and priority != 'All':
        query += " AND priority = ?"
        params.append(priority)
        
    if search_query:
        query += " AND (title LIKE ? OR content LIKE ? OR category LIKE ?)"
        search_wildcard = f"%{search_query}%"
        params.extend([search_wildcard, search_wildcard, search_wildcard])
        
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convert list of Rows into dicts
    notices = []
    for r in rows:
        notices.append(dict(r))
        
    conn.close()
    return notices

def get_notice_by_id(notice_id):
    """Fetches a single notice by its database ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM notices WHERE id = ?', (notice_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None
