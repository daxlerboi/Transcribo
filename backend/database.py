import os
import json
import sqlite3
import uuid
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

USE_MONGODB = os.getenv("MONGODB_URL", "")
USE_SQLITE = os.getenv("USE_SQLITE", "0") == "1"
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

if USE_MONGODB and not USE_SQLITE:
    from pymongo import MongoClient

    _client = MongoClient(USE_MONGODB, serverSelectionTimeoutMS=10000)
    _db = _client["transcribo"]

    async def find_one(collection: str, query: dict) -> dict | None:
        doc = await asyncio.to_thread(_db[collection].find_one, query)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def insert_one(collection: str, doc: dict) -> dict:
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        result = await asyncio.to_thread(_db[collection].insert_one, doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def update_one(collection: str, query: dict, update: dict) -> bool:
        result = await asyncio.to_thread(_db[collection].update_one, query, {"$set": update})
        return result.modified_count > 0

    async def delete_one(collection: str, query: dict) -> bool:
        result = await asyncio.to_thread(_db[collection].delete_one, query)
        return result.deleted_count > 0

else:
    def _get_conn():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db():
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                _id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                tokens_blacklisted TEXT DEFAULT '[]',
                created_at TEXT DEFAULT ''
            )
        """)
        conn.commit()
        conn.close()

    _init_db()

    def _row_to_dict(row) -> dict:
        d = dict(row)
        d["_id"] = d.pop("id")
        return d

    async def find_one(collection: str, query: dict) -> dict | None:
        if collection != "users":
            return None
        await asyncio.to_thread(_init_db)
        conn = _get_conn()
        conditions = " AND ".join(f"{k} = ?" for k in query)
        params = list(query.values())
        cur = conn.execute(f"SELECT * FROM users WHERE {conditions}", params)
        row = cur.fetchone()
        conn.close()
        return _row_to_dict(row) if row else None

    async def insert_one(collection: str, doc: dict) -> dict:
        if collection != "users":
            raise ValueError("Only users collection supported in SQLite mode")
        await asyncio.to_thread(_init_db)
        doc = dict(doc)
        doc.setdefault("_id", str(uuid.uuid4()))
        doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        doc.setdefault("tokens_blacklisted", json.dumps([]))
        if isinstance(doc.get("tokens_blacklisted"), list):
            doc["tokens_blacklisted"] = json.dumps(doc["tokens_blacklisted"])
        conn = _get_conn()
        conn.execute(
            "INSERT INTO users (_id, email, password, tokens_blacklisted, created_at) VALUES (?,?,?,?,?)",
            (doc["_id"], doc["email"], doc["password"], doc["tokens_blacklisted"], doc["created_at"]),
        )
        conn.commit()
        conn.close()
        return doc

    async def update_one(collection: str, query: dict, update: dict) -> bool:
        if collection != "users":
            return False
        await asyncio.to_thread(_init_db)
        set_clause = ", ".join(f"{k} = ?" for k in update)
        params = list(update.values())
        where_keys = list(query.keys())
        where_vals = list(query.values())
        conditions = " AND ".join(f"{k} = ?" for k in query)
        conn = _get_conn()
        cur = conn.execute(
            f"UPDATE users SET {set_clause} WHERE {conditions}",
            params + where_vals,
        )
        changed = cur.rowcount > 0
        conn.commit()
        conn.close()
        return changed

    async def delete_one(collection: str, query: dict) -> bool:
        if collection != "users":
            return False
        await asyncio.to_thread(_init_db)
        conditions = " AND ".join(f"{k} = ?" for k in query)
        params = list(query.values())
        conn = _get_conn()
        cur = conn.execute(f"DELETE FROM users WHERE {conditions}", params)
        changed = cur.rowcount > 0
        conn.commit()
        conn.close()
        return changed
