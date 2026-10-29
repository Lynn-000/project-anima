import sqlite3
from pathlib import Path
import sqlite_vec
from sqlite_vec import serialize_float32
import ollama
import asyncio

class Database:
    def __init__(self, owner_id):
        base_dir = Path(__file__).resolve().parent.parent
        db_path = base_dir/"sakiko.db"
        self.conn = sqlite3.connect(str(db_path),check_same_thread = False)

        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self.embed_client = ollama.Client(host="http://localhost:11434")
        self.embed_model = "nomic-embed-text"

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
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS archive_vectors USING vec0(
                embedding float[768]
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
    async def add_archive(self, uid: str, content: str, vector_text: str, link: str | None, created_at: str) -> int | None:
        try:

            cursor = self.conn.execute("INSERT INTO archive (uid, content, link, created_at) VALUES (?,?,?,?)",(str(uid), content, link, created_at))
            archive_id = cursor.lastrowid
            
            response = await asyncio.to_thread(
                self.embed_client.embed,
                model=self.embed_model,
                input=vector_text
            )
            vector = response['embeddings'][0]
            self.conn.execute(
                "INSERT INTO archive_vectors (rowid, embedding) VALUES (?, ?)",
                (archive_id, serialize_float32(vector))
            )
            
            self.conn.commit()
            return archive_id
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

    async def search_relevant_archive(self, uid: str, current_text: str) -> str | None:
        try:
            response = await asyncio.to_thread(
                self.embed_client.embed, 
                model=self.embed_model, 
                input=current_text
            )
            query_vector = response['embeddings'][0]
            result = self.conn.execute("""
                SELECT a.content, v.distance
                FROM (
                    SELECT rowid, distance
                    FROM archive_vectors
                    WHERE embedding MATCH ? AND k = 100 
                ) v
                JOIN archive a ON v.rowid = a.id
                WHERE a.uid = ?
                ORDER BY v.distance
            """, (serialize_float32(query_vector), str(uid))).fetchone()
            if result:
                print(f"[DEBUG] 向量搜索匹配到: '{result[0]}', 距离: {result[1]:.4f}")
            return result[0] if result else None
        except Exception as e:
            print(f"Vector Search Error: {e}")
            return None
    