import sqlite3
from pathlib import Path

class Database:
    def __init__(self, owner_id):
        base_dir = Path(__file__).resolve().parent.parent
        db_path = base_dir/"sakiko.db"
        self.conn = sqlite3.connect(str(db_path),check_same_thread = False)
        self._init_tables()
        self.owner_id = str(owner_id)

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS noble (
                uid TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                granted_by TEXT NOT NULL,
                granted_at TEXT NOT NULL)
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                content TEXT NOT NULL,
                link TEXT,
                created_at TEXT NOT NULL)
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS affection(
                uid TEXT PRIMARY KEY,
                rating INT NOT NULL CHECK(rating >= -100 AND rating <= 100)
            )
        """)
        self.conn.commit()
        pass

    def get_noble(self, uid:str) -> str | None:
        row = self.conn.execute("SELECT title FROM noble WHERE uid = ?", (str(uid),)).fetchone()
        return row[0] if row else None
    def get_latest_archive(self, uid:str)-> tuple[str, str | None] | None:
        row = self.conn.execute(
                "SELECT content, link FROM archive WHERE uid = ? ORDER BY id DESC LIMIT 1", (str(uid),)).fetchone()
        return row if row else None
    def add_noble(self, uid:str, title:str, granted_by:str, granted_at:str):
        try:
            self.conn.execute("INSERT OR REPLACE INTO noble(uid, title, granted_by, granted_at) VALUES (?,?,?,?)",(str(uid), title, str(granted_by), granted_at))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database Add Noble Error. {e}")
            self.conn.rollback()
            return False
    def add_archive(self, uid: str, content: str, link: str | None, created_at: str) -> int | None:
        try:
            cursor = self.conn.execute("INSERT INTO archive (uid, content, link, created_at) VALUES (?,?,?,?)",(str(uid), content, link, created_at))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Database Archive Error. {e}")
            self.conn.rollback()
            return None
    def affection_lookup_or_init(self, uid: str)-> int | None:
        if uid == self.owner_id:
            return 100
        try:
            rating = self.conn.execute("SELECT rating FROM affection WHERE uid = ?", (str(uid),)).fetchone()
            if rating is None:
                cursor = self.conn.execute("INSERT OR IGNORE INTO affection (uid, rating) VALUES (?,?)", (str(uid), 0))
                self.conn.commit()
                return 0
            else:
                return rating[0]
        except Exception as e:
            print(f"Database Affection Error. {e}")
            self.conn.rollback()
            return None
            
    def change_affection_rating(self, uid: str, num: int) -> bool:
        try:
            self.affection_lookup_or_init(uid)
            self.conn.execute("UPDATE affection SET rating = MAX(-100, MIN(100, rating + ?)) WHERE uid = ?", (num, uid))
            self.conn.commit()
            print(f"对{uid}的好感度改变了{num}!")
            return True
        except Exception as e:
            print(f"UPDATE Database Affection Error. {e}")
            self.conn.rollback()
            return False
    