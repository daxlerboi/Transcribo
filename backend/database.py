import os
import json
import uuid
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

def _read():
    if not os.path.exists(DATA_FILE):
        return {"users": []}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def _write(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

async def find_many(collection: str, query: dict, sort_by: str | None = None, reverse: bool = True) -> list[dict]:
    data = await asyncio.to_thread(_read)
    items = data.get(collection, [])
    result = [
        item for item in items
        if all(item.get(k) == v for k, v in query.items())
    ]
    if sort_by:
        result.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
    return result

async def find_one(collection: str, query: dict) -> dict | None:
    data = await asyncio.to_thread(_read)
    for item in data.get(collection, []):
        if all(item.get(k) == v for k, v in query.items()):
            return item
    return None

async def insert_one(collection: str, doc: dict) -> dict:
    doc = dict(doc)
    doc.setdefault("_id", str(uuid.uuid4()))
    doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    data = await asyncio.to_thread(_read)
    data.setdefault(collection, [])
    data[collection].append(doc)
    await asyncio.to_thread(_write, data)
    return doc

async def update_one(collection: str, query: dict, update: dict) -> bool:
    data = await asyncio.to_thread(_read)
    for item in data.get(collection, []):
        if all(item.get(k) == v for k, v in query.items()):
            item.update(update)
            await asyncio.to_thread(_write, data)
            return True
    return False

async def delete_one(collection: str, query: dict) -> bool:
    data = await asyncio.to_thread(_read)
    items = data.get(collection, [])
    filtered = [
        item for item in items
        if not all(item.get(k) == v for k, v in query.items())
    ]
    if len(filtered) != len(items):
        data[collection] = filtered
        await asyncio.to_thread(_write, data)
        return True
    return False
