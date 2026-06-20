import os
import json
import uuid
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "")
DB_PATH = os.path.join(os.path.dirname(__file__), "data.json")

if MONGODB_URL:
    from pymongo import MongoClient

    # Append TLS 1.2 params for Python 3.14+ compatibility with Atlas
    tls_url = MONGODB_URL
    if "tls=" not in tls_url:
        sep = "&" if "?" in tls_url else "?"
        tls_url += f"{sep}tls=true&tlsAllowInvalidCertificates=true"
    _client = MongoClient(tls_url, serverSelectionTimeoutMS=5000)
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
    _data: dict = {"users": []}

    def _load():
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {"users": []}
        return {"users": []}

    def _save():
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(_data, f, indent=2, default=str)

    _data = _load()

    async def find_one(collection: str, query: dict) -> dict | None:
        if collection not in _data:
            return None
        for doc in _data[collection]:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    async def insert_one(collection: str, doc: dict) -> dict:
        if collection not in _data:
            _data[collection] = []
        doc["_id"] = str(uuid.uuid4())
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        _data[collection].append(doc)
        _save()
        return doc

    async def update_one(collection: str, query: dict, update: dict) -> bool:
        if collection not in _data:
            return False
        for doc in _data[collection]:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update)
                _save()
                return True
        return False

    async def delete_one(collection: str, query: dict) -> bool:
        if collection not in _data:
            return False
        before = len(_data[collection])
        _data[collection] = [
            d for d in _data[collection]
            if not all(d.get(k) == v for k, v in query.items())
        ]
        if len(_data[collection]) < before:
            _save()
            return True
        return False
