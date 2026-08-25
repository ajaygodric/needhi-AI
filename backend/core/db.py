import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from core.config import DATABASE_FILE, STATIC_DATA_DIR

logger = logging.getLogger("needhi.db")

_db_initialized = False

def init_db():
    global _db_initialized
    if _db_initialized:
        return
        
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        
        # Create cases table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            cnr TEXT PRIMARY KEY,
            case_no TEXT NOT NULL,
            title TEXT NOT NULL,
            petitioner TEXT NOT NULL,
            respondent TEXT NOT NULL,
            petitioner_adv TEXT,
            respondent_adv TEXT,
            raw_json TEXT NOT NULL
        )
        """)
        
        # Create lawyers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lawyers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            city TEXT NOT NULL,
            raw_json TEXT NOT NULL
        )
        """)
        
        # Create bookings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lawyer_id TEXT NOT NULL,
            lawyer_name TEXT NOT NULL,
            lawyer_specialty TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_slot TEXT NOT NULL,
            client_name TEXT NOT NULL,
            client_email TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            client_grievance TEXT NOT NULL,
            booking_code TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)
        
        # Create subscriptions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnr TEXT NOT NULL,
            email TEXT NOT NULL,
            client_name TEXT NOT NULL,
            language TEXT NOT NULL,
            verification_token TEXT,
            verified INTEGER NOT NULL,
            subscribed_at TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)
        
        # Create rate_limits table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            ip TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits ON rate_limits (ip, endpoint, timestamp)")
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """)
        
        # Create sessions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Create search_history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            timestamp REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        
        # Migration from cases.json
        cursor.execute("SELECT COUNT(*) FROM cases")
        if cursor.fetchone()[0] == 0:
            cases_path = os.path.join(STATIC_DATA_DIR, "cases.json")
            if os.path.exists(cases_path):
                with open(cases_path, "r", encoding="utf-8") as f:
                    cases = json.load(f)
                    for c in cases:
                        cursor.execute("""
                        INSERT OR REPLACE INTO cases (cnr, case_no, title, petitioner, respondent, petitioner_adv, respondent_adv, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            c["cnr"], c.get("case_no", ""), c["title"], c.get("petitioner", ""), c.get("respondent", ""),
                            c.get("petitioner_adv", ""), c.get("respondent_adv", ""), json.dumps(c, ensure_ascii=False)
                        ))
                logger.info("Migrated cases.json to SQLite database successfully.")
                     
        # Migration from lawyers.json
        cursor.execute("SELECT COUNT(*) FROM lawyers")
        if cursor.fetchone()[0] == 0:
            lawyers_path = os.path.join(STATIC_DATA_DIR, "lawyers.json")
            if os.path.exists(lawyers_path):
                with open(lawyers_path, "r", encoding="utf-8") as f:
                    lawyers = json.load(f)
                    for l in lawyers:
                        cursor.execute("""
                        INSERT OR REPLACE INTO lawyers (id, name, specialization, city, raw_json)
                        VALUES (?, ?, ?, ?, ?)
                        """, (
                            l["id"], l["name"], l["specialization"], l.get("city", l.get("location", "Chennai")),
                            json.dumps(l, ensure_ascii=False)
                        ))
                logger.info("Migrated lawyers.json to SQLite database successfully.")
                     
        # Migration from bookings.json
        cursor.execute("SELECT COUNT(*) FROM bookings")
        if cursor.fetchone()[0] == 0:
            bookings_path = os.path.join(STATIC_DATA_DIR, "bookings.json")
            if os.path.exists(bookings_path):
                with open(bookings_path, "r", encoding="utf-8") as f:
                    bookings = json.load(f)
                    for b in bookings:
                        cursor.execute("""
                        INSERT INTO bookings (lawyer_id, lawyer_name, lawyer_specialty, booking_date, booking_slot, client_name, client_email, client_phone, client_grievance, booking_code, status, created_at, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(b["lawyer_id"]), b["lawyer_name"], b["specialization"], b["date"], b["slot"],
                            b["client_name"], b["client_email"], b["client_phone"], b.get("details", ""),
                            b.get("code", "ND-DEF"), b.get("status", "Confirmed"),
                            b.get("timestamp", datetime.now().isoformat()), b.get("timestamp", datetime.now().isoformat())
                        ))
                logger.info("Migrated bookings.json to SQLite database successfully.")
                     
        # Migration from subscriptions.json
        cursor.execute("SELECT COUNT(*) FROM subscriptions")
        if cursor.fetchone()[0] == 0:
            subscriptions_path = os.path.join(STATIC_DATA_DIR, "subscriptions.json")
            if os.path.exists(subscriptions_path):
                with open(subscriptions_path, "r", encoding="utf-8") as f:
                    subs = json.load(f)
                    for s in subs:
                        cursor.execute("""
                        INSERT INTO subscriptions (cnr, email, client_name, language, verification_token, verified, subscribed_at, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            s["cnr"], s["email"], s["client_name"], s["language"], s.get("verification_token"),
                            1 if s.get("verified", True) else 0,
                            s.get("subscribed_at", datetime.now().isoformat()), s.get("timestamp", datetime.now().isoformat())
                        ))
                logger.info("Migrated subscriptions.json to SQLite database successfully.")
                     
        conn.commit()
        _db_initialized = True
    except Exception as e:
        conn.rollback()
        logger.exception("Database initialization failed. Rolled back all changes.")
        raise e
    finally:
        conn.close()

def purge_old_records_db(days: int = 90):
    """Delete database records older than `days` days."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM bookings WHERE timestamp < ?", (cutoff,))
        purged_bookings = cursor.rowcount
        
        cursor.execute("DELETE FROM subscriptions WHERE timestamp < ?", (cutoff,))
        purged_subscriptions = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if purged_bookings > 0 or purged_subscriptions > 0:
            logger.info(f"Purged {purged_bookings} old bookings and {purged_subscriptions} old subscriptions from SQLite database.")
    except Exception as e:
        logger.error(f"Failed to purge old records from SQLite: {e}")

def search_knowledge_base(query_text: str, limit: int = 5) -> list:
    import re
    cleaned_query = re.sub(r'[^\w\s]', ' ', query_text).strip()
    if not cleaned_query:
        return []
    
    words = [w for w in cleaned_query.split() if len(w) > 2]
    if not words:
        words = [w for w in cleaned_query.split() if len(w) > 0]
        if not words:
            return []
    
    search_expr = " OR ".join(words)
    
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.act_name, c.page_number, c.content
            FROM knowledge_base_search s
            JOIN knowledge_base_chunks c ON s.chunk_id = c.id
            WHERE s.content MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (search_expr, limit))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "act_name": row[0],
                "page_number": row[1],
                "content": row[2]
            })
        return results
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return []
    finally:
        conn.close()
