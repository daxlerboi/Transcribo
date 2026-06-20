import os
import json
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "")
DB_PATH = os.path.join(os.path.dirname(__file__), "data.json")

class DB:
    def __init__(self):
        self._data = {"users": []}
        self._load()

    def _load(self):
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {"users": []}

    def _save(self):
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, default=str)

    def find_one(self, collection: str, query: dict) -> dict | None:
        if collection not in self._data:
            return None
        for doc in self._data[collection]:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    def insert_one(self, collection: str, doc: dict) -> dict:
        if collection not in self._data:
            self._data[collection] = []
        doc["_id"] = str(uuid.uuid4())
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        self._data[collection].append(doc)
        self._save()
        return doc

    def update_one(self, collection: str, query: dict, update: dict) -> bool:
        if collection not in self._data:
            return False
        for doc in self._data[collection]:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update)
                self._save()
                return True
        return False

    def delete_one(self, collection: str, query: dict) -> bool:
        if collection not in self._data:
            return False
        before = len(self._data[collection])
        self._data[collection] = [
            d for d in self._data[collection]
            if not all(d.get(k) == v for k, v in query.items())
        ]
        if len(self._data[collection]) < before:
            self._save()
            return True
        return False

db = DB()
