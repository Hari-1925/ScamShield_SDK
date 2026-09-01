import sqlite3
import os
import json
from typing import List, Dict

class ContextEngine:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to a local db in the user's home or app data directory
            home = os.path.expanduser('~')
            db_dir = os.path.join(home, '.scamshield')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'history.db')
            
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Contacts Table
            c.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    contact_id TEXT PRIMARY KEY,
                    is_saved BOOLEAN DEFAULT 0,
                    msg_count INTEGER DEFAULT 0,
                    trust_score REAL DEFAULT 0.1
                )
            ''')
            # Messages Table for RAG
            c.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id TEXT,
                    sender TEXT,
                    text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(contact_id) REFERENCES contacts(contact_id)
                )
            ''')
            conn.commit()

    def log_message(self, contact_id: str, text: str, sender: str = 'them', is_saved: bool = False):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Upsert contact
            c.execute("SELECT msg_count, is_saved FROM contacts WHERE contact_id = ?", (contact_id,))
            row = c.fetchone()
            
            if row:
                new_count = row[0] + 1
                # If they were saved previously or saved now
                current_saved = is_saved or row[1]
                
                # Trust score logic:
                # If saved, max trust is 0.99. Reaches 0.99 after ~50 messages.
                # If unsaved, max trust is 0.4.
                if current_saved:
                    new_trust = min(0.99, 0.5 + (new_count / 100.0))
                else:
                    new_trust = min(0.4, 0.1 + (new_count / 200.0))
                    
                c.execute('''
                    UPDATE contacts 
                    SET msg_count = ?, trust_score = ?, is_saved = ?
                    WHERE contact_id = ?
                ''', (new_count, new_trust, current_saved, contact_id))
            else:
                initial_trust = 0.5 if is_saved else 0.1
                c.execute('''
                    INSERT INTO contacts (contact_id, is_saved, msg_count, trust_score)
                    VALUES (?, ?, 1, ?)
                ''', (contact_id, is_saved, initial_trust))

            # Insert message
            c.execute('''
                INSERT INTO messages (contact_id, sender, text)
                VALUES (?, ?, ?)
            ''', (contact_id, sender, text))
            conn.commit()

    def get_trust_score(self, contact_id: str) -> float:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT trust_score FROM contacts WHERE contact_id = ?", (contact_id,))
            row = c.fetchone()
            return row[0] if row else 0.1

    def get_recent_messages(self, contact_id: str, limit: int = 5) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT text FROM messages 
                WHERE contact_id = ? 
                ORDER BY id DESC 
                LIMIT ?
            ''', (contact_id, limit))
            return [row[0] for row in c.fetchall()]
            
    def set_saved_status(self, contact_id: str, is_saved: bool):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE contacts SET is_saved = ? WHERE contact_id = ?", (is_saved, contact_id))
            conn.commit()

# Testing
if __name__ == "__main__":
    ce = ContextEngine(":memory:")
    ce.log_message("dad123", "hey son", sender="them", is_saved=True)
    ce.log_message("dad123", "what is the netflix otp?", sender="them", is_saved=True)
    print("Trust:", ce.get_trust_score("dad123"))
    print("History:", ce.get_recent_messages("dad123"))

