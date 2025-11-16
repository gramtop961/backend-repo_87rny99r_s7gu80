from datetime import datetime
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "appdb")

async def get_db() -> AsyncIOMotorDatabase:
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(DATABASE_URL)
        _db = _client[DATABASE_NAME]
    return _db

async def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = await get_db()
    now = datetime.utcnow()
    data.setdefault("created_at", now)
    data.setdefault("updated_at", now)
    res = await db[collection_name].insert_one(data)
    doc = await db[collection_name].find_one({"_id": res.inserted_id})
    if doc and "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc or {}

async def update_document(collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
    db = await get_db()
    update_dict.setdefault("updated_at", datetime.utcnow())
    res = await db[collection_name].update_one(filter_dict, {"$set": update_dict})
    return res.modified_count

async def get_documents(collection_name: str, filter_dict: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
    db = await get_db()
    cursor = db[collection_name].find(filter_dict).limit(limit)
    out: List[Dict[str, Any]] = []
    async for doc in cursor:
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        out.append(doc)
    return out
